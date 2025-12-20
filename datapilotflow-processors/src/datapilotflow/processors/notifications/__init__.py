"""
Notification Processing Package.

This package contains processors for handling notification events,
including notification creation, updates, and delivery operations.
"""

from .notification_processor import NotificationEventProcessor, get_notification_event_processor

__all__ = [
    "NotificationEventProcessor",
    "get_notification_event_processor",
]
