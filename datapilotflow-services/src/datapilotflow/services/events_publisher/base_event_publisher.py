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
from datapilotflow.config import settings


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
        
        # RabbitMQ Configuration
        self.rabbitmq_host = settings.RABBITMQ_HOST
        self.rabbitmq_port = settings.RABBITMQ_PORT
        self.rabbitmq_user = settings.RABBITMQ_USER
        self.rabbitmq_pass = settings.RABBITMQ_PASS
        self.rabbitmq_vhost = settings.RABBITMQ_VHOST
        self.rabbitmq_message_ttl = settings.RABBITMQ_MESSAGE_TTL
    
    def _get_connection_url(self) -> str:
        """Get RabbitMQ connection URL."""
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_pass}@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost.lstrip('/')}"
    
    async def publish_event(self, event_payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> None:
        """
        Publish an event to RabbitMQ.
        
        Args:
            event_payload: The event data to publish
            headers: Optional headers for the message
        """
        try:
            # Build RabbitMQ connection URL
            url = self._get_connection_url()
            
            # Connect to RabbitMQ
            connection = await aio_pika.connect_robust(url)
            
            async with connection:
                channel = await connection.channel()
                
                # Declare the main exchange
                exchange = await channel.declare_exchange(
                    self.exchange_name, 
                    aio_pika.ExchangeType.DIRECT, 
                    durable=True
                )
                
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
                
                # Publish the event
                await exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(enriched_payload).encode(),
                        content_type="application/json",
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        headers=message_headers
                    ),
                    routing_key=self.routing_key
                )
                
                logger.info(f"Event published successfully: {event_payload.get('event_id', 'unknown')}")
                logger.debug(f"Event payload: {enriched_payload}")
                
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            logger.error(f"Event ID: {event_payload.get('event_id', 'unknown')}")
            raise
    
    async def publish_to_dlq(self, event_payload: Dict[str, Any], error_info: Dict[str, Any]) -> None:
        """
        Publish a failed event to the Dead Letter Queue.
        
        Args:
            event_payload: The original event payload
            error_info: Information about the error that occurred
        """
        try:
            # Build RabbitMQ connection URL
            url = self._get_connection_url()
            
            # Connect to RabbitMQ
            connection = await aio_pika.connect_robust(url)
            
            async with connection:
                channel = await connection.channel()
                
                # Declare the DLQ exchange
                dlq_exchange = await channel.declare_exchange(
                    self.dlq_exchange_name, 
                    aio_pika.ExchangeType.DIRECT, 
                    durable=True
                )
                
                # Add error information to the event payload
                dlq_payload = {
                    **event_payload,
                    "error": {
                        **error_info,
                        "dlq_timestamp": datetime.utcnow().isoformat(),
                        "dlq_source": self.__class__.__name__
                    }
                }
                
                # Publish to DLQ
                await dlq_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(dlq_payload).encode(),
                        content_type="application/json",
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        headers={
                            "event_type": "event_dlq",
                            "original_event_type": event_payload.get("event_type"),
                            "error_type": error_info.get("error_type", "unknown")
                        }
                    ),
                    routing_key=self.dlq_queue_name
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
