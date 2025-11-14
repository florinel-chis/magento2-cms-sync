"""Pytest configuration and fixtures."""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from typing import AsyncGenerator, Dict, Any, List
import tempfile
import shutil
from pathlib import Path

from models.database import Base
from models.models import Instance
from config import settings


@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest_asyncio.fixture
async def test_engine():
    """Create a test database engine with in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def sample_instance(db_session: AsyncSession) -> Instance:
    """Create a sample Magento instance for testing."""
    instance = Instance(
        name="Test Instance",
        url="https://test.magento.com",
        api_token="test_token_1234567890abcdef",
        is_active=True
    )
    db_session.add(instance)
    await db_session.commit()
    await db_session.refresh(instance)
    return instance


@pytest_asyncio.fixture
async def source_instance(db_session: AsyncSession) -> Instance:
    """Create a source instance for comparison tests."""
    instance = Instance(
        name="Source Instance",
        url="https://source.magento.com",
        api_token="source_token_1234567890abcdef",
        is_active=True
    )
    db_session.add(instance)
    await db_session.commit()
    await db_session.refresh(instance)
    return instance


@pytest_asyncio.fixture
async def dest_instance(db_session: AsyncSession) -> Instance:
    """Create a destination instance for comparison tests."""
    instance = Instance(
        name="Destination Instance",
        url="https://destination.magento.com",
        api_token="dest_token_1234567890abcdef",
        is_active=True
    )
    db_session.add(instance)
    await db_session.commit()
    await db_session.refresh(instance)
    return instance


@pytest.fixture
def sample_cms_blocks() -> List[Dict[str, Any]]:
    """Sample CMS block data for testing."""
    return [
        {
            "id": 1,
            "identifier": "test-block-1",
            "title": "Test Block 1",
            "content": "<p>This is test content 1</p>",
            "is_active": True,
            "store_id": [0],
            "creation_time": "2024-01-01 00:00:00",
            "update_time": "2024-01-01 00:00:00"
        },
        {
            "id": 2,
            "identifier": "test-block-2",
            "title": "Test Block 2",
            "content": "<p>This is test content 2</p>",
            "is_active": True,
            "store_id": [0, 1],
            "creation_time": "2024-01-01 00:00:00",
            "update_time": "2024-01-01 00:00:00"
        }
    ]


@pytest.fixture
def sample_cms_pages() -> List[Dict[str, Any]]:
    """Sample CMS page data for testing."""
    return [
        {
            "id": 1,
            "identifier": "test-page",
            "url_key": "test-page",
            "title": "Test Page 1",
            "content": "<p>This is test page content</p>",
            "content_heading": "Test Heading",
            "is_active": True,
            "store_id": [0],
            "page_layout": "1column",
            "meta_title": "Test Meta Title",
            "meta_keywords": "test, keywords",
            "meta_description": "Test meta description",
            "creation_time": "2024-01-01 00:00:00",
            "update_time": "2024-01-01 00:00:00"
        }
    ]


@pytest.fixture
def different_cms_blocks() -> List[Dict[str, Any]]:
    """CMS blocks with different content for comparison testing."""
    return [
        {
            "id": 10,
            "identifier": "test-block-1",
            "title": "Test Block 1 - Modified",
            "content": "<p>This is DIFFERENT content</p>",
            "is_active": False,
            "store_id": [1],
            "creation_time": "2024-01-01 00:00:00",
            "update_time": "2024-01-02 00:00:00"
        }
    ]
