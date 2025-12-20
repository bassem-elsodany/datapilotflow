"""
File Upload Event Publisher.

This module provides specific functionality for publishing file upload-related events
to RabbitMQ, extending the base event publisher.
"""

from typing import Dict, Any
from loguru import logger
from datapilotflow.services.events import (
    FILE_UPLOAD_EVENTS_EXCHANGE,
    FILE_UPLOAD_EVENTS_QUEUE,
    FILE_UPLOAD_EVENTS_ROUTING_KEY,
    FILE_UPLOAD_EVENTS_DLQ_EXCHANGE,
    FILE_UPLOAD_EVENTS_DLQ_QUEUE,
    EventTypes,
    EventCategories
)
from .base_event_publisher import BaseEventPublisher


class FileUploadEventPublisher(BaseEventPublisher):
    """Event publisher for file upload-related events."""
    
    def __init__(self):
        """Initialize the file upload event publisher with file upload-specific configuration."""
        super().__init__(
            exchange_name=FILE_UPLOAD_EVENTS_EXCHANGE,
            queue_name=FILE_UPLOAD_EVENTS_QUEUE,
            routing_key=FILE_UPLOAD_EVENTS_ROUTING_KEY,
            dlq_exchange_name=FILE_UPLOAD_EVENTS_DLQ_EXCHANGE,
            dlq_queue_name=FILE_UPLOAD_EVENTS_DLQ_QUEUE
        )
    
    async def publish_specific_event(self, event_data: Dict[str, Any]) -> None:
        """
        Publish a file upload event.
        
        Args:
            event_data: The file upload event data to publish
        """
        try:
            # Add file upload-specific headers
            headers = {
                "file_id": event_data.get("file_id", "unknown"),
                "user_id": event_data.get("user_id", "unknown"),
                "event_category": EventCategories.FILE_UPLOAD
            }
            
            # Publish using base class method
            await self.publish_event(event_data, headers)
            
            logger.info(f"File upload event published successfully: {event_data.get('file_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to publish file upload event: {e}")
            logger.error(f"File ID: {event_data.get('file_id', 'unknown')}")
            raise
    
    async def publish_file_upload_event(self, event_data: Dict[str, Any]) -> None:
        """
        Convenience method to publish a file upload event.
        
        Args:
            event_data: The file upload event data to publish
        """
        await self.publish_specific_event(event_data)


# Global instance for easy access
_file_upload_event_publisher: FileUploadEventPublisher = None


def get_file_upload_event_publisher() -> FileUploadEventPublisher:
    """Get the global file upload event publisher instance."""
    global _file_upload_event_publisher
    
    if _file_upload_event_publisher is None:
        _file_upload_event_publisher = FileUploadEventPublisher()
    
    return _file_upload_event_publisher
