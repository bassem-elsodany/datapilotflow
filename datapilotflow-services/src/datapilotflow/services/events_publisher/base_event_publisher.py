"""
Base Event Publisher.

This module provides the base functionality for publishing events to RabbitMQ,
with common logic that can be extended by specific event publishers.
"""

import json
import aio_pika
from datetime import datetime
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from loguru import logger

from datapilotflow.infrastructure.mq.client import RabbitMQClient


class BaseEventPublisher(ABC):
    """Base class for event publishers with common RabbitMQ functionality."""
    
    def __init__(self, exchange_name: str, queue_name: str, routing_key: str, dlq_exchange_name: str, dlq_queue_name: str):
        """
        Initialize the base event publisher.
        
        Args:
            exchange_name: Name of the main exchange
            queue_name: Name of the main queue
            routing_key: Routing key for the main queue
            dlq_exchange_name: Name of the dead letter queue exchange
            dlq_queue_name: Name of the dead letter queue
        """
        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.dlq_exchange_name = dlq_exchange_name
        self.dlq_queue_name = dlq_queue_name
        
        # Initialize RabbitMQ client (uses pooled connection)
        self.mq_client = RabbitMQClient()
    
    async def publish_event(self, event_payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> None:
        """
        Publish an event to RabbitMQ using pooled connection.
        
        Args:
            event_payload: The event data to publish
            headers: Optional headers for the message
        """
        try:
            # Add metadata to the event payload
            enriched_payload = {
                **event_payload,
                "published_at": datetime.utcnow().isoformat(),
                "source": self.__class__.__name__,
                "version": "1.0"
            }
            
            # Prepare message headers
            message_headers = headers or {}
            message_headers.update({
                "event_type": event_payload.get("event_type", "unknown"),
                "aggregate_id": event_payload.get("aggregate_id", "unknown"),
                "user_id": event_payload.get("user_id", "unknown")
            })
            
            # Publish using pooled MQ client
            await self.mq_client.publish_message(
                exchange_name=self.exchange_name,
                routing_key=self.routing_key,
                message_body=json.dumps(enriched_payload).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                headers=message_headers
            )
            
            logger.info(f"Event published successfully: {event_payload.get('event_id', 'unknown')}")
            logger.debug(f"Event payload: {enriched_payload}")
                
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            logger.error(f"Event ID: {event_payload.get('event_id', 'unknown')}")
            raise
    
    async def publish_to_dlq(self, event_payload: Dict[str, Any], error_info: Dict[str, Any]) -> None:
        """
        Publish a failed event to the Dead Letter Queue using pooled connection.
        
        Args:
            event_payload: The original event payload
            error_info: Information about the error that occurred
        """
        try:
            # Add error information to the event payload
            dlq_payload = {
                **event_payload,
                "error": {
                    **error_info,
                    "dlq_timestamp": datetime.utcnow().isoformat(),
                    "dlq_source": self.__class__.__name__
                }
            }
            
            # Publish to DLQ using pooled MQ client
            await self.mq_client.publish_message(
                exchange_name=self.dlq_exchange_name,
                routing_key=self.dlq_queue_name,
                message_body=json.dumps(dlq_payload).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                headers={
                    "event_type": "event_dlq",
                    "original_event_type": event_payload.get("event_type"),
                    "error_type": error_info.get("error_type", "unknown")
                }
            )
            
            logger.warning(f"Event published to DLQ: {event_payload.get('event_id', 'unknown')}")
                
        except Exception as e:
            logger.error(f"Failed to publish event to DLQ: {e}")
            raise
    
    
    @abstractmethod
    async def publish_specific_event(self, event_data: Any) -> None:
        """
        Publish a specific type of event. Must be implemented by subclasses.
        
        Args:
            event_data: The specific event data to publish
        """
        pass
