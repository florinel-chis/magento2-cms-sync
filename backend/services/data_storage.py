import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
import aiofiles

from models.models import DataSnapshot, Instance
from models.schemas import DataType
from integrations.magento_client import MagentoClient
from config import settings

logger = logging.getLogger(__name__)


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
        """
        Save data snapshot to JSON file and create database record.

        Uses async file I/O to prevent blocking the event loop.
        """
        try:
            # Ensure directory exists
            instance_dir = DataStorageService._get_instance_dir(instance_id)
            instance_dir.mkdir(parents=True, exist_ok=True)

            # Save to JSON file asynchronously
            file_path = DataStorageService._get_snapshot_path(instance_id, data_type)

            # Serialize JSON outside of async context (CPU-bound)
            json_content = json.dumps(
                data,
                ensure_ascii=settings.json_ensure_ascii,
                indent=settings.json_indent
            )

            # Write file asynchronously (I/O-bound)
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json_content)

            logger.info(f"Saved snapshot for instance {instance_id}, type {data_type.value}, {len(data)} items")

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
                snapshot.created_at = datetime.now(timezone.utc)  # Fixed: was utcnow()
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

        except json.JSONEncodeError as e:
            await db.rollback()
            logger.error(f"Failed to serialize data for instance {instance_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to serialize snapshot data: {str(e)}"
            )
        except IOError as e:
            await db.rollback()
            logger.error(f"Failed to write snapshot file {file_path}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to write snapshot file: {str(e)}"
            )
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to save snapshot for instance {instance_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save snapshot: {str(e)}"
            )

    @staticmethod
    async def load_snapshot(instance_id: int, data_type: DataType) -> Optional[List[Dict[str, Any]]]:
        """
        Load data snapshot from JSON file asynchronously.

        Returns None if snapshot doesn't exist or is invalid.
        """
        file_path = DataStorageService._get_snapshot_path(instance_id, data_type)

        if not file_path.exists():
            logger.debug(f"Snapshot not found: {file_path}")
            return None

        try:
            # Read file asynchronously
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()

            # Parse JSON (CPU-bound, but fast enough for reasonable file sizes)
            data = json.loads(content)
            logger.debug(f"Loaded snapshot for instance {instance_id}, type {data_type.value}, {len(data)} items")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse snapshot {file_path}: {e}")
            return None
        except IOError as e:
            logger.error(f"Failed to read snapshot {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading snapshot {file_path}: {e}", exc_info=True)
            return None

    @staticmethod
    async def refresh_instance_data(
        db: AsyncSession,
        instance: Instance,
        data_type: DataType
    ) -> DataSnapshot:
        """
        Fetch fresh data from Magento and save snapshot.

        Raises HTTPException on API errors.
        """
        logger.info(f"Refreshing {data_type.value} data for instance {instance.id} ({instance.name})")

        try:
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

            # Save snapshot (includes error handling and rollback)
            snapshot = await DataStorageService.save_snapshot(
                db=db,
                instance_id=instance.id,
                data_type=data_type,
                data=data,
                metadata={"store_views": store_views}
            )

            logger.info(f"Successfully refreshed {data_type.value} data for instance {instance.id}")
            return snapshot

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            logger.error(f"Failed to refresh data for instance {instance.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch data from Magento: {str(e)}"
            )

    @staticmethod
    async def get_or_refresh_data(
        db: AsyncSession,
        instance: Instance,
        data_type: DataType,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get data from snapshot or refresh if needed.

        Args:
            db: Database session
            instance: Magento instance
            data_type: Type of data (blocks or pages)
            force_refresh: If True, always fetch fresh data from Magento

        Returns:
            List of CMS items (blocks or pages)
        """
        if not force_refresh:
            # Try to load existing snapshot
            data = await DataStorageService.load_snapshot(instance.id, data_type)
            if data is not None:
                logger.debug(f"Using cached data for instance {instance.id}, type {data_type.value}")
                return data

        # Refresh data from Magento
        logger.info(f"Cache miss or force_refresh=True for instance {instance.id}, refreshing from Magento")
        await DataStorageService.refresh_instance_data(db, instance, data_type)

        # Load and return the fresh data
        data = await DataStorageService.load_snapshot(instance.id, data_type)
        if data is None:
            logger.error(f"Failed to load snapshot after refresh for instance {instance.id}")
            return []

        return data
