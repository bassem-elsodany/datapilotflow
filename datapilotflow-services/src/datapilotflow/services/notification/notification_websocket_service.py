"""
Notification WebSocket Service.

This module provides WebSocket management for real-time notification delivery
including connection management, subscription handling, and notification broadcasting.
"""

import asyncio
from typing import Dict, List, Optional, Any
from fastapi import WebSocket
from loguru import logger

from datapilotflow.services.notification.dao.notification_service import NotificationService


class NotificationWebSocketService:
    """Service for managing WebSocket connections and real-time notifications."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationWebSocketService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.notification_service = NotificationService()
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.subscribed_users: set = set()
        self.session_subscribers: Dict[str, set] = {}
        self._initialized = True
    
    async def connect_user(self, username: str, websocket: WebSocket):
        """Connect a user to the WebSocket service."""
        self.active_connections[username] = websocket
        logger.debug(f"User {username} connected to notification WebSocket")
    
    async def disconnect_user(self, username: str):
        """Disconnect a user from the WebSocket service."""
        if username in self.active_connections:
            del self.active_connections[username]
        if username in self.subscribed_users:
            self.subscribed_users.remove(username)
        logger.debug(f"User {username} disconnected from notification WebSocket")
    
    async def subscribe_user(self, username: str):
        """Subscribe a user to general notifications."""
        self.subscribed_users.add(username)
        logger.debug(f"User {username} subscribed to notifications")
    
    async def unsubscribe_user(self, username: str):
        """Unsubscribe a user from general notifications."""
        if username in self.subscribed_users:
            self.subscribed_users.remove(username)
        logger.debug(f"User {username} unsubscribed from notifications")
    
    async def broadcast_notification(self, notification_data: Dict[str, Any]):
        """Broadcast a notification to all subscribed users."""
        message = {
            "type": "notification",
            "action": "new",
            "data": notification_data
        }
        
        for username in self.subscribed_users:
            if username in self.active_connections:
                try:
                    await self.active_connections[username].send_json(message)
                except Exception as e:
                    logger.error(f"Error sending notification to {username}: {e}")
                    await self.disconnect_user(username)
        
        logger.debug(f"Broadcasted notification to {len(self.subscribed_users)} users")
    

    
    async def create_and_broadcast_notification(self, event_payload: Dict[str, Any]):
        """Create a notification and broadcast it to subscribers."""
        try:
            from domain.notification import NotificationCreate, NotificationType, NotificationPriority
            from datetime import datetime, timezone, timedelta
            
            # Extract data from event payload
            user_id = event_payload.get("user_id")
            session_id = event_payload.get("session_id")
            notification_type = event_payload.get("notification_type")
            priority = event_payload.get("priority")
            title = event_payload.get("title")
            message = event_payload.get("message")
            metadata = event_payload.get("metadata", {})
            
            # Set expiration based on event type
            expires_at = None
            if notification_type == NotificationType.SESSION_CREATED:
                expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            elif notification_type == NotificationType.SESSION_DELETED:
                expires_at = datetime.now(timezone.utc) + timedelta(days=3)
            elif notification_type == NotificationType.INTERVIEW_STARTED:
                expires_at = datetime.now(timezone.utc) + timedelta(days=1)
            elif notification_type in [NotificationType.RESUME_ANALYSIS_COMPLETED, NotificationType.JOB_ANALYSIS_COMPLETED]:
                expires_at = datetime.now(timezone.utc) + timedelta(days=5)
            elif notification_type in [NotificationType.JOB_DELETED, NotificationType.RESUME_DELETED]:
                expires_at = datetime.now(timezone.utc) + timedelta(days=3)
            elif notification_type == NotificationType.ERROR:
                expires_at = datetime.now(timezone.utc) + timedelta(days=1)
            else:
                expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            
            # Create notification data
            notification_data = NotificationCreate(
                user_id=user_id,
                session_id=session_id,
                type=notification_type,
                priority=priority,
                title=title,
                message=message,
                metadata=metadata,
                expires_at=expires_at
            )
            
            # Create notification in MongoDB
            notification_id = self.notification_service.create_notification(notification_data)
            if notification_id:
                # Add notification ID to the payload for broadcasting
                broadcast_data = {
                    "id": notification_id,
                    "user_id": user_id,
                    "session_id": session_id,
                    "type": notification_type,
                    "priority": priority,
                    "title": title,
                    "message": message,
                    "metadata": metadata,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await self.broadcast_notification(broadcast_data)
                return notification_id
            return None
        except Exception as e:
            logger.error(f"Error creating and broadcasting notification: {e}")
            return None
