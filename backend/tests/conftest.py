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
from typing import Any, AsyncIterator, Dict, List

_TMP = Path(tempfile.mkdtemp(prefix="cmssync-tests-"))
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP / 'test.db'}"
os.environ["DATA_DIR"] = str(_TMP / "data")
os.environ["INSTANCES_DATA_DIR"] = str(_TMP / "data" / "instances")
os.environ["MAGENTO_RETRY_DELAY"] = "0"
os.environ["ENCRYPTION_KEY"] = "T2nmWvAWn7-9k8lXDyRYI-qXnEKd3V6e4lCq3e3C9Eo="  # test-only Fernet key

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


@pytest.fixture(autouse=True)
def _reset_dependency_overrides():
    """A test that overrides get_db and fails must not poison the tests after it."""
    yield
    import sys
    app = getattr(sys.modules.get("main"), "app", None)
    if app is not None:
        app.dependency_overrides.clear()


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


# ---------------------------------------------------------------------------
# Database-level fixtures (in-memory engine) and sample payloads in Magento's shape
# ---------------------------------------------------------------------------
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from models.database import Base  # noqa: E402
from models.models import Instance  # noqa: E402


@pytest_asyncio.fixture
async def test_engine():
    """In-memory SQLite engine with all tables created."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:",
                                 connect_args={"check_same_thread": False}, poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


async def _make_instance(db_session: AsyncSession, name: str, url: str, token: str) -> Instance:
    instance = Instance(name=name, url=url, api_token=token, is_active=True)
    db_session.add(instance)
    await db_session.commit()
    await db_session.refresh(instance)
    return instance


@pytest_asyncio.fixture
async def sample_instance(db_session: AsyncSession) -> Instance:
    return await _make_instance(db_session, "Test Instance", "https://test.magento.com", "test_token_1234567890abcdef")


@pytest_asyncio.fixture
async def source_instance(db_session: AsyncSession) -> Instance:
    return await _make_instance(db_session, "Source Instance", "https://source.magento.com", "source_token_1234567890abcdef")


@pytest_asyncio.fixture
async def dest_instance(db_session: AsyncSession) -> Instance:
    return await _make_instance(db_session, "Destination Instance", "https://destination.magento.com", "dest_token_1234567890abcdef")


@pytest.fixture
def sample_cms_blocks() -> List[Dict[str, Any]]:
    """Two blocks as Magento returns them (``active``, no ``is_active``)."""
    return [
        {"id": 1, "identifier": "test-block-1", "title": "Test Block 1", "content": "<p>This is test content 1</p>",
         "active": True, "store_id": [0], "creation_time": "2024-01-01 00:00:00", "update_time": "2024-01-01 00:00:00"},
        {"id": 2, "identifier": "test-block-2", "title": "Test Block 2", "content": "<p>This is test content 2</p>",
         "active": True, "store_id": [0, 1], "creation_time": "2024-01-01 00:00:00", "update_time": "2024-01-01 00:00:00"},
    ]


@pytest.fixture
def sample_cms_pages() -> List[Dict[str, Any]]:
    return [
        {"id": 1, "identifier": "test-page", "title": "Test Page 1", "content": "<p>This is test page content</p>",
         "content_heading": "Test Heading", "active": True, "store_id": [0], "page_layout": "1column",
         "meta_title": "Test Meta Title", "meta_keywords": "test, keywords", "meta_description": "Test meta description",
         "creation_time": "2024-01-01 00:00:00", "update_time": "2024-01-01 00:00:00"},
    ]


@pytest.fixture
def different_cms_blocks() -> List[Dict[str, Any]]:
    """The first sample block with different content, active flag and stores."""
    return [
        {"id": 10, "identifier": "test-block-1", "title": "Test Block 1 - Modified", "content": "<p>This is DIFFERENT content</p>",
         "active": False, "store_id": [1], "creation_time": "2024-01-01 00:00:00", "update_time": "2024-01-02 00:00:00"},
    ]
