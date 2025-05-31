from typing import List, Dict, Any, Optional
from models.schemas import DataType, SyncItem, SyncPreview
from integrations.magento_client import MagentoClient


class SyncService:
    
    @staticmethod
    def _get_identifier(item: Dict[str, Any], data_type: DataType) -> str:
        """Get the unique identifier for an item"""
        if data_type == DataType.BLOCKS:
            return item.get("identifier", "")
        else:  # DataType.PAGES
            # Try identifier first (newer Magento versions), then url_key (older versions)
            return item.get("identifier") or item.get("url_key", "")
    
    @staticmethod
    def _find_item_in_data(
        data: List[Dict[str, Any]], 
        identifier: str, 
        data_type: DataType
    ) -> Optional[Dict[str, Any]]:
        """Find an item in data by identifier"""
        for item in data:
            if SyncService._get_identifier(item, data_type) == identifier:
                return item
        return None
    
    @staticmethod
    def _prepare_item_for_sync(
        source_item: Dict[str, Any],
        dest_item: Optional[Dict[str, Any]],
        fields_to_sync: Optional[List[str]],
        store_view_mapping: Optional[Dict[str, str]],
        data_type: DataType
    ) -> Dict[str, Any]:
        """Prepare an item for sync by merging source data with optional field selection"""
        # Start with source item copy
        sync_data = source_item.copy()
        
        # If updating existing item, preserve some destination fields
        if dest_item:
            # Always preserve the ID for updates
            if data_type == DataType.BLOCKS:
                sync_data["id"] = dest_item["id"]
                sync_data["block_id"] = dest_item["block_id"]
            else:  # DataType.PAGES
                sync_data["id"] = dest_item["id"]
                # Only copy page_id if it exists
                if "page_id" in dest_item:
                    sync_data["page_id"] = dest_item["page_id"]
            
            # If specific fields are selected, only sync those
            if fields_to_sync:
                # Start with destination item and update only selected fields
                sync_data = dest_item.copy()
                for field in fields_to_sync:
                    if field in source_item:
                        sync_data[field] = source_item[field]
        
        # Apply store view mapping
        if store_view_mapping and "store_id" in sync_data:
            mapped_stores = []
            for store_id in sync_data["store_id"]:
                mapped_id = store_view_mapping.get(str(store_id), store_id)
                mapped_stores.append(mapped_id)
            sync_data["store_id"] = mapped_stores
        
        # Remove fields that shouldn't be synced
        fields_to_remove = ["creation_time", "update_time", "created_at", "updated_at"]
        for field in fields_to_remove:
            sync_data.pop(field, None)
        
        return sync_data
    
    def create_sync_preview(
        self,
        source_data: List[Dict[str, Any]],
        dest_data: List[Dict[str, Any]],
        data_type: DataType,
        sync_items: List[SyncItem],
        store_view_mapping: Optional[Dict[str, str]] = None
    ) -> SyncPreview:
        """Create a preview of what will be synced"""
        preview_items = []
        creates = 0
        updates = 0
        
        for sync_item in sync_items:
            source_item = self._find_item_in_data(
                source_data, sync_item.identifier, data_type
            )
            
            if not source_item:
                continue
            
            dest_item = self._find_item_in_data(
                dest_data, sync_item.identifier, data_type
            )
            
            # Prepare the synced version
            synced_item = self._prepare_item_for_sync(
                source_item=source_item,
                dest_item=dest_item,
                fields_to_sync=sync_item.fields_to_sync,
                store_view_mapping=store_view_mapping,
                data_type=data_type
            )
            
            preview_item = {
                "identifier": sync_item.identifier,
                "action": sync_item.action,
                "source": source_item,
                "destination": dest_item,
                "result": synced_item
            }
            
            preview_items.append(preview_item)
            
            if sync_item.action == "create":
                creates += 1
            else:
                updates += 1
        
        return SyncPreview(
            items=preview_items,
            total_changes=len(preview_items),
            creates=creates,
            updates=updates
        )
    
    async def execute_sync(
        self,
        source_data: List[Dict[str, Any]],
        dest_client: MagentoClient,
        data_type: DataType,
        sync_items: List[SyncItem],
        store_view_mapping: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Execute the sync operation"""
        results = []
        
        # First, get existing destination data to find IDs
        if data_type == DataType.BLOCKS:
            dest_data = await dest_client.get_cms_blocks()
        else:
            dest_data = await dest_client.get_cms_pages()
        
        for sync_item in sync_items:
            result = {
                "identifier": sync_item.identifier,
                "action": sync_item.action,
                "success": False,
                "message": None,
                "error": None
            }
            
            try:
                # Find source item
                source_item = self._find_item_in_data(
                    source_data, sync_item.identifier, data_type
                )
                
                if not source_item:
                    result["error"] = f"Source item not found: {sync_item.identifier}"
                    results.append(result)
                    continue
                
                # Find destination item (if updating)
                dest_item = self._find_item_in_data(
                    dest_data, sync_item.identifier, data_type
                )
                
                # Prepare item for sync
                sync_data = self._prepare_item_for_sync(
                    source_item=source_item,
                    dest_item=dest_item,
                    fields_to_sync=sync_item.fields_to_sync,
                    store_view_mapping=store_view_mapping,
                    data_type=data_type
                )
                
                # Perform sync
                if sync_item.action == "create" and not dest_item:
                    # Create new item
                    if data_type == DataType.BLOCKS:
                        await dest_client.create_cms_block(sync_data)
                    else:
                        await dest_client.create_cms_page(sync_data)
                    
                    result["success"] = True
                    result["message"] = f"Created {data_type.value[:-1]} successfully"
                    
                elif sync_item.action == "update" and dest_item:
                    # Update existing item
                    if data_type == DataType.BLOCKS:
                        item_id = dest_item["id"]
                        await dest_client.update_cms_block(item_id, sync_data)
                    else:
                        item_id = dest_item["id"]
                        await dest_client.update_cms_page(item_id, sync_data)
                    
                    result["success"] = True
                    result["message"] = f"Updated {data_type.value[:-1]} successfully"
                    
                else:
                    result["error"] = f"Invalid action or item state: {sync_item.action}"
                    
            except Exception as e:
                result["error"] = str(e)
            
            results.append(result)
        
        return results