"""
Notification Event Publisher.

This module provides specific functionality for publishing notification-related events
to RabbitMQ, extending the base event publisher.
"""

from typing import Dict, Any
from loguru import logger
from src.services.events import (
    NOTIFICATION_EVENTS_EXCHANGE,
    NOTIFICATION_EVENTS_QUEUE,
    NOTIFICATION_EVENTS_ROUTING_KEY,
    NOTIFICATION_EVENTS_DLQ_EXCHANGE,
    NOTIFICATION_EVENTS_DLQ_QUEUE,
    EventTypes,
    EventCategories
)
from .base_event_publisher import BaseEventPublisher


class NotificationEventPublisher(BaseEventPublisher):
    """Event publisher for notification-related events."""
    
    def __init__(self):
        """Initialize the notification event publisher with notification-specific configuration."""
        super().__init__(
            exchange_name=NOTIFICATION_EVENTS_EXCHANGE,
            queue_name=NOTIFICATION_EVENTS_QUEUE,
            routing_key=NOTIFICATION_EVENTS_ROUTING_KEY,
            dlq_exchange_name=NOTIFICATION_EVENTS_DLQ_EXCHANGE,
            dlq_queue_name=NOTIFICATION_EVENTS_DLQ_QUEUE
        )
    
    async def publish_specific_event(self, event_data: Dict[str, Any]) -> None:
        """
        Publish a notification event.
        
        Args:
            event_data: The notification event data to publish
        """
        try:
            # Add notification-specific headers
            headers = {
                "user_id": event_data.get("user_id", "unknown"),
                "notification_type": event_data.get("notification_type", "unknown"),
                "event_category": EventCategories.NOTIFICATION
            }
            
            # Publish using base class method
            await self.publish_event(event_data, headers)
            
            logger.info(f"Notification event published successfully: {event_data.get('event_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to publish notification event: {e}")
            logger.error(f"Event ID: {event_data.get('event_id', 'unknown')}")
            raise
    
    async def publish_notification_event(self, event_data: Dict[str, Any]) -> None:
        """
        Convenience method to publish a notification event.
        
        Args:
            event_data: The notification event data to publish
        """
        await self.publish_specific_event(event_data)


# Global instance for easy access
_notification_event_publisher: NotificationEventPublisher = None


def get_notification_event_publisher() -> NotificationEventPublisher:
    """Get the global notification event publisher instance."""
    global _notification_event_publisher
    
    if _notification_event_publisher is None:
        _notification_event_publisher = NotificationEventPublisher()
    
    return _notification_event_publisher
