from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base


class Instance(Base):
    __tablename__ = "instances"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    url = Column(String(500), nullable=False)
    api_token = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    data_snapshots = relationship("DataSnapshot", back_populates="instance", cascade="all, delete-orphan")
    sync_history = relationship("SyncHistory", foreign_keys="SyncHistory.source_instance_id", cascade="all, delete-orphan")


class DataSnapshot(Base):
    __tablename__ = "data_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("instances.id"), nullable=False)
    data_type = Column(String(50), nullable=False)  # 'blocks' or 'pages'
    file_path = Column(String(500), nullable=False)  # Path to JSON file
    item_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    snapshot_metadata = Column(JSON, default=dict)  # Store additional info like store views
    
    # Relationships
    instance = relationship("Instance", back_populates="data_snapshots")


class SyncHistory(Base):
    __tablename__ = "sync_history"
    
    id = Column(Integer, primary_key=True, index=True)
    source_instance_id = Column(Integer, ForeignKey("instances.id"), nullable=False)
    destination_instance_id = Column(Integer, ForeignKey("instances.id"), nullable=False)
    sync_type = Column(String(50), nullable=False)  # 'blocks' or 'pages'
    sync_status = Column(String(50), nullable=False)  # 'pending', 'in_progress', 'completed', 'failed'
    items_synced = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    sync_details = Column(JSON, default=dict)  # Detailed results for each item
    
    # Relationships
    source_instance = relationship("Instance", foreign_keys=[source_instance_id], overlaps="sync_history")
    destination_instance = relationship("Instance", foreign_keys=[destination_instance_id], overlaps="sync_history")


class ComparisonCache(Base):
    __tablename__ = "comparison_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    source_instance_id = Column(Integer, ForeignKey("instances.id"), nullable=False)
    destination_instance_id = Column(Integer, ForeignKey("instances.id"), nullable=False)
    comparison_type = Column(String(50), nullable=False)  # 'blocks' or 'pages'
    cache_key = Column(String(255), unique=True, nullable=False)
    result_summary = Column(JSON, nullable=False)  # Summary statistics
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    source_instance = relationship("Instance", foreign_keys=[source_instance_id], overlaps="sync_history")
    destination_instance = relationship("Instance", foreign_keys=[destination_instance_id], overlaps="sync_history")