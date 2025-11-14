"""Unit tests for SyncService."""
import pytest
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock, patch

from services.sync import SyncService
from models.schemas import DataType, SyncItem


@pytest.mark.unit
class TestSyncService:
    """Test suite for SyncService."""

    def test_get_identifier_for_blocks(self):
        """Test getting identifier from block."""
        block = {"identifier": "test-block"}
        result = SyncService._get_identifier(block, DataType.BLOCKS)
        assert result == "test-block"

    def test_get_identifier_for_pages(self):
        """Test getting identifier from page."""
        page = {"identifier": "test-page"}
        result = SyncService._get_identifier(page, DataType.PAGES)
        assert result == "test-page"

    def test_find_item_in_data(self):
        """Test finding item by identifier."""
        data = [
            {"identifier": "block-1", "title": "Block 1"},
            {"identifier": "block-2", "title": "Block 2"}
        ]

        result = SyncService._find_item_in_data(data, "block-2", DataType.BLOCKS)

        assert result is not None
        assert result["title"] == "Block 2"

    def test_find_item_not_found(self):
        """Test finding non-existent item."""
        data = [{"identifier": "block-1", "title": "Block 1"}]

        result = SyncService._find_item_in_data(data, "nonexistent", DataType.BLOCKS)

        assert result is None

    def test_prepare_item_for_sync_create(self):
        """Test preparing new item for creation."""
        source_item = {
            "identifier": "new-block",
            "title": "New Block",
            "content": "<p>Content</p>",
            "is_active": True,
            "store_id": [0],
            "creation_time": "2024-01-01",
            "update_time": "2024-01-02"
        }

        result = SyncService._prepare_item_for_sync(
            source_item=source_item,
            dest_item=None,
            fields_to_sync=None,
            store_view_mapping=None,
            data_type=DataType.BLOCKS
        )

        # Should have all fields except timestamps
        assert result["identifier"] == "new-block"
        assert result["title"] == "New Block"
        assert "creation_time" not in result
        assert "update_time" not in result

    def test_prepare_item_for_sync_update(self):
        """Test preparing item for update."""
        source_item = {
            "identifier": "existing-block",
            "title": "Updated Title",
            "content": "<p>New Content</p>",
            "is_active": True,
            "store_id": [0]
        }
        dest_item = {
            "id": 123,
            "block_id": 123,
            "identifier": "existing-block",
            "title": "Old Title",
            "content": "<p>Old Content</p>",
            "is_active": False,
            "store_id": [1]
        }

        result = SyncService._prepare_item_for_sync(
            source_item=source_item,
            dest_item=dest_item,
            fields_to_sync=None,
            store_view_mapping=None,
            data_type=DataType.BLOCKS
        )

        # Should preserve destination ID
        assert result["id"] == 123
        assert result["block_id"] == 123
        # Should have source content
        assert result["title"] == "Updated Title"
        assert result["content"] == "<p>New Content</p>"

    def test_prepare_item_for_sync_selective_fields(self):
        """Test syncing only selected fields."""
        source_item = {
            "identifier": "block",
            "title": "New Title",
            "content": "<p>New Content</p>",
            "is_active": True,
            "store_id": [0]
        }
        dest_item = {
            "id": 123,
            "block_id": 123,
            "identifier": "block",
            "title": "Old Title",
            "content": "<p>Old Content</p>",
            "is_active": False,
            "store_id": [1]
        }

        result = SyncService._prepare_item_for_sync(
            source_item=source_item,
            dest_item=dest_item,
            fields_to_sync=["title"],  # Only sync title
            store_view_mapping=None,
            data_type=DataType.BLOCKS
        )

        # Should have updated title
        assert result["title"] == "New Title"
        # Should keep old content and active status
        assert result["content"] == "<p>Old Content</p>"
        assert result["is_active"] is False

    def test_prepare_item_with_store_mapping(self):
        """Test store view mapping during sync."""
        source_item = {
            "identifier": "block",
            "title": "Test",
            "content": "<p>Test</p>",
            "is_active": True,
            "store_id": [0, 1, 2]
        }

        store_mapping = {
            "0": 10,
            "1": 11,
            "2": 12
        }

        result = SyncService._prepare_item_for_sync(
            source_item=source_item,
            dest_item=None,
            fields_to_sync=None,
            store_view_mapping=store_mapping,
            data_type=DataType.BLOCKS
        )

        # Store IDs should be mapped
        assert result["store_id"] == [10, 11, 12]

    def test_create_sync_preview(self, sample_cms_blocks):
        """Test creating sync preview."""
        sync_items = [
            SyncItem(identifier="test-block-1", action="update"),
            SyncItem(identifier="test-block-2", action="create")
        ]

        service = SyncService()
        preview = service.create_sync_preview(
            source_data=sample_cms_blocks,
            dest_data=[sample_cms_blocks[0]],  # Only first block exists
            data_type=DataType.BLOCKS,
            sync_items=sync_items,
            store_view_mapping=None
        )

        assert preview.total_changes == 2
        assert preview.creates == 1
        assert preview.updates == 1
        assert len(preview.items) == 2

    @pytest.mark.asyncio
    async def test_execute_sync_create(self, sample_cms_blocks):
        """Test executing sync with create action."""
        mock_client = AsyncMock()
        mock_client.get_cms_blocks.return_value = []
        mock_client.create_cms_block.return_value = {"id": 1, "identifier": "test-block-1"}

        sync_items = [
            SyncItem(identifier="test-block-1", action="create")
        ]

        service = SyncService()
        results = await service.execute_sync(
            source_data=sample_cms_blocks,
            dest_client=mock_client,
            data_type=DataType.BLOCKS,
            sync_items=sync_items,
            store_view_mapping=None
        )

        assert len(results) == 1
        assert results[0]["success"] is True
        assert results[0]["action"] == "create"
        mock_client.create_cms_block.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_sync_update(self, sample_cms_blocks):
        """Test executing sync with update action."""
        existing_block = sample_cms_blocks[0].copy()
        existing_block["content"] = "<p>Old content</p>"

        mock_client = AsyncMock()
        mock_client.get_cms_blocks.return_value = [existing_block]
        mock_client.update_cms_block.return_value = {"id": 1, "identifier": "test-block-1"}

        sync_items = [
            SyncItem(identifier="test-block-1", action="update")
        ]

        service = SyncService()
        results = await service.execute_sync(
            source_data=sample_cms_blocks,
            dest_client=mock_client,
            data_type=DataType.BLOCKS,
            sync_items=sync_items,
            store_view_mapping=None
        )

        assert len(results) == 1
        assert results[0]["success"] is True
        assert results[0]["action"] == "update"
        mock_client.update_cms_block.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_sync_item_not_found(self):
        """Test sync fails when source item not found."""
        mock_client = AsyncMock()
        mock_client.get_cms_blocks.return_value = []

        sync_items = [
            SyncItem(identifier="nonexistent", action="create")
        ]

        service = SyncService()
        results = await service.execute_sync(
            source_data=[],
            dest_client=mock_client,
            data_type=DataType.BLOCKS,
            sync_items=sync_items,
            store_view_mapping=None
        )

        assert len(results) == 1
        assert results[0]["success"] is False
        assert "not found" in results[0]["error"]
