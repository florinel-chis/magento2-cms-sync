import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.models import DataSnapshot, Instance
from models.schemas import DataType
from integrations.magento_client import MagentoClient
from config import settings


class DataStorageService:
    @staticmethod
    def _get_instance_dir(instance_id: int) -> Path:
        """Get the data directory for an instance"""
        return settings.instances_data_dir / str(instance_id)
    
    @staticmethod
    def _get_snapshot_path(instance_id: int, data_type: DataType) -> Path:
        """Get the file path for a data snapshot"""
        instance_dir = DataStorageService._get_instance_dir(instance_id)
        return instance_dir / f"{data_type.value}.json"
    
    @staticmethod
    async def save_snapshot(
        db: AsyncSession,
        instance_id: int,
        data_type: DataType,
        data: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> DataSnapshot:
        """Save data snapshot to JSON file and create database record"""
        # Ensure directory exists
        instance_dir = DataStorageService._get_instance_dir(instance_id)
        instance_dir.mkdir(parents=True, exist_ok=True)
        
        # Save to JSON file
        file_path = DataStorageService._get_snapshot_path(instance_id, data_type)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(
                data, 
                f, 
                ensure_ascii=settings.json_ensure_ascii,
                indent=settings.json_indent
            )
        
        # Create or update database record
        result = await db.execute(
            select(DataSnapshot).where(
                DataSnapshot.instance_id == instance_id,
                DataSnapshot.data_type == data_type.value
            )
        )
        snapshot = result.scalar_one_or_none()
        
        if snapshot:
            # Update existing snapshot
            snapshot.file_path = str(file_path)
            snapshot.item_count = len(data)
            snapshot.created_at = datetime.utcnow()
            snapshot.snapshot_metadata = metadata or {}
        else:
            # Create new snapshot
            snapshot = DataSnapshot(
                instance_id=instance_id,
                data_type=data_type.value,
                file_path=str(file_path),
                item_count=len(data),
                snapshot_metadata=metadata or {}
            )
            db.add(snapshot)
        
        await db.commit()
        await db.refresh(snapshot)
        
        return snapshot
    
    @staticmethod
    def load_snapshot(instance_id: int, data_type: DataType) -> Optional[List[Dict[str, Any]]]:
        """Load data snapshot from JSON file"""
        file_path = DataStorageService._get_snapshot_path(instance_id, data_type)
        
        if not file_path.exists():
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    async def refresh_instance_data(
        db: AsyncSession,
        instance: Instance,
        data_type: DataType
    ) -> DataSnapshot:
        """Fetch fresh data from Magento and save snapshot"""
        client = MagentoClient(
            base_url=str(instance.url),
            token=instance.api_token
        )
        
        # Fetch data based on type
        if data_type == DataType.BLOCKS:
            data = await client.get_cms_blocks()
        else:  # DataType.PAGES
            data = await client.get_cms_pages()
        
        # Get store views for metadata
        store_views = await client.get_store_views()
        
        # Save snapshot
        snapshot = await DataStorageService.save_snapshot(
            db=db,
            instance_id=instance.id,
            data_type=data_type,
            data=data,
            metadata={"store_views": store_views}
        )
        
        return snapshot
    
    @staticmethod
    async def get_or_refresh_data(
        db: AsyncSession,
        instance: Instance,
        data_type: DataType,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """Get data from snapshot or refresh if needed"""
        if not force_refresh:
            # Try to load existing snapshot
            data = DataStorageService.load_snapshot(instance.id, data_type)
            if data is not None:
                return data
        
        # Refresh data from Magento
        await DataStorageService.refresh_instance_data(db, instance, data_type)
        
        # Load and return the fresh data
        data = DataStorageService.load_snapshot(instance.id, data_type)
        return data or []