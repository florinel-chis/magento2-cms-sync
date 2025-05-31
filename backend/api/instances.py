from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
import httpx
from pathlib import Path
import shutil

from models.database import get_db
from models.models import Instance as InstanceModel, DataSnapshot
from models.schemas import Instance, InstanceCreate, InstanceUpdate, InstanceTestResult
from integrations.magento_client import MagentoClient
from config import settings

router = APIRouter()


@router.get("/", response_model=List[Instance])
async def list_instances(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(InstanceModel).offset(skip).limit(limit)
    )
    instances = result.scalars().all()
    return instances


@router.get("/{instance_id}", response_model=Instance)
async def get_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(InstanceModel).where(InstanceModel.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    return instance


@router.post("/", response_model=Instance)
async def create_instance(
    instance_data: InstanceCreate,
    db: AsyncSession = Depends(get_db)
):
    # Check if instance with same name exists
    result = await db.execute(
        select(InstanceModel).where(InstanceModel.name == instance_data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instance with this name already exists"
        )
    
    # Create instance
    instance_dict = instance_data.model_dump()
    # Convert HttpUrl to string
    instance_dict['url'] = str(instance_data.url)
    instance = InstanceModel(**instance_dict)
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    
    # Create data directory for this instance
    instance_dir = settings.instances_data_dir / str(instance.id)
    instance_dir.mkdir(parents=True, exist_ok=True)
    
    return instance


@router.put("/{instance_id}", response_model=Instance)
async def update_instance(
    instance_id: int,
    instance_data: InstanceUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(InstanceModel).where(InstanceModel.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    # Check if new name conflicts with existing instance
    if instance_data.name and instance_data.name != instance.name:
        result = await db.execute(
            select(InstanceModel).where(InstanceModel.name == instance_data.name)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instance with this name already exists"
            )
    
    # Update instance
    update_data = instance_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Convert HttpUrl to string if updating URL
        if field == 'url' and value is not None:
            value = str(value)
        setattr(instance, field, value)
    
    await db.commit()
    await db.refresh(instance)
    
    return instance


@router.delete("/{instance_id}")
async def delete_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(InstanceModel).where(InstanceModel.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    # Delete data directory for this instance
    instance_dir = settings.instances_data_dir / str(instance_id)
    if instance_dir.exists():
        shutil.rmtree(instance_dir)
    
    # Delete instance
    await db.delete(instance)
    await db.commit()
    
    return {"message": "Instance deleted successfully"}


@router.post("/{instance_id}/test", response_model=InstanceTestResult)
async def test_instance_connection(
    instance_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(InstanceModel).where(InstanceModel.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    try:
        client = MagentoClient(
            base_url=str(instance.url),
            token=instance.api_token
        )
        
        # Test connection by fetching store views
        store_views = await client.get_store_views()
        
        return InstanceTestResult(
            success=True,
            message="Connection successful",
            store_views=store_views
        )
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return InstanceTestResult(
                success=False,
                message="Authentication failed. Please check your API token."
            )
        else:
            return InstanceTestResult(
                success=False,
                message=f"HTTP error: {e.response.status_code}"
            )
    except Exception as e:
        return InstanceTestResult(
            success=False,
            message=f"Connection failed: {str(e)}"
        )


@router.get("/{instance_id}/data-snapshots")
async def get_instance_data_snapshots(
    instance_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get data snapshot information for an instance"""
    # Verify instance exists
    instance_result = await db.execute(
        select(InstanceModel).where(InstanceModel.id == instance_id)
    )
    instance = instance_result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )
    
    # Get latest snapshots for blocks and pages
    blocks_result = await db.execute(
        select(DataSnapshot)
        .where(
            DataSnapshot.instance_id == instance_id,
            DataSnapshot.data_type == "blocks"
        )
        .order_by(DataSnapshot.created_at.desc())
        .limit(1)
    )
    blocks_snapshot = blocks_result.scalar_one_or_none()
    
    pages_result = await db.execute(
        select(DataSnapshot)
        .where(
            DataSnapshot.instance_id == instance_id,
            DataSnapshot.data_type == "pages"
        )
        .order_by(DataSnapshot.created_at.desc())
        .limit(1)
    )
    pages_snapshot = pages_result.scalar_one_or_none()
    
    return {
        "instance_id": instance_id,
        "blocks": {
            "count": blocks_snapshot.item_count,
            "last_updated": blocks_snapshot.created_at.isoformat()
        } if blocks_snapshot else None,
        "pages": {
            "count": pages_snapshot.item_count,
            "last_updated": pages_snapshot.created_at.isoformat()
        } if pages_snapshot else None
    }


@router.get("/data-snapshots/all")
async def get_all_data_snapshots(
    db: AsyncSession = Depends(get_db)
):
    """Get data snapshot information for all instances"""
    # Get all instances
    instances_result = await db.execute(select(InstanceModel))
    instances = instances_result.scalars().all()
    
    snapshots_info = {}
    
    for instance in instances:
        # Get latest snapshots for blocks and pages
        blocks_result = await db.execute(
            select(DataSnapshot)
            .where(
                DataSnapshot.instance_id == instance.id,
                DataSnapshot.data_type == "blocks"
            )
            .order_by(DataSnapshot.created_at.desc())
            .limit(1)
        )
        blocks_snapshot = blocks_result.scalar_one_or_none()
        
        pages_result = await db.execute(
            select(DataSnapshot)
            .where(
                DataSnapshot.instance_id == instance.id,
                DataSnapshot.data_type == "pages"
            )
            .order_by(DataSnapshot.created_at.desc())
            .limit(1)
        )
        pages_snapshot = pages_result.scalar_one_or_none()
        
        snapshots_info[instance.id] = {
            "blocks": {
                "count": blocks_snapshot.item_count,
                "lastUpdated": blocks_snapshot.created_at.isoformat()
            } if blocks_snapshot else None,
            "pages": {
                "count": pages_snapshot.item_count,
                "lastUpdated": pages_snapshot.created_at.isoformat()
            } if pages_snapshot else None
        }
    
    return snapshots_info