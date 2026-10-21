"""Unit tests for ComparisonService."""
import pytest
from typing import Dict, Any, List

from services.comparison import ComparisonService
from models.schemas import DataType, ComparisonStatus


@pytest.mark.unit
class TestComparisonService:
    """Test suite for ComparisonService."""

    def test_get_identifier_for_blocks(self):
        """Test getting identifier from CMS block."""
        block = {"identifier": "test-block", "title": "Test"}
        result = ComparisonService._get_identifier(block, DataType.BLOCKS)
        assert result == "test-block"

    def test_get_identifier_for_pages_with_identifier(self):
        """Test getting identifier from CMS page (newer Magento)."""
        page = {"identifier": "test-page", "url_key": "test-url", "title": "Test"}
        result = ComparisonService._get_identifier(page, DataType.PAGES)
        assert result == "test-page"

    def test_get_identifier_for_pages_with_url_key(self):
        """Test getting identifier from CMS page using url_key fallback."""
        page = {"url_key": "test-url", "title": "Test"}
        result = ComparisonService._get_identifier(page, DataType.PAGES)
        assert result == "test-url"

    def test_get_title(self):
        """Test getting title from item."""
        item = {"title": "Test Title", "content": "Content"}
        result = ComparisonService._get_title(item)
        assert result == "Test Title"

    def test_get_title_fallback_to_content_heading(self):
        """Test title fallback to content_heading."""
        item = {"content_heading": "Heading", "content": "Content"}
        result = ComparisonService._get_title(item)
        assert result == "Heading"

    def test_compare_items_identical_blocks(self):
        """Test comparing identical blocks returns no differences."""
        block = {
            "identifier": "test",
            "title": "Test",
            "content": "<p>Test</p>",
            "is_active": True,
            "store_id": [0]
        }

        is_different, differences = ComparisonService._compare_items(
            block, block.copy(), DataType.BLOCKS
        )

        assert not is_different
        assert len(differences) == 0

    def test_compare_items_different_content(self):
        """Test comparing blocks with different content."""
        source = {
            "identifier": "test",
            "title": "Test",
            "content": "<p>Source content</p>",
            "is_active": True,
            "store_id": [0]
        }
        dest = {
            "identifier": "test",
            "title": "Test",
            "content": "<p>Dest content</p>",
            "is_active": True,
            "store_id": [0]
        }

        is_different, differences = ComparisonService._compare_items(
            source, dest, DataType.BLOCKS
        )

        assert is_different
        assert "content" in differences

    def test_compare_items_different_stores(self):
        """Test comparing blocks with different store assignments."""
        source = {
            "identifier": "test",
            "title": "Test",
            "content": "<p>Test</p>",
            "is_active": True,
            "store_id": [0]
        }
        dest = {
            "identifier": "test",
            "title": "Test",
            "content": "<p>Test</p>",
            "is_active": True,
            "store_id": [0, 1]
        }

        is_different, differences = ComparisonService._compare_items(
            source, dest, DataType.BLOCKS
        )

        assert is_different
        assert "store_id" in differences

    def test_compare_data_all_same(self, sample_cms_blocks):
        """Test comparison when all blocks are identical."""
        result = ComparisonService.compare_data(
            source_data=sample_cms_blocks,
            dest_data=sample_cms_blocks.copy(),
            data_type=DataType.BLOCKS,
            source_instance=None,
            dest_instance=None
        )

        assert result.total_source == 2
        assert result.total_destination == 2
        assert result.exists_in_both == 2
        assert result.different == 0
        assert result.missing_in_destination == 0
        assert result.missing_in_source == 0

    def test_compare_data_missing_in_destination(self, sample_cms_blocks):
        """Test comparison when blocks are missing in destination."""
        result = ComparisonService.compare_data(
            source_data=sample_cms_blocks,
            dest_data=[],
            data_type=DataType.BLOCKS,
            source_instance=None,
            dest_instance=None
        )

        assert result.total_source == 2
        assert result.total_destination == 0
        assert result.exists_in_both == 0
        assert result.missing_in_destination == 2
        assert result.missing_in_source == 0

    def test_compare_data_different_content(self, sample_cms_blocks, different_cms_blocks):
        """Test comparison when content differs."""
        result = ComparisonService.compare_data(
            source_data=sample_cms_blocks[:1],  # Just first block
            dest_data=different_cms_blocks,
            data_type=DataType.BLOCKS,
            source_instance=None,
            dest_instance=None
        )

        assert result.total_source == 1
        assert result.total_destination == 1
        assert result.exists_in_both == 1
        assert result.different == 1

        # Check the comparison item details
        item = result.items[0]
        assert item.source_status == ComparisonStatus.DIFFERENT
        assert item.destination_status == ComparisonStatus.DIFFERENT
        assert len(item.differences) > 0
        assert "content" in item.differences
        assert "active" in item.differences

    def test_get_item_diff_with_differences(self):
        """Test getting detailed field diff."""
        source = {
            "identifier": "test",
            "title": "Source Title",
            "content": "<p>Source</p>",
            "is_active": True,
            "store_id": [0]
        }
        dest = {
            "identifier": "test",
            "title": "Dest Title",
            "content": "<p>Dest</p>",
            "is_active": False,
            "store_id": [1]
        }

        result = ComparisonService.get_item_diff(
            source_item=source,
            dest_item=dest,
            data_type=DataType.BLOCKS,
            identifier="test"
        )

        assert result.identifier == "test"
        assert result.data_type == DataType.BLOCKS
        assert len(result.fields) > 0

        # Check specific field differences
        title_field = next(f for f in result.fields if f.field_name == "title")
        assert title_field.is_different
        assert title_field.source_value == "Source Title"
        assert title_field.destination_value == "Dest Title"

        content_field = next(f for f in result.fields if f.field_name == "content")
        assert content_field.is_different

    def test_get_item_diff_missing_destination(self):
        """Test getting diff when destination item is missing."""
        source = {
            "identifier": "test",
            "title": "Source Title",
            "content": "<p>Source</p>",
            "is_active": True,
            "store_id": [0]
        }

        result = ComparisonService.get_item_diff(
            source_item=source,
            dest_item=None,
            data_type=DataType.BLOCKS,
            identifier="test"
        )

        assert result.identifier == "test"
        assert result.source_stores == [0]
        assert result.destination_stores == []

        # All fields should show source value vs None
        for field in result.fields:
            if field.field_name in source:
                assert field.source_value is not None
                assert field.destination_value is None
                assert field.is_different
