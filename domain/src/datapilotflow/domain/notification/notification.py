from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """Types of notifications"""
    JOB_UPLOAD_PROGRESS = "job_upload_progress"
    RESUME_UPLOAD_PROGRESS = "resume_upload_progress"
    ANALYSIS_PROGRESS = "analysis_progress"
    SESSION_CREATED = "session_created"
    SESSION_DELETED = "session_deleted"
    SESSION_UPDATED = "session_updated"
    INTERVIEW_STARTED = "interview_started"
    RESUME_ANALYSIS_COMPLETED = "resume_analysis_completed"
    JOB_ANALYSIS_COMPLETED = "job_analysis_completed"
    JOB_DELETED = "job_deleted"
    RESUME_DELETED = "resume_deleted"

    # Knowledge Job Processing Notifications
    KNOWLEDGE_JOB_STARTED = "knowledge_job_started"
    KNOWLEDGE_JOB_PROGRESS = "knowledge_job_progress"
    KNOWLEDGE_JOB_COMPLETED = "knowledge_job_completed"
    KNOWLEDGE_JOB_FAILED = "knowledge_job_failed"
    KNOWLEDGE_JOB_CANCELLED = "knowledge_job_cancelled"

    ERROR = "error"
    SUCCESS = "success"
    INFO = "info"


class NotificationStatus(str, Enum):
    """Status of notifications"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationPriority(str, Enum):
    """Priority levels for notifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification(BaseModel):
    """Notification model for in-transit notifications"""
    notification_id: str = Field(..., description="Unique identifier for the notification")
    user_id: str = Field(..., description="User ID who owns this notification")
    session_id: Optional[str] = Field(None, description="Associated session ID if applicable")
    type: NotificationType = Field(..., description="Type of notification")
    status: NotificationStatus = Field(default=NotificationStatus.PENDING, description="Current status")
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM, description="Priority level")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    progress: Optional[float] = Field(None, ge=0, le=100, description="Progress percentage (0-100)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(None, description="Expiration time for the notification")
    read_at: Optional[datetime] = Field(None, description="When the notification was read")
    dismissed_at: Optional[datetime] = Field(None, description="When the notification was dismissed")


class NotificationCreate(BaseModel):
    """Model for creating a new notification"""
    user_id: str
    session_id: Optional[str] = None
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    title: str
    message: str
    progress: Optional[float] = None
    metadata: Dict[str, Any] = {}
    expires_at: Optional[datetime] = None


class NotificationUpdate(BaseModel):
    """Model for updating a notification"""
    status: Optional[NotificationStatus] = None
    title: Optional[str] = None
    message: Optional[str] = None
    progress: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class NotificationResponse(BaseModel):
    """Response model for notifications"""
    notification_id: str
    user_id: str
    session_id: Optional[str]
    type: NotificationType
    status: NotificationStatus
    priority: NotificationPriority
    title: str
    message: str
    progress: Optional[float]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    read_at: Optional[datetime]
    dismissed_at: Optional[datetime]


class NotificationListResponse(BaseModel):
    """Response model for list of notifications"""
    notifications: List[NotificationResponse]
    total_count: int
    unread_count: int


class NotificationStats(BaseModel):
    """Statistics for notifications"""
    total_count: int
    unread_count: int
    pending_count: int
    in_progress_count: int
    completed_count: int
    failed_count: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
