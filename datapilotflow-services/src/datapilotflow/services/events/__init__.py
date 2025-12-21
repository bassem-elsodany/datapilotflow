"""
Events Package.

This package contains event publishers and utilities.
Event constants are now centralized in datapilotflow.domain.events.
"""

from datapilotflow.domain.events import (
    # Job Events
    JOB_EVENTS_EXCHANGE,
    JOB_EVENTS_QUEUE,
    JOB_EVENTS_ROUTING_KEY,
    JOB_EVENTS_DLQ_EXCHANGE,
    JOB_EVENTS_DLQ_QUEUE,

    # File Upload Events
    FILE_UPLOAD_EVENTS_EXCHANGE,
    FILE_UPLOAD_EVENTS_QUEUE,
    FILE_UPLOAD_EVENTS_ROUTING_KEY,
    FILE_UPLOAD_EVENTS_DLQ_EXCHANGE,
    FILE_UPLOAD_EVENTS_DLQ_QUEUE,

    # Notification Events
    NOTIFICATION_EVENTS_EXCHANGE,
    NOTIFICATION_EVENTS_QUEUE,
    NOTIFICATION_EVENTS_ROUTING_KEY,
    NOTIFICATION_EVENTS_DLQ_EXCHANGE,
    NOTIFICATION_EVENTS_DLQ_QUEUE,

    # Timeline Events
    TIMELINE_EVENTS_EXCHANGE,
    TIMELINE_EVENTS_QUEUE,
    TIMELINE_EVENTS_ROUTING_KEY,
    TIMELINE_EVENTS_DLQ_EXCHANGE,
    TIMELINE_EVENTS_DLQ_QUEUE,

    # Event Types and Categories
    EventTypes,
    EventCategories,
    RetryConfig,
    MessageHeaders
)

__all__ = [
    # Job Events
    "JOB_EVENTS_EXCHANGE",
    "JOB_EVENTS_QUEUE", 
    "JOB_EVENTS_ROUTING_KEY",
    "JOB_EVENTS_DLQ_EXCHANGE",
    "JOB_EVENTS_DLQ_QUEUE",
    
    # File Upload Events
    "FILE_UPLOAD_EVENTS_EXCHANGE",
    "FILE_UPLOAD_EVENTS_QUEUE",
    "FILE_UPLOAD_EVENTS_ROUTING_KEY", 
    "FILE_UPLOAD_EVENTS_DLQ_EXCHANGE",
    "FILE_UPLOAD_EVENTS_DLQ_QUEUE",
    
    # Notification Events
    "NOTIFICATION_EVENTS_EXCHANGE",
    "NOTIFICATION_EVENTS_QUEUE",
    "NOTIFICATION_EVENTS_ROUTING_KEY",
    "NOTIFICATION_EVENTS_DLQ_EXCHANGE", 
    "NOTIFICATION_EVENTS_DLQ_QUEUE",
    
    # Timeline Events
    "TIMELINE_EVENTS_EXCHANGE",
    "TIMELINE_EVENTS_QUEUE",
    "TIMELINE_EVENTS_ROUTING_KEY",
    "TIMELINE_EVENTS_DLQ_EXCHANGE",
    "TIMELINE_EVENTS_DLQ_QUEUE",
    
    # Event Types and Categories
    "EventTypes",
    "EventCategories",
    "RetryConfig",
    "MessageHeaders"
]
