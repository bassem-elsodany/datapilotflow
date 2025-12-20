"""
Pydantic models for RAG file upload tracking.

This module defines the data models for tracking file uploads, processing status,
and failed events in the RAG system.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class FileUploadStatus(str, Enum):
    """Enum for file upload processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class StatusHistoryEntry(BaseModel):
    """Model for tracking status changes."""
    status: FileUploadStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message: str
    step: str
    error: Optional[str] = None
    traceback: Optional[str] = None


class ProcessingResults(BaseModel):
    """Model for tracking processing results."""
    chunks_created: int = 0
    llm_enrichment_enabled: bool = True
    enriched_chunks: int = 0
    processing_time_seconds: Optional[float] = None
    output_file: Optional[str] = None
    knowledge_source_id: Optional[str] = None
    document_id: Optional[str] = Field(description="Document ID for the processed file")
    chunk_ids: List[str] = Field(default_factory=list, description="List of chunk IDs created from the file")


class ErrorDetails(BaseModel):
    """Model for tracking error details."""
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    failed_step: Optional[str] = None
    retry_count: int = 0
    dlq_event: Optional[Dict[str, Any]] = None


class FileLocations(BaseModel):
    """Model for tracking file locations."""
    inbound: Optional[str] = None
    failed: Optional[str] = None
    archive: Optional[str] = None


class FileMetadata(BaseModel):
    """Model for file metadata."""
    source: str = "web_ui"
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    priority: str = "normal"


class RagFileUpload(BaseModel):
    """Main model for RAG file upload tracking."""
    
    # Core fields
    file_id: str = Field(description="Unique file ID (UUID)")
    user_id: Optional[str] = Field(description="ID of the user who uploaded the file")
    original_filename: str = Field(description="Original filename from upload")
    safe_filename: str = Field(description="Safe filename stored on disk")
    file_path: str = Field(description="Full path to the file")
    file_size: int = Field(description="File size in bytes")
    content_type: str = Field(description="MIME type of the file")
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Status tracking
    status: FileUploadStatus = Field(default=FileUploadStatus.UPLOADED)
    current_step: Optional[str] = Field(description="Current processing step")
    status_history: List[StatusHistoryEntry] = Field(default_factory=list)
    
    # Processing results
    processing_results: Optional[ProcessingResults] = None
    
    # Error details
    error_details: Optional[ErrorDetails] = None
    
    # File locations
    file_locations: FileLocations = Field(default_factory=FileLocations)
    
    # Metadata
    metadata: FileMetadata = Field(default_factory=FileMetadata)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(json_encoders={
        datetime: lambda v: v.isoformat()
    })


class RagFailedEvent(BaseModel):
    """Model for tracking failed events in DLQ."""
    
    # Event identification
    event_id: str = Field(description="Unique event ID")
    original_event: Dict[str, Any] = Field(description="Original event that failed")
    
    # Error information
    error_type: str = Field(description="Type of error that occurred")
    error_message: str = Field(description="Error message")
    traceback: str = Field(description="Full error traceback")
    failed_step: str = Field(description="Step where failure occurred")
    
    # Context
    source_queue: str = Field(description="Queue where failure occurred")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    
    # Timestamps
    failed_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    model_config = ConfigDict(json_encoders={
        datetime: lambda v: v.isoformat()
    }) 