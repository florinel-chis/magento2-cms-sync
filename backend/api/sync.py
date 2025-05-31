from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List
from datetime import datetime

from models.database import get_db, AsyncSessionLocal
from models.models import Instance, SyncHistory
from models.schemas import (
    SyncRequest, SyncPreview, SyncResult, SyncStatus,
    DataType
)
from services.data_storage import DataStorageService
from services.sync import SyncService
from integrations.magento_client import MagentoClient

router = APIRouter()


async def get_instance_or_404(db: AsyncSession, instance_id: int) -> Instance:
    """Helper to get instance or raise 404"""
    result = await db.execute(
        select(Instance).where(Instance.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instance with id {instance_id} not found"
        )
    
    return instance


@router.post("/preview", response_model=SyncPreview)
async def preview_sync(
    request: SyncRequest,
    db: AsyncSession = Depends(get_db)
):
    """Preview what changes would be made during sync"""
    # Get instances
    source_instance = await get_instance_or_404(db, request.source_instance_id)
    dest_instance = await get_instance_or_404(db, request.destination_instance_id)
    
    # Load data
    source_data = DataStorageService.load_snapshot(source_instance.id, request.data_type)
    dest_data = DataStorageService.load_snapshot(dest_instance.id, request.data_type)
    
    if source_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data snapshot found for source instance. Please run comparison first."
        )
    
    # Create preview
    sync_service = SyncService()
    preview = sync_service.create_sync_preview(
        source_data=source_data,
        dest_data=dest_data or [],
        data_type=request.data_type,
        sync_items=request.items,
        store_view_mapping=request.store_view_mapping
    )
    
    return preview


@router.post("/blocks", response_model=SyncResult)
async def sync_blocks(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Sync CMS blocks from source to destination"""
    return await _perform_sync(request, DataType.BLOCKS, background_tasks, db)


@router.post("/pages", response_model=SyncResult)
async def sync_pages(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Sync CMS pages from source to destination"""
    return await _perform_sync(request, DataType.PAGES, background_tasks, db)


async def _perform_sync(
    request: SyncRequest,
    data_type: DataType,
    background_tasks: BackgroundTasks,
    db: AsyncSession
) -> SyncResult:
    """Perform the actual sync operation"""
    # Validate data type matches
    if request.data_type != data_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data type mismatch. Expected {data_type.value}"
        )
    
    # Get instances
    source_instance = await get_instance_or_404(db, request.source_instance_id)
    dest_instance = await get_instance_or_404(db, request.destination_instance_id)
    
    
    # Create sync history record
    sync_history = SyncHistory(
        source_instance_id=source_instance.id,
        destination_instance_id=dest_instance.id,
        sync_type=data_type.value,
        sync_status=SyncStatus.PENDING.value,
        sync_details={"items": [item.model_dump() for item in request.items]}
    )
    db.add(sync_history)
    await db.commit()
    await db.refresh(sync_history)
    
    # Start sync in background
    background_tasks.add_task(
        _execute_sync,
        sync_history.id,
        source_instance,
        dest_instance,
        request
    )
    
    return SyncResult(
        sync_id=sync_history.id,
        status=SyncStatus.PENDING,
        items_synced=0,
        items_failed=0,
        started_at=sync_history.started_at,
        completed_at=None,
        details=[],
        error_message=None
    )


async def _execute_sync(
    sync_id: int,
    source_instance: Instance,
    dest_instance: Instance,
    request: SyncRequest
):
    """Execute sync operation (runs in background)"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get sync history record
            result = await db.execute(
                select(SyncHistory).where(SyncHistory.id == sync_id)
            )
            sync_history = result.scalar_one()
            
            # Update status to in progress
            sync_history.sync_status = SyncStatus.IN_PROGRESS.value
            await db.commit()
            
            # Load source data
            source_data = DataStorageService.load_snapshot(
                source_instance.id, request.data_type
            )
            
            if not source_data:
                raise Exception("No source data found")
            
            # Create Magento client for destination
            dest_client = MagentoClient(
                base_url=str(dest_instance.url),
                token=dest_instance.api_token
            )
            
            # Perform sync
            sync_service = SyncService()
            
            results = await sync_service.execute_sync(
                source_data=source_data,
                dest_client=dest_client,
                data_type=request.data_type,
                sync_items=request.items,
                store_view_mapping=request.store_view_mapping
            )
            
            # Update sync history
            sync_history.sync_status = SyncStatus.COMPLETED.value
            sync_history.completed_at = datetime.utcnow()
            sync_history.items_synced = len([r for r in results if r["success"]])
            sync_history.items_failed = len([r for r in results if not r["success"]])
            sync_history.sync_details = {"results": results}
            
            # Refresh destination data
            await DataStorageService.refresh_instance_data(
                db, dest_instance, request.data_type
            )
            
        except Exception as e:
            # Update sync history with error
            sync_history.sync_status = SyncStatus.FAILED.value
            sync_history.completed_at = datetime.utcnow()
            sync_history.error_message = str(e)
        
        await db.commit()


@router.get("/status/{sync_id}", response_model=SyncResult)
async def get_sync_status(
    sync_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the status of a sync operation"""
    result = await db.execute(
        select(SyncHistory).where(SyncHistory.id == sync_id)
    )
    sync_history = result.scalar_one_or_none()
    
    if not sync_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync operation not found"
        )
    
    details = sync_history.sync_details.get("results", []) if sync_history.sync_details else []
    
    return SyncResult(
        sync_id=sync_history.id,
        status=SyncStatus(sync_history.sync_status),
        items_synced=sync_history.items_synced,
        items_failed=sync_history.items_failed,
        started_at=sync_history.started_at,
        completed_at=sync_history.completed_at,
        details=details,
        error_message=sync_history.error_message
    )