from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import get_db
from models.models import Instance
from models.schemas import (
    ComparisonRequest, ComparisonResult, DataType,
    DiffRequest, DiffResult
)
from services.data_storage import DataStorageService
from services.comparison import ComparisonService

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


@router.post("/blocks", response_model=ComparisonResult)
async def compare_blocks(
    request: ComparisonRequest,
    db: AsyncSession = Depends(get_db)
):
    """Compare CMS blocks between two instances"""
    # Get instances
    source_instance = await get_instance_or_404(db, request.source_instance_id)
    dest_instance = await get_instance_or_404(db, request.destination_instance_id)
    
    # Get data for both instances
    source_data = await DataStorageService.get_or_refresh_data(
        db, source_instance, DataType.BLOCKS, request.force_refresh
    )
    dest_data = await DataStorageService.get_or_refresh_data(
        db, dest_instance, DataType.BLOCKS, request.force_refresh
    )
    
    # Compare data
    result = ComparisonService.compare_data(
        source_data=source_data,
        dest_data=dest_data,
        data_type=DataType.BLOCKS,
        source_instance=source_instance,
        dest_instance=dest_instance
    )
    
    return result


@router.post("/pages", response_model=ComparisonResult)
async def compare_pages(
    request: ComparisonRequest,
    db: AsyncSession = Depends(get_db)
):
    """Compare CMS pages between two instances"""
    # Get instances
    source_instance = await get_instance_or_404(db, request.source_instance_id)
    dest_instance = await get_instance_or_404(db, request.destination_instance_id)
    
    # Get data for both instances
    source_data = await DataStorageService.get_or_refresh_data(
        db, source_instance, DataType.PAGES, request.force_refresh
    )
    dest_data = await DataStorageService.get_or_refresh_data(
        db, dest_instance, DataType.PAGES, request.force_refresh
    )
    
    # Compare data
    result = ComparisonService.compare_data(
        source_data=source_data,
        dest_data=dest_data,
        data_type=DataType.PAGES,
        source_instance=source_instance,
        dest_instance=dest_instance
    )
    
    return result


@router.post("/diff", response_model=DiffResult)
async def get_item_diff(
    request: DiffRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed diff for a specific item"""
    # Get instances
    source_instance = await get_instance_or_404(db, request.source_instance_id)
    dest_instance = await get_instance_or_404(db, request.destination_instance_id)
    
    # Load data (async file I/O)
    source_data = await DataStorageService.load_snapshot(source_instance.id, request.data_type)
    dest_data = await DataStorageService.load_snapshot(dest_instance.id, request.data_type)
    
    if source_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data snapshot found for source instance. Please run comparison first."
        )
    
    if dest_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data snapshot found for destination instance. Please run comparison first."
        )
    
    # Find items
    source_item = None
    dest_item = None
    
    for item in source_data:
        if request.data_type == DataType.BLOCKS:
            if item.get("identifier") == request.identifier:
                source_item = item
                break
        else:  # DataType.PAGES
            # Try identifier first (newer Magento versions), then url_key (older versions)
            if item.get("identifier") == request.identifier or item.get("url_key") == request.identifier:
                source_item = item
                break
    
    for item in dest_data:
        if request.data_type == DataType.BLOCKS:
            if item.get("identifier") == request.identifier:
                dest_item = item
                break
        else:  # DataType.PAGES
            # Try identifier first (newer Magento versions), then url_key (older versions)
            if item.get("identifier") == request.identifier or item.get("url_key") == request.identifier:
                dest_item = item
                break
    
    if not source_item and not dest_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with identifier '{request.identifier}' not found in either instance"
        )
    
    # Get diff
    diff_result = ComparisonService.get_item_diff(
        source_item=source_item,
        dest_item=dest_item,
        data_type=request.data_type,
        identifier=request.identifier
    )
    
    return diff_result


@router.post("/refresh/{instance_id}")
async def refresh_instance_data(
    instance_id: int,
    data_type: DataType,
    db: AsyncSession = Depends(get_db)
):
    """Manually refresh data for a specific instance"""
    instance = await get_instance_or_404(db, instance_id)
    
    snapshot = await DataStorageService.refresh_instance_data(
        db, instance, data_type
    )
    
    return {
        "message": "Data refreshed successfully",
        "snapshot_id": snapshot.id,
        "item_count": snapshot.item_count,
        "created_at": snapshot.created_at
    }