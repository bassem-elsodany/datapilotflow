"""
RabbitMQ Client with Connection Pooling.

This module provides a singleton RabbitMQ client with connection pooling
for efficient message queue operations across the application.
"""

import asyncio
from typing import Optional
from contextlib import asynccontextmanager

import aio_pika
from aio_pika import Connection, Channel, Exchange, Queue
from loguru import logger

from datapilotflow.domain.config import settings


# Global RabbitMQ connection instance
_rabbitmq_connection: Optional[Connection] = None
_connection_lock = asyncio.Lock()


def _get_connection_url() -> str:
    """Build RabbitMQ connection URL from settings."""
    vhost = settings.RABBITMQ_VHOST.lstrip("/")
    return (
        f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASS}"
        f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/{vhost}"
    )


async def get_rabbitmq_client() -> Connection:
    """
    Get or create a singleton RabbitMQ connection with pooling.
    
    Uses aio_pika's connect_robust which provides automatic reconnection
    and connection pooling capabilities.
    
    Returns:
        Connection: The singleton RabbitMQ connection
        
    Raises:
        Exception: If connection fails
    """
    global _rabbitmq_connection
    
    async with _connection_lock:
        if _rabbitmq_connection is None or _rabbitmq_connection.is_closed:
            try:
                url = _get_connection_url()
                logger.info(f"Creating RabbitMQ connection to {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
                
                _rabbitmq_connection = await aio_pika.connect_robust(
                    url,
                    heartbeat=settings.RABBITMQ_HEARTBEAT,
                    client_properties={
                        "connection_name": "datapilotflow-infrastructure",
                    },
                )
                
                logger.info("Created singleton RabbitMQ connection with pooling")
            except Exception as e:
                logger.error(f"Failed to create RabbitMQ connection: {e}")
                raise
        
        return _rabbitmq_connection


async def close_rabbitmq_client() -> None:
    """Close the global RabbitMQ connection."""
    global _rabbitmq_connection
    
    async with _connection_lock:
        if _rabbitmq_connection is not None and not _rabbitmq_connection.is_closed:
            await _rabbitmq_connection.close()
            _rabbitmq_connection = None
            logger.info("Closed singleton RabbitMQ connection")


class RabbitMQClient:
    """
    RabbitMQ Client wrapper for message queue operations.
    
    This class provides a clean interface for RabbitMQ operations with
    connection pooling and automatic reconnection. It follows the same
    pattern as MongoClientWrapper for consistency.
    
    Example:
        ```python
        client = RabbitMQClient()
        
        # Get a channel (uses pooled connection)
        async with client.get_channel() as channel:
            exchange = await channel.declare_exchange(
                "my_exchange", aio_pika.ExchangeType.DIRECT, durable=True
            )
            await exchange.publish(message, routing_key="my.key")
        ```
    """
    
    def __init__(self):
        """Initialize the RabbitMQ client."""
        self._connection: Optional[Connection] = None
        self._channel: Optional[Channel] = None
    
    async def get_connection(self) -> Connection:
        """
        Get the RabbitMQ connection (singleton, pooled).
        
        Returns:
            Connection: The RabbitMQ connection
        """
        if self._connection is None or self._connection.is_closed:
            self._connection = await get_rabbitmq_client()
        return self._connection
    
    @asynccontextmanager
    async def get_channel(self):
        """
        Get a RabbitMQ channel (context manager).
        
        Channels are lightweight and can be created per operation.
        The connection is pooled and reused.
        
        Yields:
            Channel: The RabbitMQ channel
            
        Example:
            ```python
            client = RabbitMQClient()
            async with client.get_channel() as channel:
                # Use channel for operations
                exchange = await channel.declare_exchange(...)
            ```
        """
        connection = await self.get_connection()
        channel = await connection.channel()
        
        try:
            yield channel
        finally:
            await channel.close()
    
    async def declare_exchange(
        self,
        exchange_name: str,
        exchange_type: aio_pika.ExchangeType = aio_pika.ExchangeType.DIRECT,
        durable: bool = True,
        auto_delete: bool = False,
    ) -> Exchange:
        """
        Declare an exchange.
        
        Args:
            exchange_name: Name of the exchange
            exchange_type: Type of exchange (DIRECT, TOPIC, FANOUT, HEADERS)
            durable: Whether the exchange survives broker restart
            auto_delete: Whether to delete exchange when no longer used
            
        Returns:
            Exchange: The declared exchange
        """
        async with self.get_channel() as channel:
            exchange = await channel.declare_exchange(
                exchange_name,
                exchange_type,
                durable=durable,
                auto_delete=auto_delete,
            )
            return exchange
    
    async def declare_queue(
        self,
        queue_name: str,
        durable: bool = True,
        exclusive: bool = False,
        auto_delete: bool = False,
        arguments: Optional[dict] = None,
    ) -> Queue:
        """
        Declare a queue.
        
        Args:
            queue_name: Name of the queue
            durable: Whether the queue survives broker restart
            exclusive: Whether the queue can only be used by one connection
            auto_delete: Whether to delete queue when no longer used
            arguments: Additional queue arguments (e.g., TTL, DLQ settings)
            
        Returns:
            Queue: The declared queue
        """
        async with self.get_channel() as channel:
            queue = await channel.declare_queue(
                queue_name,
                durable=durable,
                exclusive=exclusive,
                auto_delete=auto_delete,
                arguments=arguments or {},
            )
            return queue
    
    async def publish_message(
        self,
        exchange_name: str,
        routing_key: str,
        message_body: bytes,
        content_type: str = "application/json",
        delivery_mode: aio_pika.DeliveryMode = aio_pika.DeliveryMode.PERSISTENT,
        headers: Optional[dict] = None,
    ) -> None:
        """
        Publish a message to an exchange.
        
        Args:
            exchange_name: Name of the exchange
            routing_key: Routing key for the message
            message_body: Message body as bytes
            content_type: Content type of the message
            delivery_mode: Delivery mode (PERSISTENT or NON_PERSISTENT)
            headers: Optional message headers
        """
        async with self.get_channel() as channel:
            exchange = await channel.declare_exchange(
                exchange_name,
                aio_pika.ExchangeType.DIRECT,
                durable=True,
            )
            
            message = aio_pika.Message(
                body=message_body,
                content_type=content_type,
                delivery_mode=delivery_mode,
                headers=headers or {},
            )
            
            await exchange.publish(message, routing_key=routing_key)
            logger.debug(f"Published message to {exchange_name} with routing key {routing_key}")
    
    async def consume_messages(
        self,
        queue_name: str,
        callback,
        prefetch_count: int = 10,
        no_ack: bool = False,
    ) -> None:
        """
        Consume messages from a queue.
        
        Args:
            queue_name: Name of the queue to consume from
            callback: Async function to process messages: async def callback(message: IncomingMessage)
            prefetch_count: Number of unacknowledged messages per consumer
            no_ack: Whether to auto-acknowledge messages
        """
        connection = await self.get_connection()
        channel = await connection.channel()
        
        try:
            await channel.set_qos(prefetch_count=prefetch_count)
            
            queue = await channel.declare_queue(queue_name, durable=True)
            
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    try:
                        await callback(message)
                        if not no_ack:
                            await message.ack()
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        if not no_ack:
                            await message.nack(requeue=True)
        finally:
            await channel.close()
    
    async def close(self) -> None:
        """Close the client connection (usually not needed due to singleton)."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            self._connection = None

