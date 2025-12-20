"""
File Upload Event Listener.

This module provides specific functionality for listening to file upload-related events
from RabbitMQ, extending the base event listener.
"""

import asyncio
import traceback
import shutil
from pathlib import Path
from typing import Dict, Any
from loguru import logger
from datapilotflow.services.events import (
    FILE_UPLOAD_EVENTS_EXCHANGE,
    FILE_UPLOAD_EVENTS_QUEUE,
    FILE_UPLOAD_EVENTS_ROUTING_KEY,
    FILE_UPLOAD_EVENTS_DLQ_EXCHANGE,
    FILE_UPLOAD_EVENTS_DLQ_QUEUE,
    EventTypes
)
from datapilotflow.processors.file_upload.file_upload_processor import get_file_upload_event_processor
from .base_event_listener import BaseEventListener


class FileUploadEventListener(BaseEventListener):
    """Event listener for file upload-related events."""
    
    def __init__(self):
        """Initialize the file upload event listener with file upload-specific configuration."""
        super().__init__(
            exchange_name=FILE_UPLOAD_EVENTS_EXCHANGE,
            queue_name=FILE_UPLOAD_EVENTS_QUEUE,
            routing_key=FILE_UPLOAD_EVENTS_ROUTING_KEY,
            dlq_exchange_name=FILE_UPLOAD_EVENTS_DLQ_EXCHANGE,
            dlq_queue_name=FILE_UPLOAD_EVENTS_DLQ_QUEUE
        )
        
        self.file_processor = get_file_upload_event_processor()
    
    async def handle_event(self, event_payload: Dict[str, Any]) -> bool:
        """
        Handle a file upload event.
        
        Args:
            event_payload: The file upload event data to process
            
        Returns:
            True if event was processed successfully, False otherwise
        """
        try:
            # Extract event information
            event_type = event_payload.get("event_type")
            file_id = event_payload.get("file_id")
            file_path = event_payload.get("location")
            user_id = event_payload.get("user_id")
            
            logger.info(f"Handling file upload event: {event_type} for file {file_id}")
            
            # Handle different event types
            if event_type == EventTypes.FILE_UPLOAD:
                return await self.file_processor.process_file_upload(event_payload)
            else:
                logger.warning(f"Unknown file upload event type: {event_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling file upload event: {e}")
            return False
    


# Global instance for easy access
_file_upload_event_listener: FileUploadEventListener = None


def get_file_upload_event_listener() -> FileUploadEventListener:
    """Get the global file upload event listener instance."""
    global _file_upload_event_listener
    
    if _file_upload_event_listener is None:
        _file_upload_event_listener = FileUploadEventListener()
    
    return _file_upload_event_listener


async def start_file_upload_event_listener() -> None:
    """
    Convenience function to start the file upload event listener.
    """
    listener = get_file_upload_event_listener()
    await listener.start_listening()
