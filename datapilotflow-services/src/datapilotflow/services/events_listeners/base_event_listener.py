"""
Base Event Listener.

This module provides the base functionality for listening to events from RabbitMQ,
with common logic that can be extended by specific event listeners.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, Optional

import aio_pika
from aio_pika.exceptions import ChannelPreconditionFailed
from loguru import logger

from datapilotflow.config import settings


class BaseEventListener(ABC):
    """Base class for event listeners with common RabbitMQ functionality."""

    def __init__(
        self,
        exchange_name: str,
        queue_name: str,
        routing_key: str,
        dlq_exchange_name: str,
        dlq_queue_name: str,
    ):
        """
        Initialize the base event listener.

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
        self.rabbitmq_heartbeat = settings.RABBITMQ_HEARTBEAT

        # Listener state
        self.is_running = False
        self.connection = None
        self.channel = None

    def _get_connection_url(self) -> str:
        """Get RabbitMQ connection URL."""
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_pass}@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost.lstrip('/')}"

    async def setup_queues(self) -> None:
        """
        Setup RabbitMQ exchanges and queues for this event listener.
        This should be called before starting to listen.
        """
        try:
            # Build RabbitMQ connection URL
            url = self._get_connection_url()

            # Connect to RabbitMQ
            self.connection = await aio_pika.connect_robust(
                url, heartbeat=self.rabbitmq_heartbeat
            )
            self.channel = await self.connection.channel()

            # Set QoS
            await self.channel.set_qos(prefetch_count=10)

            # Declare main exchange and queue
            main_exchange = await self.channel.declare_exchange(
                self.exchange_name, aio_pika.ExchangeType.DIRECT, durable=True
            )

            # Try to declare queue with arguments, fall back to passive if it exists with different args
            try:
                main_queue = await self.channel.declare_queue(
                    self.queue_name,
                    durable=True,
                    arguments={
                        "x-message-ttl": self.rabbitmq_message_ttl,
                        "x-dead-letter-exchange": self.dlq_exchange_name,
                        "x-dead-letter-routing-key": self.dlq_queue_name,
                    },
                )
            except ChannelPreconditionFailed as e:
                if "PRECONDITION_FAILED" in str(e):
                    logger.warning(
                        f"Queue {self.queue_name} already exists with different arguments. Using existing queue."
                    )
                    # Use passive declaration to get the existing queue
                    main_queue = await self.channel.declare_queue(
                        self.queue_name, passive=True
                    )
                else:
                    raise

            # Declare DLQ exchange and queue
            dlq_exchange = await self.channel.declare_exchange(
                self.dlq_exchange_name, aio_pika.ExchangeType.DIRECT, durable=True
            )

            # Try to declare DLQ with arguments, fall back to passive if it exists with different args
            try:
                dlq_queue = await self.channel.declare_queue(
                    self.dlq_queue_name,
                    durable=True,
                    arguments={"x-message-ttl": self.rabbitmq_message_ttl},
                )
            except ChannelPreconditionFailed as e:
                if "PRECONDITION_FAILED" in str(e):
                    logger.warning(
                        f"DLQ {self.dlq_queue_name} already exists with different arguments. Using existing queue."
                    )
                    # Use passive declaration to get the existing queue
                    dlq_queue = await self.channel.declare_queue(
                        self.dlq_queue_name, passive=True
                    )
                else:
                    raise

            # Bind queues to exchanges
            await main_queue.bind(main_exchange, self.routing_key)
            await dlq_queue.bind(dlq_exchange, self.dlq_queue_name)

            logger.info(
                f"Event listener queues setup completed for {self.__class__.__name__}:"
            )
            logger.info(
                f"  Main: {self.exchange_name} -> {self.queue_name} (routing: {self.routing_key})"
            )
            logger.info(f"  DLQ: {self.dlq_exchange_name} -> {self.dlq_queue_name}")

        except Exception as e:
            logger.error(
                f"Failed to setup event listener queues for {self.__class__.__name__}: {e}"
            )
            raise

    async def start_listening(self) -> None:
        """
        Start listening for events. This method will run indefinitely.
        """
        try:
            if not self.connection or not self.channel:
                await self.setup_queues()

            self.is_running = True
            logger.info(f"Starting {self.__class__.__name__} event listener...")

            # Get the main queue (use passive to avoid conflicts)
            queue = await self.channel.declare_queue(self.queue_name, passive=True)

            # Start consuming messages
            await queue.consume(self._process_message, no_ack=False)

            logger.info(
                f"{self.__class__.__name__} event listener started. Waiting for messages..."
            )

            # Keep the listener running
            try:
                await asyncio.Future()  # Run forever
            except KeyboardInterrupt:
                logger.info(f"{self.__class__.__name__} event listener stopped by user")
                await self.stop_listening()

        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__} event listener: {e}")
            await self.stop_listening()
            raise

    async def stop_listening(self) -> None:
        """Stop the event listener and close connections."""
        try:
            self.is_running = False

            if self.channel:
                await self.channel.close()

            if self.connection:
                await self.connection.close()

            logger.info(f"{self.__class__.__name__} event listener stopped")

        except Exception as e:
            logger.error(
                f"Error stopping {self.__class__.__name__} event listener: {e}"
            )

    async def _process_message(self, message: aio_pika.IncomingMessage) -> None:
        """
        Process an incoming message. This method handles common message processing
        and delegates to the specific event handler.

        For long-running jobs, we ACK the message immediately to prevent timeout issues
        and then process the event asynchronously.

        Args:
            message: The incoming RabbitMQ message
        """
        try:
            # Parse message body first
            body = message.body.decode()
            event_payload = json.loads(body)
            event_type = event_payload.get("event_type", "unknown")

            logger.info(f"Received event: {event_type}")

            # ACK the message immediately to prevent timeout for long-running jobs
            await message.ack()
            logger.debug(f"ACKed message for event: {event_type}")

            # Now process the event asynchronously (job can take hours)
            try:
                success = await self.handle_event(event_payload)

                if success:
                    logger.info(f"Successfully processed event: {event_type}")
                else:
                    logger.error(f"Failed to process event: {event_type}")
                    # Note: Message already ACKed, so failure is just logged

            except Exception as e:
                logger.error(f"Error processing event {event_type}: {e}")
                # Note: Message already ACKed, so we can't send to DLQ
                # Job failures are handled by the job processor itself

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding event message: {e}")
            # NACK and send to DLQ (message parsing failed before ACK)
            await message.nack(requeue=False)
        except Exception as e:
            logger.error(f"Error receiving event message: {e}")
            logger.error(
                f"Message body: {message.body.decode() if hasattr(message, 'body') else 'N/A'}"
            )
            # NACK and send to DLQ
            await message.nack(requeue=False)

    @abstractmethod
    async def handle_event(self, event_payload: Dict[str, Any]) -> bool:
        """
        Handle a specific event. Must be implemented by subclasses.

        Args:
            event_payload: The event data to process

        Returns:
            True if event was processed successfully, False otherwise
        """
        pass
