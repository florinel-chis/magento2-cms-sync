from typing import List, Dict, Any, Set, Tuple
from datetime import datetime, timezone

from models.schemas import (
    ComparisonItem, ComparisonResult, ComparisonStatus,
    DataType, DiffField, DiffResult
)


class ComparisonService:
    
    @staticmethod
    def _get_identifier(item: Dict[str, Any], data_type: DataType) -> str:
        """Get the unique identifier for an item"""
        if data_type == DataType.BLOCKS:
            return item.get("identifier", "")
        else:  # DataType.PAGES
            # Try identifier first (newer Magento versions), then url_key (older versions)
            return item.get("identifier", item.get("url_key", ""))
    
    @staticmethod
    def _get_title(item: Dict[str, Any]) -> str:
        """Get the title/name of an item"""
        return item.get("title", item.get("content_heading", ""))
    
    @staticmethod
    def _compare_items(
        source_item: Dict[str, Any],
        dest_item: Dict[str, Any],
        data_type: DataType
    ) -> Tuple[bool, List[str]]:
        """Compare two items and return if they're different and which fields"""
        differences = []
        
        # Fields to compare based on data type
        if data_type == DataType.BLOCKS:
            compare_fields = [
                "title", "content", "is_active", "creation_time",
                "update_time", "sort_order"
            ]
        else:  # DataType.PAGES
            compare_fields = [
                "title", "content", "content_heading", "page_layout",
                "meta_title", "meta_keywords", "meta_description",
                "is_active", "sort_order", "layout_update_xml",
                "custom_theme", "custom_root_template", "custom_layout_update_xml"
            ]
        
        for field in compare_fields:
            source_val = source_item.get(field)
            dest_val = dest_item.get(field)
            
            if source_val != dest_val:
                differences.append(field)
        
        # Check store assignments
        source_stores = set(source_item.get("store_id", []))
        dest_stores = set(dest_item.get("store_id", []))
        
        if source_stores != dest_stores:
            differences.append("store_id")
        
        return len(differences) > 0, differences
    
    @staticmethod
    def compare_data(
        source_data: List[Dict[str, Any]],
        dest_data: List[Dict[str, Any]],
        data_type: DataType,
        source_instance: Any,
        dest_instance: Any
    ) -> ComparisonResult:
        """Compare source and destination data"""
        # Create lookup dictionaries
        source_lookup = {
            ComparisonService._get_identifier(item, data_type): item
            for item in source_data
        }
        dest_lookup = {
            ComparisonService._get_identifier(item, data_type): item
            for item in dest_data
        }
        
        # Get all unique identifiers
        all_identifiers = set(source_lookup.keys()) | set(dest_lookup.keys())
        
        # Compare items
        comparison_items = []
        exists_in_both = 0
        missing_in_dest = 0
        missing_in_source = 0
        different = 0
        
        for identifier in sorted(all_identifiers):
            source_item = source_lookup.get(identifier)
            dest_item = dest_lookup.get(identifier)
            
            if source_item and dest_item:
                # Item exists in both
                is_different, differences = ComparisonService._compare_items(
                    source_item, dest_item, data_type
                )
                
                if is_different:
                    status = ComparisonStatus.DIFFERENT
                    different += 1
                else:
                    status = ComparisonStatus.EXISTS
                    
                exists_in_both += 1
                
                comparison_item = ComparisonItem(
                    identifier=identifier,
                    title=ComparisonService._get_title(source_item),
                    source_status=status,
                    destination_status=status,
                    source_data=source_item,
                    destination_data=dest_item,
                    differences=differences if is_different else None
                )
                
            elif source_item and not dest_item:
                # Missing in destination
                missing_in_dest += 1
                comparison_item = ComparisonItem(
                    identifier=identifier,
                    title=ComparisonService._get_title(source_item),
                    source_status=ComparisonStatus.EXISTS,
                    destination_status=ComparisonStatus.MISSING,
                    source_data=source_item,
                    destination_data=None,
                    differences=None
                )
                
            else:  # not source_item and dest_item
                # Missing in source (exists only in destination)
                missing_in_source += 1
                comparison_item = ComparisonItem(
                    identifier=identifier,
                    title=ComparisonService._get_title(dest_item),
                    source_status=ComparisonStatus.MISSING,
                    destination_status=ComparisonStatus.EXISTS,
                    source_data=None,
                    destination_data=dest_item,
                    differences=None
                )
            
            comparison_items.append(comparison_item)
        
        return ComparisonResult(
            source_instance=source_instance,
            destination_instance=dest_instance,
            data_type=data_type,
            total_source=len(source_data),
            total_destination=len(dest_data),
            exists_in_both=exists_in_both,
            missing_in_destination=missing_in_dest,
            missing_in_source=missing_in_source,
            different=different,
            items=comparison_items,
            compared_at=datetime.now(timezone.utc)
        )
    
    @staticmethod
    def get_item_diff(
        source_item: Dict[str, Any],
        dest_item: Dict[str, Any],
        data_type: DataType,
        identifier: str
    ) -> DiffResult:
        """Get detailed field-by-field diff for an item"""
        diff_fields = []
        
        # Get fields to compare
        if data_type == DataType.BLOCKS:
            compare_fields = [
                "title", "content", "is_active", "creation_time",
                "update_time", "sort_order"
            ]
        else:  # DataType.PAGES
            compare_fields = [
                "title", "content", "content_heading", "page_layout",
                "meta_title", "meta_keywords", "meta_description",
                "is_active", "sort_order", "layout_update_xml",
                "custom_theme", "custom_root_template", "custom_layout_update_xml"
            ]
        
        # Compare each field
        for field in compare_fields:
            source_val = source_item.get(field) if source_item else None
            dest_val = dest_item.get(field) if dest_item else None
            
            diff_field = DiffField(
                field_name=field,
                source_value=source_val,
                destination_value=dest_val,
                is_different=source_val != dest_val
            )
            diff_fields.append(diff_field)
        
        # Get store assignments
        source_stores = source_item.get("store_id", []) if source_item else []
        dest_stores = dest_item.get("store_id", []) if dest_item else []
        
        return DiffResult(
            identifier=identifier,
            data_type=data_type,
            fields=diff_fields,
            source_stores=source_stores,
            destination_stores=dest_stores
        )