"""
Event Listener Services Package.

This package provides RabbitMQ-based event listening for various event types
in the SkillPilot system, following a base class pattern for common functionality.
"""

from datapilotflow.processors.file_upload.file_upload_processor import (
    FileUploadEventProcessor,
    get_file_upload_event_processor,
)

# Old knowledge job processors commented out to avoid circular imports
# They are deprecated - new architecture uses RefactoredKnowledgeJobEventProcessor
# from datapilotflow.processors.knowledge_job.knowledge_job_event_processor import (
#     KnowledgeJobEventProcessor,
#     get_knowledge_job_event_processor,
# )
# from datapilotflow.processors.knowledge_job.knowledge_job_processor import (
#     KnowledgeJobProcessor,
#     get_knowledge_job_processor,
# )

from datapilotflow.processors.notifications.notification_processor import (
    NotificationEventProcessor,
    get_notification_event_processor,
)

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
    # Processors
    # Old knowledge job processors deprecated (commented out to avoid circular imports)
    # "KnowledgeJobEventProcessor",
    # "get_knowledge_job_event_processor",
    # "KnowledgeJobProcessor",
    # "get_knowledge_job_processor",
    "FileUploadEventProcessor",
    "get_file_upload_event_processor",
    "NotificationEventProcessor",
    "get_notification_event_processor",
]
