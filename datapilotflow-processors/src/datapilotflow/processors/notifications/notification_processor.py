"""
Notification Event Processor.

This module contains the actual processing logic for notification-related events,
separated from the event listening infrastructure.
"""

import asyncio
from typing import Dict, Any, Optional
from loguru import logger


class NotificationEventProcessor:
    """Processor for notification-related events."""
    
    def __init__(self):
        """Initialize the notification event processor."""
        logger.info("NotificationEventProcessor initialized")
    
    async def process_notification_event(self, event_payload: Dict[str, Any]) -> bool:
        """
        Process a notification event by creating notification in DB and broadcasting via WebSocket.

        Args:
            event_payload: The notification event data

        Returns:
            True if event was processed successfully, False otherwise
        """
        try:
            event_type = event_payload.get('event_type')
            user_id = event_payload.get('user_id')
            notification_type = event_payload.get('notification_type')

            logger.info(f"Processing notification event: {event_type} for user {user_id}")

            # Use existing notification listener service to process the event
            # This creates notification in MongoDB and broadcasts via WebSocket
            from datapilotflow.services.notification.notification_listener_service import (
                process_notification_event
            )

            success = await process_notification_event(event_payload)

            if success:
                logger.info(f"Notification processed and broadcasted successfully: {notification_type}")
            else:
                logger.error(f"Failed to process notification: {notification_type}")

            return success

        except Exception as e:
            logger.error(f"Error processing notification event: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False


# Global instance for easy access
_notification_event_processor: Optional[NotificationEventProcessor] = None


def get_notification_event_processor() -> NotificationEventProcessor:
    """Get the global notification event processor instance."""
    global _notification_event_processor
    
    if _notification_event_processor is None:
        _notification_event_processor = NotificationEventProcessor()
    
    return _notification_event_processor
