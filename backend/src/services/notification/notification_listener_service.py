"""
Notification Listener Service

This module handles consuming notification events from RabbitMQ and creating
notifications in MongoDB. It runs as a separate service to handle notification
creation asynchronously.
"""

import json
import asyncio
import aio_pika
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from loguru import logger

from src.config import settings
from src.domain.notification import (
    NotificationCreate, NotificationType, NotificationPriority, NotificationStatus
)
from src.services.notification.dao.notification_service import NotificationService

# RabbitMQ Configuration for Notifications
RABBITMQ_HOST = settings.RABBITMQ_HOST
RABBITMQ_PORT = settings.RABBITMQ_PORT
RABBITMQ_USER = settings.RABBITMQ_USER
RABBITMQ_PASS = settings.RABBITMQ_PASS
RABBITMQ_VHOST = settings.RABBITMQ_VHOST

# Notification Queues
RABBITMQ_NOTIFICATION_EXCHANGE = "skillpilot_notification_exchange"
RABBITMQ_NOTIFICATION_QUEUE = "skillpilot_notification_queue"
RABBITMQ_NOTIFICATION_DLQ_EXCHANGE = "skillpilot_notification_dlq_exchange"
RABBITMQ_NOTIFICATION_DLQ_QUEUE = "skillpilot_notification_dlq_queue"


async def setup_notification_queues():
    """Setup notification queues and exchanges in RabbitMQ."""
    try:
        url = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VHOST.lstrip('/')}"
        connection = await aio_pika.connect_robust(url)
        async with connection:
            channel = await connection.channel()
            
            # Declare main notification exchange
            await channel.declare_exchange(
                RABBITMQ_NOTIFICATION_EXCHANGE,
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )
            
            # Declare main notification queue
            queue = await channel.declare_queue(
                RABBITMQ_NOTIFICATION_QUEUE,
                durable=True
            )
            
            # Bind queue to exchange
            await queue.bind(RABBITMQ_NOTIFICATION_EXCHANGE, RABBITMQ_NOTIFICATION_QUEUE)
            
            # Declare DLQ exchange
            await channel.declare_exchange(
                RABBITMQ_NOTIFICATION_DLQ_EXCHANGE,
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )
            
            # Declare DLQ queue
            dlq_queue = await channel.declare_queue(
                RABBITMQ_NOTIFICATION_DLQ_QUEUE,
                durable=True
            )
            
            # Bind DLQ queue to DLQ exchange
            await dlq_queue.bind(RABBITMQ_NOTIFICATION_DLQ_EXCHANGE, RABBITMQ_NOTIFICATION_DLQ_QUEUE)
            
            logger.info("Notification queues and exchanges setup completed")
            
    except Exception as e:
        logger.error(f"Error setting up notification queues: {e}")
        raise


