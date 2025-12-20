"""
Event Listener Services Package.

This package provides RabbitMQ-based event listening for various event types
in the SkillPilot system, following a base class pattern for common functionality.
"""

# Processors import commented out - they belong in backend/processors
# TODO: Extract processors to separate package when needed
# from datapilotflow.processors.file_upload.file_upload_processor import (
#     FileUploadEventProcessor,
#     get_file_upload_event_processor,
# )
# from datapilotflow.processors.notifications.notification_processor import (
#     NotificationEventProcessor,
#     get_notification_event_processor,
# )

from .base_event_listener import BaseEventListener
from .file_upload_event_listener import (
    FileUploadEventListener,
    get_file_upload_event_listener,
    start_file_upload_event_listener,
)
from .job_event_listener import (
    JobEventListener,
    get_job_event_listener,
    start_job_event_listener,
)
from .notification_event_listener import (
    NotificationEventListener,
    get_notification_event_listener,
    start_notification_event_listener,
)

__all__ = [
    "BaseEventListener",
    "JobEventListener",
    "get_job_event_listener",
    "start_job_event_listener",
    "NotificationEventListener",
    "get_notification_event_listener",
    "start_notification_event_listener",
    "FileUploadEventListener",
    "get_file_upload_event_listener",
    "start_file_upload_event_listener",
    # Processors - commented out until extracted
    # "FileUploadEventProcessor",
    # "get_file_upload_event_processor",
    # "NotificationEventProcessor",
    # "get_notification_event_processor",
]
