from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Dict, Any, Union, Literal
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


class Instance(BaseModel):
    """Instance as returned by the API: the token is write-only and never echoed back."""
    id: int
    name: str
    url: HttpUrl
    is_active: bool
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
    """Request to compare data between two instances.

    Validation rules:
    - source and destination must be different
    - instance IDs must be positive
    """
    source_instance_id: int = Field(..., gt=0)
    destination_instance_id: int = Field(..., gt=0)
    force_refresh: bool = False

    @validator('destination_instance_id')
    def validate_different_instances(cls, v, values):
        """Ensure source and destination are different."""
        if 'source_instance_id' in values and v == values['source_instance_id']:
            raise ValueError("Cannot compare an instance with itself")
        return v


class ComparisonItem(BaseModel):
    identifier: str  # block identifier or page url_key
    title: str
    source_status: ComparisonStatus
    destination_status: ComparisonStatus
    source_data: Optional[Dict[str, Any]] = None
    destination_data: Optional[Dict[str, Any]] = None
    differences: Optional[List[str]] = None


class ComparisonResult(BaseModel):
    source_instance: Optional[Instance] = None
    destination_instance: Optional[Instance] = None
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
    """Request to get detailed diff for a specific item.

    Validation rules:
    - identifier: 1-255 characters
    """
    source_instance_id: int = Field(..., gt=0)
    destination_instance_id: int = Field(..., gt=0)
    data_type: DataType
    identifier: str = Field(..., min_length=1, max_length=255)


class DiffField(BaseModel):
    """Field-level difference between source and destination.

    Values can be:
    - str: Text content, HTML, identifiers
    - int: IDs, sort orders
    - bool: is_active, flags
    - list[int]: store_id arrays
    - list[str]: string arrays
    - None: missing/empty values
    """
    field_name: str
    source_value: Union[str, int, bool, List[int], List[str], None]
    destination_value: Union[str, int, bool, List[int], List[str], None]
    is_different: bool


class DiffResult(BaseModel):
    identifier: str
    data_type: DataType
    fields: List[DiffField]
    source_stores: List[Union[int, str]] = []
    destination_stores: List[Union[int, str]] = []


# Sync Schemas
class SyncItem(BaseModel):
    """Item to be synced from source to destination.

    Validation rules:
    - identifier: 1-255 characters
    - action: must be 'create' or 'update'
    - fields_to_sync: optional list of field names (max 50 fields)
    """
    identifier: str = Field(..., min_length=1, max_length=255)
    action: Literal['create', 'update']
    fields_to_sync: Optional[List[str]] = Field(None, max_length=50)

    @validator('fields_to_sync')
    def validate_field_names(cls, v):
        """Validate that field names are from allowed set."""
        if v is not None:
            # Define valid fields for both blocks and pages
            valid_fields = {
                # Common fields
                'title', 'content', 'active', 'is_active', 'store_id',
                # Block-specific
                'identifier', 'sort_order',
                # Page-specific
                'content_heading', 'page_layout', 'meta_title',
                'meta_keywords', 'meta_description', 'url_key',
                'layout_update_xml', 'custom_theme', 'custom_root_template',
                'custom_layout_update_xml'
            }
            invalid_fields = [f for f in v if f not in valid_fields]
            if invalid_fields:
                raise ValueError(f"Invalid field names: {', '.join(invalid_fields)}")
        return v


class SyncRequest(BaseModel):
    """Request to synchronize items between instances.

    Validation rules:
    - source and destination must be different
    - items list: 1-100 items
    - store_view_mapping: maps source store IDs to destination store IDs
    """
    source_instance_id: int = Field(..., gt=0)
    destination_instance_id: int = Field(..., gt=0)
    data_type: DataType
    items: List[SyncItem] = Field(..., min_length=1, max_length=100)
    store_view_mapping: Optional[Dict[str, str]] = None

    @validator('destination_instance_id')
    def validate_different_instances(cls, v, values):
        """Ensure source and destination are different."""
        if 'source_instance_id' in values and v == values['source_instance_id']:
            raise ValueError("Source and destination instances must be different")
        return v


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