from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SyncStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class DataType(str, Enum):
    BLOCKS = "blocks"
    PAGES = "pages"


class ComparisonStatus(str, Enum):
    EXISTS = "exists"
    MISSING = "missing"
    DIFFERENT = "different"


# Instance Schemas
class InstanceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl
    api_token: str = Field(..., min_length=1)
    is_active: bool = True


class InstanceCreate(InstanceBase):
    pass


class InstanceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[HttpUrl] = None
    api_token: Optional[str] = Field(None, min_length=1)
    is_active: Optional[bool] = None


class Instance(InstanceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InstanceTestResult(BaseModel):
    success: bool
    message: str
    version: Optional[str] = None
    store_views: Optional[List[Dict[str, Any]]] = None


# Data Snapshot Schemas
class DataSnapshotBase(BaseModel):
    instance_id: int
    data_type: DataType
    file_path: str
    item_count: int = 0
    snapshot_metadata: Dict[str, Any] = {}


class DataSnapshot(DataSnapshotBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Comparison Schemas
class ComparisonRequest(BaseModel):
    source_instance_id: int
    destination_instance_id: int
    force_refresh: bool = False


class ComparisonItem(BaseModel):
    identifier: str  # block identifier or page url_key
    title: str
    source_status: ComparisonStatus
    destination_status: ComparisonStatus
    source_data: Optional[Dict[str, Any]] = None
    destination_data: Optional[Dict[str, Any]] = None
    differences: Optional[List[str]] = None


class ComparisonResult(BaseModel):
    source_instance: Instance
    destination_instance: Instance
    data_type: DataType
    total_source: int
    total_destination: int
    exists_in_both: int
    missing_in_destination: int
    missing_in_source: int
    different: int
    items: List[ComparisonItem]
    compared_at: datetime


# Diff Schemas
class DiffRequest(BaseModel):
    source_instance_id: int
    destination_instance_id: int
    data_type: DataType
    identifier: str


class DiffField(BaseModel):
    field_name: str
    source_value: Any
    destination_value: Any
    is_different: bool


class DiffResult(BaseModel):
    identifier: str
    data_type: DataType
    fields: List[DiffField]
    source_stores: List[str] = []
    destination_stores: List[str] = []


# Sync Schemas
class SyncItem(BaseModel):
    identifier: str
    action: str  # 'create' or 'update'
    fields_to_sync: Optional[List[str]] = None  # If None, sync all fields


class SyncRequest(BaseModel):
    source_instance_id: int
    destination_instance_id: int
    data_type: DataType
    items: List[SyncItem]
    store_view_mapping: Optional[Dict[str, str]] = None


class SyncPreview(BaseModel):
    items: List[Dict[str, Any]]
    total_changes: int
    creates: int
    updates: int


class SyncResult(BaseModel):
    sync_id: int
    status: SyncStatus
    items_synced: int
    items_failed: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    details: List[Dict[str, Any]] = []
    error_message: Optional[str] = None