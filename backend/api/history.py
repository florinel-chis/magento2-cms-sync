from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import logging

from models.database import get_db
from models.models import SyncHistory, Instance
from models.schemas import SyncStatus

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_sync_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    sync_type: Optional[str] = None,
    source_instance_id: Optional[int] = None,
    destination_instance_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get sync history with optional filters.

    Uses eager loading to prevent N+1 queries when fetching related instances.
    """
    # Use eager loading to prevent N+1 queries
    query = (
        select(SyncHistory)
        .options(
            selectinload(SyncHistory.source_instance),
            selectinload(SyncHistory.destination_instance)
        )
        .order_by(SyncHistory.started_at.desc())
    )
    
    # Apply filters
    filters = []
    if status:
        filters.append(SyncHistory.sync_status == status)
    if sync_type:
        filters.append(SyncHistory.sync_type == sync_type)
    if source_instance_id:
        filters.append(SyncHistory.source_instance_id == source_instance_id)
    if destination_instance_id:
        filters.append(SyncHistory.destination_instance_id == destination_instance_id)
    if start_date:
        filters.append(SyncHistory.started_at >= start_date)
    if end_date:
        filters.append(SyncHistory.started_at <= end_date)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar()
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    history_items = result.scalars().all()

    logger.debug(f"Fetched {len(history_items)} sync history items")

    # Access preloaded instances (no additional queries!)
    history_data = []
    for item in history_items:
        # Instances are already loaded via selectinload - no N+1 queries!
        history_data.append({
            "id": item.id,
            "source_instance_id": item.source_instance_id,
            "source_instance_name": item.source_instance.name if item.source_instance else "Unknown",
            "destination_instance_id": item.destination_instance_id,
            "destination_instance_name": item.destination_instance.name if item.destination_instance else "Unknown",
            "sync_type": item.sync_type,
            "sync_status": item.sync_status,
            "items_synced": item.items_synced,
            "items_failed": item.items_failed,
            "started_at": item.started_at,
            "completed_at": item.completed_at,
            "error_message": item.error_message,
            "duration": (item.completed_at - item.started_at).total_seconds() if item.completed_at else None
        })
    
    return {
        "items": history_data,
        "total": total_count,
        "skip": skip,
        "limit": limit
    }


@router.get("/statistics")
async def get_sync_statistics(
    period: str = Query("today", regex="^(today|week|month|all)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get sync statistics for dashboard"""
    # Calculate date range
    now = datetime.now(timezone.utc)
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:  # all
        start_date = None
    
    # Build base query
    query = select(SyncHistory)
    if start_date:
        query = query.where(SyncHistory.started_at >= start_date)
    
    result = await db.execute(query)
    all_syncs = result.scalars().all()
    
    # Calculate statistics
    total_syncs = len(all_syncs)
    completed_syncs = sum(1 for s in all_syncs if s.sync_status == SyncStatus.COMPLETED.value)
    failed_syncs = sum(1 for s in all_syncs if s.sync_status == SyncStatus.FAILED.value)
    total_items_synced = sum(s.items_synced for s in all_syncs)
    total_items_failed = sum(s.items_failed for s in all_syncs)
    
    success_rate = (completed_syncs / total_syncs * 100) if total_syncs > 0 else 0
    
    # Get active syncs
    active_result = await db.execute(
        select(SyncHistory).where(
            SyncHistory.sync_status.in_([SyncStatus.PENDING.value, SyncStatus.IN_PROGRESS.value])
        )
    )
    active_syncs = active_result.scalars().all()
    
    return {
        "period": period,
        "total_syncs": total_syncs,
        "completed_syncs": completed_syncs,
        "failed_syncs": failed_syncs,
        "active_syncs": len(active_syncs),
        "success_rate": round(success_rate, 2),
        "total_items_synced": total_items_synced,
        "total_items_failed": total_items_failed,
        "active_sync_details": [
            {
                "id": sync.id,
                "sync_type": sync.sync_type,
                "status": sync.sync_status,
                "progress": (sync.items_synced / (sync.items_synced + sync.items_failed)) * 100 
                           if (sync.items_synced + sync.items_failed) > 0 else 0
            }
            for sync in active_syncs
        ]
    }


@router.get("/{sync_id}")
async def get_sync_details(
    sync_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific sync"""
    result = await db.execute(
        select(SyncHistory).where(SyncHistory.id == sync_id)
    )
    sync = result.scalar_one_or_none()
    
    if not sync:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync history not found"
        )
    
    # Get instance names
    source_result = await db.execute(
        select(Instance).where(Instance.id == sync.source_instance_id)
    )
    source_instance = source_result.scalar_one_or_none()
    
    dest_result = await db.execute(
        select(Instance).where(Instance.id == sync.destination_instance_id)
    )
    dest_instance = dest_result.scalar_one_or_none()
    
    return {
        "id": sync.id,
        "source_instance": {
            "id": sync.source_instance_id,
            "name": source_instance.name if source_instance else "Unknown"
        },
        "destination_instance": {
            "id": sync.destination_instance_id,
            "name": dest_instance.name if dest_instance else "Unknown"
        },
        "sync_type": sync.sync_type,
        "sync_status": sync.sync_status,
        "items_synced": sync.items_synced,
        "items_failed": sync.items_failed,
        "started_at": sync.started_at,
        "completed_at": sync.completed_at,
        "duration": (sync.completed_at - sync.started_at).total_seconds() if sync.completed_at else None,
        "error_message": sync.error_message,
        "sync_details": sync.sync_details
    }