async def process_notification_event(event_payload: Dict[str, Any]) -> bool:
    """Process a notification event and create notification in MongoDB."""
    try:
        notification_service = NotificationService()
        
        # Extract notification data from event
        user_id = event_payload.get("user_id")
        session_id = event_payload.get("session_id")
        notification_type = event_payload.get("notification_type")
        priority = event_payload.get("priority")
        title = event_payload.get("title")
        message = event_payload.get("message")
        metadata = event_payload.get("metadata", {})
        progress = event_payload.get("progress")  # Extract progress for job notifications
        
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
        # Knowledge Job Processing Notifications
        elif notification_type in [NotificationType.KNOWLEDGE_JOB_STARTED, NotificationType.KNOWLEDGE_JOB_PROGRESS]:
            # Progress notifications expire quickly (1 hour) since they're transient
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        elif notification_type in [NotificationType.KNOWLEDGE_JOB_COMPLETED, NotificationType.KNOWLEDGE_JOB_FAILED, NotificationType.KNOWLEDGE_JOB_CANCELLED]:
            # Final status notifications kept for 7 days
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
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
            progress=progress,  # Include progress for job notifications
            metadata=metadata,
            expires_at=expires_at
        )
        
        # Create notification in MongoDB
        notification_id = notification_service.create_notification(notification_data)
        
        if notification_id:
            logger.info(f"Created notification {notification_id} for event {event_payload.get('event_type')} user {user_id}")
            
            # Broadcast notification via WebSocket through API server
            try:
                import aiohttp
                from config import settings
                
                # Prepare broadcast data
                broadcast_data = {
                    "id": notification_id,
                    "user_id": user_id,
                    "session_id": session_id,
                    "type": notification_type,
                    "priority": priority,
                    "title": title,
                    "message": message,
                    "progress": progress,  # Include progress for job notifications
                    "metadata": metadata,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Call the broadcast endpoint using configured API server settings
                async with aiohttp.ClientSession() as session:
                    # Use full API path with version prefix (/api/v1)
                    api_url = f"http://{settings.API_SERVER_HOST}:{settings.API_SERVER_PORT}/api/v1/notifications/broadcast"
                    headers = {"Content-Type": "application/json"}
                    
                    async with session.post(api_url, json=broadcast_data, headers=headers) as response:
                        if response.status == 200:
                            logger.info(f"Notification {notification_id} broadcasted successfully")
                        else:
                            logger.warning(f"Failed to broadcast notification {notification_id}: {response.status}")
                            
            except Exception as broadcast_error:
                logger.warning(f"Error broadcasting notification {notification_id}: {broadcast_error}")
                # Don't fail the notification creation if broadcasting fails
            
            return True
        else:
            logger.error(f"Failed to create notification for event {event_payload.get('event_type')}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing notification event: {e}")
        return False


async def notification_event_listener():
    """Main notification event listener that consumes events from RabbitMQ."""
    try:
        logger.info("Starting notification event listener...")
        
        # Setup queues
        await setup_notification_queues()
        
        # Connect to RabbitMQ
        url = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VHOST.lstrip('/')}"
        connection = await aio_pika.connect_robust(url)
        
        async with connection:
            channel = await connection.channel()
            
            # Set QoS
            await channel.set_qos(prefetch_count=10)
            
            # Declare queue
            queue = await channel.declare_queue(
                RABBITMQ_NOTIFICATION_QUEUE,
                durable=True
            )
            
            logger.info("Notification event listener started. Waiting for messages...")
            
            async def process_message(message: aio_pika.IncomingMessage):
                """Process individual notification message."""
                async with message.process():
                    try:
                        # Parse message body
                        body = message.body.decode()
                        event_payload = json.loads(body)
                        
                        logger.info(f"Processing notification event: {event_payload.get('event_type')}")
                        
                        # Process the notification event
                        success = await process_notification_event(event_payload)
                        
                        if success:
                            logger.info(f"Successfully processed notification event: {event_payload.get('event_type')}")
                        else:
                            logger.error(f"Failed to process notification event: {event_payload.get('event_type')}")
                            # Could implement retry logic here
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding notification message: {e}")
                    except Exception as e:
                        logger.error(f"Error processing notification message: {e}")
                        logger.error(f"Message body: {message.body.decode()}")
            
            # Start consuming messages
            await queue.consume(process_message)
            
            # Keep the listener running
            try:
                await asyncio.Future()  # Run forever
            except KeyboardInterrupt:
                logger.info("Notification event listener stopped by user")
                
    except Exception as e:
        logger.error(f"Error in notification event listener: {e}")
        raise


async def start_notification_listener():
    """Start the notification event listener."""
    try:
        await notification_event_listener()
    except Exception as e:
        logger.error(f"Failed to start notification listener: {e}")
        # Could implement retry logic here
        raise


if __name__ == "__main__":
    """Run the notification listener as a standalone service."""
    try:
        asyncio.run(start_notification_listener())
    except KeyboardInterrupt:
        logger.info("Notification listener service stopped")
    except Exception as e:
        logger.error(f"Notification listener service failed: {e}")
