"""
Job Timeline domain models.

This module defines the domain models for tracking job execution timelines,
allowing multiple executions of the same job with detailed history.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datapilotflow.domain.knowledge.knowledge_job import JobStatus


class JobTimeline(BaseModel):
    """Timeline entry for a job execution.
    
    This model represents a single execution of a knowledge processing job,
    allowing multiple executions of the same job to be tracked separately.
    """
    
    id: str = Field(description="Unique identifier for this timeline entry")
    job_id: str = Field(description="ID of the knowledge job this execution belongs to")
    user_id: str = Field(description="ID of the user who owns the job")
    
    # Execution details
    status: JobStatus = Field(description="Status of this execution")
    started_at: Optional[datetime] = Field(default=None, description="When this execution started")
    completed_at: Optional[datetime] = Field(default=None, description="When this execution completed")
    
    # Execution statistics
    documents_processed: int = Field(default=0, description="Number of documents processed in this execution")
    chunks_created: int = Field(default=0, description="Number of chunks created in this execution")
    processing_time_seconds: float = Field(default=0.0, description="Total processing time in seconds")
    
    # Error handling
    error_message: Optional[str] = Field(default=None, description="Error message if execution failed")
    error_traceback: Optional[str] = Field(default=None, description="Full error traceback if execution failed")
    
    # Execution context
    execution_context: Optional[Dict[str, Any]] = Field(default=None, description="Context about how this execution was triggered")
    triggered_by: Optional[str] = Field(default=None, description="Who/what triggered this execution (user_id, system, etc.)")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this timeline entry was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When this timeline entry was last updated")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class JobTimelineCreate(BaseModel):
    """Model for creating a new job timeline entry."""
    
    job_id: str = Field(description="ID of the knowledge job this execution belongs to")
    user_id: str = Field(description="ID of the user who owns the job")
    status: JobStatus = Field(description="Status of this execution")
    started_at: Optional[datetime] = Field(default=None, description="When this execution started")
    documents_processed: int = Field(default=0, description="Number of documents processed in this execution")
    chunks_created: int = Field(default=0, description="Number of chunks created in this execution")
    processing_time_seconds: float = Field(default=0.0, description="Total processing time in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if execution failed")
    error_traceback: Optional[str] = Field(default=None, description="Full error traceback if execution failed")
    execution_context: Optional[Dict[str, Any]] = Field(default=None, description="Context about how this execution was triggered")
    triggered_by: Optional[str] = Field(default=None, description="Who/what triggered this execution")


class JobTimelineUpdate(BaseModel):
    """Model for updating an existing job timeline entry."""
    
    status: Optional[JobStatus] = Field(default=None, description="Status of this execution")
    started_at: Optional[datetime] = Field(default=None, description="When this execution started")
    completed_at: Optional[datetime] = Field(default=None, description="When this execution completed")
    documents_processed: Optional[int] = Field(default=None, description="Number of documents processed in this execution")
    chunks_created: Optional[int] = Field(default=None, description="Number of chunks created in this execution")
    processing_time_seconds: Optional[float] = Field(default=None, description="Total processing time in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if execution failed")
    error_traceback: Optional[str] = Field(default=None, description="Full error traceback if execution failed")
    execution_context: Optional[Dict[str, Any]] = Field(default=None, description="Context about how this execution was triggered")
    triggered_by: Optional[str] = Field(default=None, description="Who/what triggered this execution")
