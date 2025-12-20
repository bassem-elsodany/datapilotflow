"""
Timeline Events.

This module defines domain events that extend the existing timeline domain,
enabling real-time progress tracking through the existing timeline system.
"""

from typing import Optional, Dict, Any
from pydantic import Field
from .base import DomainEvent
from ..knowledge.job_timeline import JobTimeline, JobTimelineUpdate


class TimelineEvent(DomainEvent):
    """Base class for timeline events that extend the existing timeline domain."""
    
    job_id: str = Field(description="ID of the knowledge job")
    user_id: str = Field(description="ID of the user who owns the job")
    timeline_id: str = Field(description="ID of the timeline entry")
    
    def __init__(self, **data):
        # Set aggregate_id to job_id for consistency
        if 'aggregate_id' not in data:
            data['aggregate_id'] = data.get('job_id')
        super().__init__(**data)


class TimelineBatchProgressUpdated(TimelineEvent):
    """Event published when timeline batch progress is updated."""
    
    event_type: str = Field(default="timeline_batch_progress_updated", description="Type of the event")
    aggregate_type: str = Field(default="job_timeline", description="Type of the aggregate")
    
    # Batch progress data that updates the timeline (CUMULATIVE VALUES)
    batch_number: int = Field(description="Number of the batch processed")
    total_processed: int = Field(description="CUMULATIVE: Total documents processed so far (accumulated from all previous batches)")
    documents_in_batch: int = Field(description="Number of documents in this specific batch")
    chunks_created: int = Field(description="Number of chunks created in this specific batch")
    total_chunks: int = Field(description="CUMULATIVE: Total chunks created so far (accumulated from all previous batches)")
    processing_time: float = Field(description="CUMULATIVE: Total processing time in seconds (accumulated from all previous batches)")
    
    def to_timeline_update(self) -> JobTimelineUpdate:
        """Convert this event to a JobTimelineUpdate for database updates."""
        return JobTimelineUpdate(
            documents_processed=self.total_processed,
            chunks_created=self.total_chunks,
            processing_time_seconds=self.processing_time
        )
    
    def __init__(self, **data):
        super().__init__(**data)


class TimelineStatusChanged(TimelineEvent):
    """Event published when timeline status changes."""
    
    event_type: str = Field(default="timeline_status_changed", description="Type of the event")
    aggregate_type: str = Field(default="job_timeline", description="Type of the aggregate")
    
    # Status change data
    new_status: str = Field(description="New status of the timeline entry")
    message: Optional[str] = Field(default=None, description="Status change message")
    
    def to_timeline_update(self) -> JobTimelineUpdate:
        """Convert this event to a JobTimelineUpdate for database updates."""
        from ..knowledge.knowledge_job import JobStatus
        return JobTimelineUpdate(
            status=JobStatus(self.new_status),
            completed_at=None if self.new_status != "completed" else None  # Will be set by service
        )
    
    def __init__(self, **data):
        super().__init__(**data)
