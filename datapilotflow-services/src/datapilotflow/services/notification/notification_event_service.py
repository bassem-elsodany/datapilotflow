"""
Notification Event Service

This module handles publishing notification events to RabbitMQ for the event-driven
notification system. It decouples notification creation from the main application flow.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import aio_pika
from datapilotflow.domain.config import settings
from datapilotflow.domain.events.constants import (
    NOTIFICATION_EVENTS_DLQ_EXCHANGE,
    NOTIFICATION_EVENTS_DLQ_QUEUE,
    NOTIFICATION_EVENTS_EXCHANGE,
    NOTIFICATION_EVENTS_QUEUE,
    NOTIFICATION_EVENTS_ROUTING_KEY,
)
from datapilotflow.domain.notification import NotificationPriority, NotificationType
from loguru import logger

# RabbitMQ Configuration for Notifications
RABBITMQ_HOST = settings.RABBITMQ_HOST
RABBITMQ_PORT = settings.RABBITMQ_PORT
RABBITMQ_USER = settings.RABBITMQ_USER
RABBITMQ_PASS = settings.RABBITMQ_PASS
RABBITMQ_VHOST = settings.RABBITMQ_VHOST

# Use constants from shared constants file
RABBITMQ_NOTIFICATION_EXCHANGE = NOTIFICATION_EVENTS_EXCHANGE
RABBITMQ_NOTIFICATION_QUEUE = NOTIFICATION_EVENTS_QUEUE
RABBITMQ_NOTIFICATION_DLQ_EXCHANGE = NOTIFICATION_EVENTS_DLQ_EXCHANGE
RABBITMQ_NOTIFICATION_DLQ_QUEUE = NOTIFICATION_EVENTS_DLQ_QUEUE
RABBITMQ_ROUTING_KEY = NOTIFICATION_EVENTS_ROUTING_KEY


async def publish_notification_event(event_payload: dict):
    """Publish notification event to RabbitMQ."""
    try:
        url = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VHOST.lstrip('/')}"
        connection = await aio_pika.connect_robust(url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                RABBITMQ_NOTIFICATION_EXCHANGE,
                aio_pika.ExchangeType.DIRECT,
                durable=True,
            )

            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(event_payload).encode(),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    message_id=str(uuid.uuid4()),
                    timestamp=datetime.now(timezone.utc),
                ),
                routing_key=RABBITMQ_ROUTING_KEY,
            )

            logger.info(
                f"Published notification event: {event_payload.get('event_type')} for user {event_payload.get('user_id')}"
            )

            # WebSocket broadcasting will be handled by the notification listener service
            # which will create the notification in MongoDB and broadcast via the API server's WebSocket service

    except Exception as e:
        logger.error(f"Error publishing notification event: {e}")
        # Publish to DLQ
        await publish_to_notification_dlq(event_payload)


async def publish_to_notification_dlq(event_payload: dict):
    """Publish the notification event to the DLQ exchange/queue."""
    try:
        url = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VHOST.lstrip('/')}"
        connection = await aio_pika.connect_robust(url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                RABBITMQ_NOTIFICATION_DLQ_EXCHANGE,
                aio_pika.ExchangeType.DIRECT,
                durable=True,
            )

            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(event_payload).encode(),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    message_id=str(uuid.uuid4()),
                    timestamp=datetime.now(timezone.utc),
                ),
                routing_key=RABBITMQ_ROUTING_KEY,
            )

            logger.warning(
                f"Published notification event to DLQ: {event_payload.get('event_type')}"
            )

    except Exception as e:
        logger.error(f"Error publishing to notification DLQ: {e}")


# Event-specific publishing functions
async def fire_session_created_event(
    user_id: str, session_id: str, session_name: str, job_title: Optional[str] = None
):
    """Fire session created notification event."""
    event_payload = {
        "event_type": "session_created",
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "session_id": session_id,
        "session_name": session_name,
        "job_title": job_title,
        "notification_type": NotificationType.SESSION_CREATED,
        "priority": NotificationPriority.LOW,
        "title": "New Interview Session Created",
        "message": f"Session '{session_name}' has been created successfully."
        + (f" Job: {job_title}" if job_title else ""),
        "metadata": {
            "session_name": session_name,
            "job_title": job_title,
            "event": "session_created",
        },
    }

    await publish_notification_event(event_payload)


async def fire_session_deleted_event(user_id: str, session_id: str, session_name: str):
    """Fire session deleted notification event."""
    event_payload = {
        "event_type": "session_deleted",
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "session_id": session_id,
        "session_name": session_name,
        "notification_type": NotificationType.SESSION_DELETED,
        "priority": NotificationPriority.LOW,
        "title": "Interview Session Deleted",
        "message": f"Session '{session_name}' has been deleted successfully.",
        "metadata": {"session_name": session_name, "event": "session_deleted"},
    }

    await publish_notification_event(event_payload)


async def fire_interview_started_event(
    user_id: str,
    session_id: str,
    session_name: str,
    candidate_name: Optional[str] = None,
):
    """Fire interview started notification event."""
    message = f"Interview for session '{session_name}' has begun."
    if candidate_name:
        message += f" Candidate: {candidate_name}"

    event_payload = {
        "event_type": "interview_started",
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "session_id": session_id,
        "session_name": session_name,
        "candidate_name": candidate_name,
        "notification_type": NotificationType.INTERVIEW_STARTED,
        "priority": NotificationPriority.HIGH,
        "title": "Interview Started",
        "message": message,
        "metadata": {
            "session_name": session_name,
            "candidate_name": candidate_name,
            "event": "interview_started",
        },
    }

    await publish_notification_event(event_payload)


async def fire_resume_analysis_completed_event(
    user_id: str,
    session_id: str,
    candidate_name: str,
    analysis_summary: Optional[str] = None,
):
    """Fire resume analysis completed notification event."""
    message = f"Resume analysis for {candidate_name} has been completed successfully."
    if analysis_summary:
        message += f" Summary: {analysis_summary}"

    event_payload = {
        "event_type": "resume_analysis_completed",
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "session_id": session_id,
        "candidate_name": candidate_name,
        "analysis_summary": analysis_summary,
        "notification_type": NotificationType.RESUME_ANALYSIS_COMPLETED,
        "priority": NotificationPriority.MEDIUM,
        "title": "Resume Analysis Completed",
        "message": message,
        "metadata": {
            "candidate_name": candidate_name,
            "analysis_summary": analysis_summary,
            "event": "resume_analysis_completed",
        },
    }

    await publish_notification_event(event_payload)


async def fire_job_analysis_completed_event(
    user_id: str, session_id: str, job_title: str, company_name: Optional[str] = None
):
    """Fire job analysis completed notification event."""
    message = f"Job analysis for '{job_title}' has been completed successfully."
    if company_name:
        message += f" Company: {company_name}"

    event_payload = {
        "event_type": "job_analysis_completed",
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "session_id": session_id,
        "job_title": job_title,
        "company_name": company_name,
        "notification_type": NotificationType.JOB_ANALYSIS_COMPLETED,
        "priority": NotificationPriority.MEDIUM,
        "title": "Job Analysis Completed",
        "message": message,
        "metadata": {
            "job_title": job_title,
            "company_name": company_name,
            "event": "job_analysis_completed",
        },
    }

    await publish_notification_event(event_payload)


async def fire_error_event(
    user_id: str,
    session_id: Optional[str],
    error_type: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None,
):
    """Fire error notification event."""
    event_payload = {
        "event_type": "error",
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "session_id": session_id,
        "error_type": error_type,
        "error_message": error_message,
        "context": context or {},
        "notification_type": NotificationType.ERROR,
        "priority": NotificationPriority.HIGH,
        "title": f"Error: {error_type}",
        "message": error_message,
        "metadata": {
            "error_type": error_type,
            "context": context or {},
            "event": "error",
        },
    }

    await publish_notification_event(event_payload)


async def fire_job_deleted_event(user_id: str, job_title: str, job_id: str):
    """Fire job deleted notification event."""
    event_payload = {
        "event_type": "job_deleted",
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "job_id": job_id,
        "job_title": job_title,
        "notification_type": NotificationType.JOB_DELETED,
        "priority": NotificationPriority.MEDIUM,
        "title": "Job Description Deleted",
        "message": f"Job description '{job_title}' has been deleted successfully.",
        "metadata": {"job_id": job_id, "job_title": job_title, "event": "job_deleted"},
    }

    await publish_notification_event(event_payload)


async def fire_resume_deleted_event(
    user_id: str, candidate_name: str, candidate_id: str
):
    """Fire resume deleted notification event."""
    event_payload = {
        "event_type": "resume_deleted",
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "notification_type": NotificationType.RESUME_DELETED,
        "priority": NotificationPriority.MEDIUM,
        "title": "Resume Deleted",
        "message": f"Resume for '{candidate_name}' has been deleted successfully.",
        "metadata": {
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "event": "resume_deleted",
        },
    }

    await publish_notification_event(event_payload)
