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

import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

from tests.magento_stub import FakeMagento, StubNetwork, create_app, patch_magento_client  # noqa: E402

SOURCE_HOST = "source.magento.test"
DEST_HOST = "dest.magento.test"
TOKEN = "integration-token"


def pytest_sessionfinish(session, exitstatus):
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


@pytest.fixture
def network(monkeypatch) -> StubNetwork:
    """Routes MagentoClient traffic to registered stubs by hostname."""
    net = StubNetwork()
    patch_magento_client(monkeypatch, net)
    return net


@pytest.fixture
def source_magento(network: StubNetwork) -> FakeMagento:
    m = FakeMagento(name="source", tokens=[TOKEN])
    m.seed_stock_pages()
    m.add_block("footer_links_block", "Footer Links", "<ul><li><a href=\"/about-us\">About us</a></li></ul>")
    m.add_block("contact-us-info", "Contact us info", "<p>Call us: +40 000 000 000</p>")
    m.add_block("sale_coupon", "Sale coupon", "<p>Use code SPRING</p>")
    m.add_page("about-us", "About us", "<p>We sell nice things.</p>", content_heading="About us")
    network.register(SOURCE_HOST, m)
    return m


@pytest.fixture
def dest_magento(network: StubNetwork) -> FakeMagento:
    m = FakeMagento(name="dest", tokens=[TOKEN])
    m.seed_stock_pages()
    # Drifted copy: one shared block with different content, one block only here.
    m.add_block("footer_links_block", "Footer Links", "<ul><li><a href=\"/about\">About</a></li></ul>")
    m.add_block("dest_only_block", "Only on destination", "<p>Not on source</p>")
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
