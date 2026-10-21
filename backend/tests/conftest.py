"""
Shared fixtures.

Environment overrides happen at import time, before ``config`` is imported anywhere, so
the app's global engine and data directories point at a throw-away location.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import AsyncIterator

_TMP = Path(tempfile.mkdtemp(prefix="cmssync-tests-"))
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP / 'test.db'}"
os.environ["DATA_DIR"] = str(_TMP / "data")
os.environ["INSTANCES_DATA_DIR"] = str(_TMP / "data" / "instances")
os.environ["MAGENTO_RETRY_DELAY"] = "0"

import logging_config  # noqa: E402

# main.py calls setup_logging(log_to_file=True) at import: it would write backend/logs/*.log
# on every test run and clear the root handlers pytest relies on for caplog.
logging_config.setup_logging = lambda *args, **kwargs: None  # type: ignore[assignment]

import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

from tests.magento_stub import FakeMagento, StubNetwork, create_app, patch_magento_client, seed_profile  # noqa: E402

SOURCE_HOST = "source.magento.test"
DEST_HOST = "dest.magento.test"
TOKEN = "integration-token"
# Both stubs share one frozen clock so creation_time/update_time never straddle a second
# boundary between seeding and syncing (ComparisonService compares those fields).
FROZEN_TIME = "2026-01-01 00:00:00"


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    shutil.rmtree(_TMP, ignore_errors=True)


@pytest.fixture
def magento() -> FakeMagento:
    """A single fake Magento with the four stock pages and three blocks."""
    m = FakeMagento(name="magento", tokens=[TOKEN])
    m.seed_stock_pages()
    m.add_block("footer_links_block", "Footer Links", "<ul><li>About</li></ul>")
    m.add_block("contact-us-info", "Contact us info", "<p>Call us</p>")
    m.add_block("sale_coupon", "Sale coupon", "<p>SPRING</p>", active=False)
    return m


@pytest_asyncio.fixture
async def magento_http(magento: FakeMagento) -> AsyncIterator[httpx.AsyncClient]:
    """Raw httpx client against the stub, for contract tests of the stub itself."""
    transport = httpx.ASGITransport(app=create_app(magento))
    async with httpx.AsyncClient(transport=transport, base_url="http://magento.test",
                                 headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client


@pytest_asyncio.fixture
async def network(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[StubNetwork]:
    """Routes MagentoClient traffic to registered stubs by hostname."""
    net = StubNetwork()
    patch_magento_client(monkeypatch, net)
    yield net
    await net.aclose()


@pytest.fixture
def source_magento(network: StubNetwork) -> FakeMagento:
    """The 'demo' seed profile: stock pages, three blocks, an about-us page."""
    m = FakeMagento(name="source", tokens=[TOKEN], clock=lambda: FROZEN_TIME)
    seed_profile(m, "demo")
    network.register(SOURCE_HOST, m)
    return m


@pytest.fixture
def dest_magento(network: StubNetwork) -> FakeMagento:
    """The 'demo-dest' profile: a drifted footer block and one block only the destination has."""
    m = FakeMagento(name="dest", tokens=[TOKEN], clock=lambda: FROZEN_TIME)
    seed_profile(m, "demo-dest")
    network.register(DEST_HOST, m)
    return m


@pytest_asyncio.fixture
async def api(source_magento, dest_magento) -> AsyncIterator[httpx.AsyncClient]:
    """The real FastAPI app on a fresh database, with Magento traffic routed to the stubs."""
    from main import app
    from models.database import Base, engine
    from config import settings

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    shutil.rmtree(settings.instances_data_dir, ignore_errors=True)
    settings.instances_data_dir.mkdir(parents=True, exist_ok=True)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://cmssync.test") as client:
        yield client

    await engine.dispose()
