"""
Event System Constants.

This module contains all shared constants for the event-driven architecture,
including exchange names, queue names, routing keys, and other configuration
that must be consistent between publishers and listeners across the DataPilotFlow system.
"""

# ============================================================================
# JOB EVENTS CONFIGURATION
# ============================================================================
JOB_EVENTS_EXCHANGE = "job_events_exchange"
JOB_EVENTS_QUEUE = "knowledge_job_action_requested_queue"
JOB_EVENTS_ROUTING_KEY = "knowledge.job.action.requested"
JOB_EVENTS_DLQ_EXCHANGE = "job_events_dlq_exchange"
JOB_EVENTS_DLQ_QUEUE = "job_events_dlq_queue"

# ============================================================================
# FILE UPLOAD EVENTS CONFIGURATION
# ============================================================================
FILE_UPLOAD_EVENTS_EXCHANGE = "rag_file_upload_exchange"
FILE_UPLOAD_EVENTS_QUEUE = "rag_file_upload_queue"
FILE_UPLOAD_EVENTS_ROUTING_KEY = "rag_file_upload_routing_key"
FILE_UPLOAD_EVENTS_DLQ_EXCHANGE = "rag_file_upload_dlq_exchange"
FILE_UPLOAD_EVENTS_DLQ_QUEUE = "rag_file_upload_dlq_queue"

# ============================================================================
# NOTIFICATION EVENTS CONFIGURATION
# ============================================================================
NOTIFICATION_EVENTS_EXCHANGE = "notification_events_exchange"
NOTIFICATION_EVENTS_QUEUE = "notification_queue"
NOTIFICATION_EVENTS_ROUTING_KEY = "notification.new"
NOTIFICATION_EVENTS_DLQ_EXCHANGE = "notification_events_dlq_exchange"
NOTIFICATION_EVENTS_DLQ_QUEUE = "notification_dlq_queue"

# ============================================================================
# TIMELINE EVENTS CONFIGURATION
# ============================================================================
TIMELINE_EVENTS_EXCHANGE = "timeline_events_exchange"
TIMELINE_EVENTS_QUEUE = "timeline_events_queue"
TIMELINE_EVENTS_ROUTING_KEY = "timeline.*"
TIMELINE_EVENTS_DLQ_EXCHANGE = "timeline_events_dlq_exchange"
TIMELINE_EVENTS_DLQ_QUEUE = "timeline_events_dlq_queue"


# ============================================================================
# EVENT TYPES
# ============================================================================
class EventTypes:
    """Constants for event type strings."""

    KNOWLEDGE_JOB_ACTION_REQUESTED = "knowledge_job_action_requested"
    FILE_UPLOAD = "file_upload"
    NEW_NOTIFICATION = "NewNotification"
    TIMELINE_BATCH_PROGRESS_UPDATED = "timeline_batch_progress_updated"
    TIMELINE_STATUS_CHANGED = "timeline_status_changed"


# ============================================================================
# EVENT CATEGORIES
# ============================================================================
class EventCategories:
    """Constants for event categories."""

    JOB = "job"
    FILE_UPLOAD = "file_upload"
    NOTIFICATION = "notification"


# ============================================================================
# RETRY CONFIGURATION
# ============================================================================
class RetryConfig:
    """Constants for retry configuration."""

    MAX_RETRIES = 3
    DEFAULT_RETRY_COUNT = 0


# ============================================================================
# MESSAGE HEADERS
# ============================================================================
class MessageHeaders:
    """Constants for message headers."""

    FILE_ID = "file_id"
    USER_ID = "user_id"
    EVENT_CATEGORY = "event_category"
    RETRY_COUNT = "x-retry-count"
