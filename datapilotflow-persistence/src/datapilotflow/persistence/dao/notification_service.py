from loguru import logger
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from bson import ObjectId

from src.domain.notification import (
    Notification, NotificationCreate, NotificationUpdate, 
    NotificationResponse, NotificationListResponse, NotificationStats,
    NotificationStatus, NotificationType, NotificationPriority
)
from src.infrastructure.mongo.client import MongoClientWrapper


class NotificationService(MongoClientWrapper[Notification]):
    """Service for managing notifications in MongoDB"""
    
    def __init__(self):
        super().__init__(
            model=Notification,
            collection_name="notifications"
        )
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure proper indexes exist for notifications"""
        try:
            # Index for user_id and created_at for efficient queries
            self.collection.create_index([("user_id", 1), ("created_at", -1)])
            
            # Index for session_id for session-related notifications
            self.collection.create_index([("session_id", 1)])
            
            # Index for status and type for filtering
            self.collection.create_index([("status", 1), ("type", 1)])
            
            # Index for expires_at for cleanup operations
            self.collection.create_index([("expires_at", 1)])
            
            # Index for read_at and dismissed_at for unread counts
            self.collection.create_index([("read_at", 1), ("dismissed_at", 1)])
            
            logger.info("Notification indexes ensured")
        except Exception as e:
            logger.error(f"Error creating notification indexes: {e}")
    
    def create_notification(self, notification_data: NotificationCreate) -> Optional[str]:
        """Create a new notification"""
        try:
            notification = Notification(
                notification_id=str(ObjectId()),
                user_id=notification_data.user_id,
                session_id=notification_data.session_id,
                type=notification_data.type,
                priority=notification_data.priority,
                title=notification_data.title,
                message=notification_data.message,
                progress=notification_data.progress,
                metadata=notification_data.metadata,
                expires_at=notification_data.expires_at
            )
            
            doc = notification.model_dump()
            result = self.collection.insert_one(doc)
            
            if result.inserted_id:
                logger.info(f"Created notification {notification.notification_id} for user {notification_data.user_id}")
                return notification.notification_id
            return None
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None
    
    def get_notification(self, notification_id: str) -> Optional[NotificationResponse]:
        """Get a notification by ID"""
        try:
            doc = self.collection.find_one({"notification_id": notification_id})
            if doc:
                return NotificationResponse.model_validate(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting notification {notification_id}: {e}")
            return None
    
    def get_user_notifications(
        self, 
        user_id: str, 
        limit: int = 50, 
        skip: int = 0,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[NotificationType] = None,
        include_read: bool = True,
        include_dismissed: bool = False
    ) -> NotificationListResponse:
        """Get notifications for a user with filtering options"""
        try:
            # Build query
            query = {"user_id": user_id}
            
            if status:
                query["status"] = status.value
            
            if notification_type:
                query["type"] = notification_type.value
            
            if not include_read:
                query["read_at"] = None
            
            if not include_dismissed:
                query["dismissed_at"] = None
            
            # Get notifications
            cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            notifications = [NotificationResponse.model_validate(doc) for doc in cursor]
            
            # Get counts
            total_count = self.collection.count_documents(query)
            unread_query = {**query, "read_at": None, "dismissed_at": None}
            unread_count = self.collection.count_documents(unread_query)
            
            return NotificationListResponse(
                notifications=notifications,
                total_count=total_count,
                unread_count=unread_count
            )
            
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {e}")
            return NotificationListResponse(notifications=[], total_count=0, unread_count=0)
    
    def get_session_notifications(self, session_id: str) -> List[NotificationResponse]:
        """Get all notifications for a specific session"""
        try:
            cursor = self.collection.find({"session_id": session_id}).sort("created_at", -1)
            return [NotificationResponse.model_validate(doc) for doc in cursor]
        except Exception as e:
            logger.error(f"Error getting notifications for session {session_id}: {e}")
            return []
    
    def update_notification(self, notification_id: str, update_data: NotificationUpdate) -> bool:
        """Update a notification"""
        try:
            update_fields = {}
            
            if update_data.status is not None:
                update_fields["status"] = update_data.status.value
            
            if update_data.title is not None:
                update_fields["title"] = update_data.title
            
            if update_data.message is not None:
                update_fields["message"] = update_data.message
            
            if update_data.progress is not None:
                update_fields["progress"] = update_data.progress
            
            if update_data.metadata is not None:
                update_fields["metadata"] = update_data.metadata
            
            if update_data.expires_at is not None:
                update_fields["expires_at"] = update_data.expires_at
            
            # Always update the updated_at field
            update_fields["updated_at"] = datetime.now(timezone.utc)
            
            if not update_fields:
                return False
            
            result = self.collection.update_one(
                {"notification_id": notification_id},
                {"$set": update_fields}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated notification {notification_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating notification {notification_id}: {e}")
            return False
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        try:
            result = self.collection.update_one(
                {"notification_id": notification_id},
                {"$set": {"read_at": datetime.now(timezone.utc)}}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Marked notification {notification_id} as read")
            
            return success
            
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {e}")
            return False
    
    def mark_as_dismissed(self, notification_id: str) -> bool:
        """Mark a notification as dismissed"""
        try:
            result = self.collection.update_one(
                {"notification_id": notification_id},
                {"$set": {"dismissed_at": datetime.now(timezone.utc)}}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Marked notification {notification_id} as dismissed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as dismissed: {e}")
            return False
    
    def mark_all_as_read(self, user_id: str) -> bool:
        """Mark all notifications for a user as read"""
        try:
            result = self.collection.update_many(
                {"user_id": user_id, "read_at": None},
                {"$set": {"read_at": datetime.now(timezone.utc)}}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Marked {result.modified_count} notifications as read for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error marking notifications as read for user {user_id}: {e}")
            return False
    
    def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification"""
        try:
            result = self.collection.delete_one({"notification_id": notification_id})
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted notification {notification_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting notification {notification_id}: {e}")
            return False
    
    def delete_expired_notifications(self) -> int:
        """Delete notifications that have expired"""
        try:
            result = self.collection.delete_many({
                "expires_at": {"$lt": datetime.now(timezone.utc)}
            })
            
            deleted_count = result.deleted_count
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} expired notifications")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting expired notifications: {e}")
            return 0
    
    def get_notification_stats(self, user_id: str) -> NotificationStats:
        """Get notification statistics for a user"""
        try:
            # Base query for user
            base_query = {"user_id": user_id}
            
            # Total count
            total_count = self.collection.count_documents(base_query)
            
            # Unread count
            unread_count = self.collection.count_documents({
                **base_query,
                "read_at": None,
                "dismissed_at": None
            })
            
            # Status counts
            pending_count = self.collection.count_documents({
                **base_query,
                "status": NotificationStatus.PENDING.value
            })
            
            in_progress_count = self.collection.count_documents({
                **base_query,
                "status": NotificationStatus.IN_PROGRESS.value
            })
            
            completed_count = self.collection.count_documents({
                **base_query,
                "status": NotificationStatus.COMPLETED.value
            })
            
            failed_count = self.collection.count_documents({
                **base_query,
                "status": NotificationStatus.FAILED.value
            })
            
            # Type counts
            type_pipeline = [
                {"$match": base_query},
                {"$group": {"_id": "$type", "count": {"$sum": 1}}}
            ]
            type_counts = {}
            for doc in self.collection.aggregate(type_pipeline):
                type_counts[doc["_id"]] = doc["count"]
            
            # Priority counts
            priority_pipeline = [
                {"$match": base_query},
                {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
            ]
            priority_counts = {}
            for doc in self.collection.aggregate(priority_pipeline):
                priority_counts[doc["_id"]] = doc["count"]
            
            return NotificationStats(
                total_count=total_count,
                unread_count=unread_count,
                pending_count=pending_count,
                in_progress_count=in_progress_count,
                completed_count=completed_count,
                failed_count=failed_count,
                by_type=type_counts,
                by_priority=priority_counts
            )
            
        except Exception as e:
            logger.error(f"Error getting notification stats for user {user_id}: {e}")
            return NotificationStats(
                total_count=0,
                unread_count=0,
                pending_count=0,
                in_progress_count=0,
                completed_count=0,
                failed_count=0,
                by_type={},
                by_priority={}
            )
    
    def create_progress_notification(
        self, 
        user_id: str, 
        session_id: str, 
        notification_type: NotificationType,
        title: str,
        message: str,
        progress: float = 0.0
    ) -> Optional[str]:
        """Create a progress notification for uploads/analysis"""
        try:
            notification_data = NotificationCreate(
                user_id=user_id,
                session_id=session_id,
                type=notification_type,
                priority=NotificationPriority.MEDIUM,
                title=title,
                message=message,
                progress=progress,
                metadata={"session_id": session_id}
            )
            
            return self.create_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Error creating progress notification: {e}")
            return None
    
    def update_progress(self, notification_id: str, progress: float, message: Optional[str] = None) -> bool:
        """Update progress for a notification"""
        try:
            update_data = NotificationUpdate(progress=progress)
            if message:
                update_data.message = message
            
            if progress >= 100:
                update_data.status = NotificationStatus.COMPLETED
            
            return self.update_notification(notification_id, update_data)
            
        except Exception as e:
            logger.error(f"Error updating progress for notification {notification_id}: {e}")
            return False
