"""
Notification Event Listener.

This module provides specific functionality for listening to notification-related events
from RabbitMQ, extending the base event listener.
"""

import asyncio
from typing import Dict, Any
from loguru import logger
from datapilotflow.services.events import (
    NOTIFICATION_EVENTS_EXCHANGE,
    NOTIFICATION_EVENTS_QUEUE,
    NOTIFICATION_EVENTS_ROUTING_KEY,
    NOTIFICATION_EVENTS_DLQ_EXCHANGE,
    NOTIFICATION_EVENTS_DLQ_QUEUE,
    EventTypes
)
from datapilotflow.processors.notifications.notification_processor import get_notification_event_processor
from .base_event_listener import BaseEventListener


class NotificationEventListener(BaseEventListener):
    """Event listener for notification-related events."""
    
    def __init__(self):
        """Initialize the notification event listener with notification-specific configuration."""
        super().__init__(
            exchange_name=NOTIFICATION_EVENTS_EXCHANGE,
            queue_name=NOTIFICATION_EVENTS_QUEUE,
            routing_key=NOTIFICATION_EVENTS_ROUTING_KEY,
            dlq_exchange_name=NOTIFICATION_EVENTS_DLQ_EXCHANGE,
            dlq_queue_name=NOTIFICATION_EVENTS_DLQ_QUEUE
        )
        self.notification_processor = get_notification_event_processor()
    
    async def handle_event(self, event_payload: Dict[str, Any]) -> bool:
        """
        Handle a notification event.
        
        Args:
            event_payload: The notification event data to process
            
        Returns:
            True if event was processed successfully, False otherwise
        """
        try:
            # Extract event information
            event_type = event_payload.get("event_type")
            user_id = event_payload.get("user_id")
            notification_type = event_payload.get("notification_type")
            
            logger.info(f"Handling notification event: {event_type} for user {user_id}")

            # Handle different event types
            if event_type in ["notification_created", "notification_updated", "notification_deleted"]:
                return await self.notification_processor.process_notification_event(event_payload)
            elif event_type == "knowledge_job_notification":
                # Handle knowledge job notifications (started, progress, completed, failed, cancelled)
                logger.debug(f"Processing knowledge job notification: type={notification_type}, user={user_id}")
                return await self.notification_processor.process_notification_event(event_payload)
            else:
                logger.warning(f"Unknown notification event type: {event_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling notification event: {e}")
            return False
    


# Global instance for easy access
_notification_event_listener: NotificationEventListener = None


def get_notification_event_listener() -> NotificationEventListener:
    """Get the global notification event listener instance."""
    global _notification_event_listener
    
    if _notification_event_listener is None:
        _notification_event_listener = NotificationEventListener()
    
    return _notification_event_listener


async def start_notification_event_listener() -> None:
    """
    Convenience function to start the notification event listener.
    """
    listener = get_notification_event_listener()
    await listener.start_listening()
