"""
Job domain events.

This module defines domain events related to knowledge processing jobs.
"""

from typing import Any, Dict, Optional

from pydantic import Field

from .base import DomainEvent


class JobActionRequested(DomainEvent):
    """
    Event published when a user requests a job action (start or cancel).

    This event is triggered when a user clicks the "Start Processing", "Execute Job",
    or "Cancel Job" button in the UI. The event listener will process the action
    based on the execution_context.action field.
    """

    event_type: str = Field(
        default="knowledge_job_action_requested", description="Type of the event"
    )

    # Event-specific payload - these match the expected structure
    job_id: str = Field(description="ID of the knowledge job to execute")
    user_id: str = Field(description="ID of the user who requested execution")
    requested_at: str = Field(description="Timestamp when execution was requested")

    # Optional metadata for additional context
    execution_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional context for job execution"
    )

    def __init__(self, **data):
        super().__init__(**data)


class JobExecutionScheduled(DomainEvent):
    """
    Event published when a job execution is scheduled for async processing.

    This event is triggered after JobExecutionRequested and indicates
    that the job has been queued for background processing.
    """

    event_type: str = Field(
        default="job_execution_scheduled", description="Type of the event"
    )

    # Event-specific payload
    job_id: str = Field(description="ID of the knowledge job")
    scheduled_at: str = Field(description="Timestamp when job was scheduled")
    queue_name: Optional[str] = Field(
        default=None, description="Name of the processing queue"
    )

    def __init__(self, **data):
        super().__init__(**data)


class JobStarted(DomainEvent):
    """
    Event published when a knowledge processing job starts execution.
    """

    event_type: str = Field(default="job_started", description="Type of the event")

    # Event-specific payload
    job_id: str = Field(description="ID of the knowledge job")
    started_at: str = Field(description="Timestamp when job started")

    def __init__(self, **data):
        super().__init__(**data)


class JobCompleted(DomainEvent):
    """
    Event published when a knowledge processing job completes successfully.
    """

    event_type: str = Field(default="job_completed", description="Type of the event")

    # Event-specific payload
    job_id: str = Field(description="ID of the knowledge job")
    completed_at: str = Field(description="Timestamp when job completed")
    documents_processed: int = Field(description="Number of documents processed")
    chunks_created: int = Field(description="Number of chunks created")

    def __init__(self, **data):
        super().__init__(**data)


class JobFailed(DomainEvent):
    """
    Event published when a knowledge processing job fails.
    """

    event_type: str = Field(default="job_failed", description="Type of the event")

    # Event-specific payload
    job_id: str = Field(description="ID of the knowledge job")
    failed_at: str = Field(description="Timestamp when job failed")
    error_message: str = Field(description="Error message describing the failure")
    error_type: Optional[str] = Field(
        default=None, description="Type of error that occurred"
    )

    def __init__(self, **data):
        super().__init__(**data)


class JobCancelled(DomainEvent):
    """
    Event published when a knowledge processing job is cancelled.
    """

    event_type: str = Field(default="job_cancelled", description="Type of the event")

    # Event-specific payload
    job_id: str = Field(description="ID of the knowledge job")
    cancelled_at: str = Field(description="Timestamp when job was cancelled")
    cancelled_by: str = Field(description="ID of the user who cancelled the job")
    reason: Optional[str] = Field(default=None, description="Reason for cancellation")

    def __init__(self, **data):
        super().__init__(**data)
