"""
Events domain models and constants.

This subpackage contains all event-related domain models, event handlers,
event dispatching, and shared event system constants.
"""

from .base import (
    DomainEvent,
    EventDispatcher,
    EventHandler,
    dispatch_event,
    dispatch_events,
    get_event_dispatcher,
)
from .constants import (
    # Event Exchanges
    FILE_UPLOAD_EVENTS_EXCHANGE,
    FILE_UPLOAD_EVENTS_DLQ_EXCHANGE,
    JOB_EVENTS_EXCHANGE,
    JOB_EVENTS_DLQ_EXCHANGE,
    NOTIFICATION_EVENTS_EXCHANGE,
    NOTIFICATION_EVENTS_DLQ_EXCHANGE,
    TIMELINE_EVENTS_EXCHANGE,
    TIMELINE_EVENTS_DLQ_EXCHANGE,
    # Event Queues
    FILE_UPLOAD_EVENTS_QUEUE,
    FILE_UPLOAD_EVENTS_DLQ_QUEUE,
    JOB_EVENTS_QUEUE,
    JOB_EVENTS_DLQ_QUEUE,
    NOTIFICATION_EVENTS_QUEUE,
    NOTIFICATION_EVENTS_DLQ_QUEUE,
    TIMELINE_EVENTS_QUEUE,
    TIMELINE_EVENTS_DLQ_QUEUE,
    # Event Routing Keys
    FILE_UPLOAD_EVENTS_ROUTING_KEY,
    JOB_EVENTS_ROUTING_KEY,
    NOTIFICATION_EVENTS_ROUTING_KEY,
    TIMELINE_EVENTS_ROUTING_KEY,
    # Event Type and Category Constants
    EventCategories,
    EventTypes,
    MessageHeaders,
    RetryConfig,
)
from .confluence_events import ConfluenceContentExtracted
from .job_events import (
    JobActionRequested,
    JobCancelled,
    JobCompleted,
    JobExecutionScheduled,
    JobFailed,
    JobStarted,
)

__all__ = [
    # Base Event System
    "DomainEvent",
    "EventHandler",
    "EventDispatcher",
    "get_event_dispatcher",
    "dispatch_event",
    "dispatch_events",
    # Job Events
    "JobActionRequested",
    "JobExecutionScheduled",
    "JobStarted",
    "JobCompleted",
    "JobFailed",
    "JobCancelled",
    # Confluence Events
    "ConfluenceContentExtracted",
    # Event Constants - Exchanges
    "FILE_UPLOAD_EVENTS_EXCHANGE",
    "FILE_UPLOAD_EVENTS_DLQ_EXCHANGE",
    "JOB_EVENTS_EXCHANGE",
    "JOB_EVENTS_DLQ_EXCHANGE",
    "NOTIFICATION_EVENTS_EXCHANGE",
    "NOTIFICATION_EVENTS_DLQ_EXCHANGE",
    "TIMELINE_EVENTS_EXCHANGE",
    "TIMELINE_EVENTS_DLQ_EXCHANGE",
    # Event Constants - Queues
    "FILE_UPLOAD_EVENTS_QUEUE",
    "FILE_UPLOAD_EVENTS_DLQ_QUEUE",
    "JOB_EVENTS_QUEUE",
    "JOB_EVENTS_DLQ_QUEUE",
    "NOTIFICATION_EVENTS_QUEUE",
    "NOTIFICATION_EVENTS_DLQ_QUEUE",
    "TIMELINE_EVENTS_QUEUE",
    "TIMELINE_EVENTS_DLQ_QUEUE",
    # Event Constants - Routing Keys
    "FILE_UPLOAD_EVENTS_ROUTING_KEY",
    "JOB_EVENTS_ROUTING_KEY",
    "NOTIFICATION_EVENTS_ROUTING_KEY",
    "TIMELINE_EVENTS_ROUTING_KEY",
    # Event Type and Category Constants
    "EventCategories",
    "EventTypes",
    "MessageHeaders",
    "RetryConfig",
]
