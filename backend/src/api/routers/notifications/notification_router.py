import logging
import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from src.domain.notification.notification import (
    NotificationCreate, NotificationUpdate, NotificationResponse, 
    NotificationListResponse, NotificationStats, NotificationType, 
    NotificationStatus, NotificationPriority
)
from src.services.notification.dao.notification_service import NotificationService
from src.api.routers.auth.auth_router import get_current_user
from src.domain.user import User


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("", response_model=dict)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new notification"""
    try:
        # Ensure the notification is created for the current user
        notification_data.user_id = current_user.username
        
        service = NotificationService()
        notification_id = service.create_notification(notification_data)
        
        if notification_id:
            return {
                "success": True,
                "notification_id": notification_id,
                "message": "Notification created successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create notification"
            )
            
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    status: Optional[NotificationStatus] = Query(None),
    notification_type: Optional[NotificationType] = Query(None),
    include_read: bool = Query(True),
    include_dismissed: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for the current user"""
    try:
        service = NotificationService()
        result = service.get_user_notifications(
            user_id=current_user.username,
            limit=limit,
            skip=skip,
            status=status,
            notification_type=notification_type,
            include_read=include_read,
            include_dismissed=include_dismissed
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific notification by ID"""
    try:
        service = NotificationService()
        notification = service.get_notification(notification_id)
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Ensure the notification belongs to the current user
        if notification.user_id != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification {notification_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{notification_id}", response_model=dict)
async def update_notification(
    notification_id: str,
    update_data: NotificationUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a notification"""
    try:
        service = NotificationService()
        
        # First check if the notification exists and belongs to the user
        notification = service.get_notification(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        if notification.user_id != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        success = service.update_notification(notification_id, update_data)
        
        if success:
            return {
                "success": True,
                "message": "Notification updated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update notification"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification {notification_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{notification_id}/read", response_model=dict)
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read"""
    try:
        service = NotificationService()
        
        # First check if the notification exists and belongs to the user
        notification = service.get_notification(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        if notification.user_id != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        success = service.mark_as_read(notification_id)
        
        if success:
            return {
                "success": True,
                "message": "Notification marked as read"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to mark notification as read"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{notification_id}/dismiss", response_model=dict)
async def dismiss_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Dismiss a notification"""
    try:
        service = NotificationService()
        
        # First check if the notification exists and belongs to the user
        notification = service.get_notification(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        if notification.user_id != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        success = service.mark_as_dismissed(notification_id)
        
        if success:
            return {
                "success": True,
                "message": "Notification dismissed"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to dismiss notification"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing notification {notification_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/read-all", response_model=dict)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications for the current user as read"""
    try:
        service = NotificationService()
        success = service.mark_all_as_read(current_user.username)
        
        if success:
            return {
                "success": True,
                "message": "All notifications marked as read"
            }
        else:
            return {
                "success": True,
                "message": "No notifications to mark as read"
            }
            
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{notification_id}", response_model=dict)
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a notification"""
    try:
        service = NotificationService()
        
        # First check if the notification exists and belongs to the user
        notification = service.get_notification(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        if notification.user_id != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        success = service.delete_notification(notification_id)
        
        if success:
            return {
                "success": True,
                "message": "Notification deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete notification"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification {notification_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/session/{session_id}/notifications", response_model=List[NotificationResponse])
async def get_session_notifications(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all notifications for a specific session"""
    try:
        service = NotificationService()
        notifications = service.get_session_notifications(session_id)
        
        # Filter notifications to only show those belonging to the current user
        user_notifications = [
            notification for notification in notifications 
            if notification.user_id == current_user.username
        ]
        
        return user_notifications
        
    except Exception as e:
        logger.error(f"Error getting session notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/stats/summary", response_model=NotificationStats)
async def get_notification_stats(
    current_user: User = Depends(get_current_user)
):
    """Get notification statistics for the current user"""
    try:
        service = NotificationService()
        stats = service.get_notification_stats(current_user.username)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/progress", response_model=dict)
async def create_progress_notification(
    session_id: str,
    notification_type: NotificationType,
    title: str,
    message: str,
    progress: float = Query(0.0, ge=0.0, le=100.0),
    current_user: User = Depends(get_current_user)
):
    """Create a progress notification for uploads/analysis"""
    try:
        service = NotificationService()
        notification_id = service.create_progress_notification(
            user_id=current_user.username,
            session_id=session_id,
            notification_type=notification_type,
            title=title,
            message=message,
            progress=progress
        )
        
        if notification_id:
            return {
                "success": True,
                "notification_id": notification_id,
                "message": "Progress notification created successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create progress notification"
            )
            
    except Exception as e:
        logger.error(f"Error creating progress notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/progress/{notification_id}", response_model=dict)
async def update_progress(
    notification_id: str,
    progress: float = Query(..., ge=0.0, le=100.0),
    message: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Update progress for a notification"""
    try:
        service = NotificationService()
        
        # First check if the notification exists and belongs to the user
        notification = service.get_notification(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        if notification.user_id != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        success = service.update_progress(notification_id, progress, message)
        
        if success:
            return {
                "success": True,
                "message": "Progress updated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update progress"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating progress for notification {notification_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/broadcast", response_model=dict)
async def broadcast_notification(
    notification_data: dict
):
    """Internal endpoint to broadcast a notification to WebSocket subscribers."""
    try:
        from services.notification.notification_websocket_service import NotificationWebSocketService
        
        websocket_service = NotificationWebSocketService()
        await websocket_service.broadcast_notification(notification_data)
        
        return {
            "success": True,
            "message": "Notification broadcasted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/cleanup/expired", response_model=dict)
async def cleanup_expired_notifications(
    current_user: User = Depends(get_current_user)
):
    """Clean up expired notifications (admin function)"""
    try:
        # TODO: Add admin role check here
        service = NotificationService()
        deleted_count = service.delete_expired_notifications()
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Cleaned up {deleted_count} expired notifications"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up expired notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



