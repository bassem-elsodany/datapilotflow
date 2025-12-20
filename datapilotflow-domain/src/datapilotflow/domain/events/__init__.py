"""
Events domain models.

This subpackage contains all event-related domain models for
managing domain events, event handlers, and event dispatching.
"""

from .base import (
    DomainEvent,
    EventDispatcher,
    EventHandler,
    dispatch_event,
    dispatch_events,
    get_event_dispatcher,
)
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
]
