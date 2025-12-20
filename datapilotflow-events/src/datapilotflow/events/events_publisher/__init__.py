"""
Event Publisher Services Package.

This package provides RabbitMQ-based event publishing for various event types
in the SkillPilot system, following a base class pattern for common functionality.
"""

from .base_event_publisher import BaseEventPublisher
from .job_event_publisher import JobEventPublisher, get_job_event_publisher
from .notification_event_publisher import NotificationEventPublisher, get_notification_event_publisher
from .file_upload_event_publisher import FileUploadEventPublisher, get_file_upload_event_publisher

__all__ = [
    "BaseEventPublisher",
    "JobEventPublisher",
    "get_job_event_publisher",
    "NotificationEventPublisher",
    "get_notification_event_publisher",
    "FileUploadEventPublisher",
    "get_file_upload_event_publisher"
]
