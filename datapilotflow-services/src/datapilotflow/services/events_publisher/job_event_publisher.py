"""
Job Event Publisher.

This module provides specific functionality for publishing job-related events
to RabbitMQ, extending the base event publisher.
"""

from typing import Any, Dict

from loguru import logger

from datapilotflow.domain.events.job_events import JobActionRequested
from datapilotflow.services.events import (
    JOB_EVENTS_DLQ_EXCHANGE,
    JOB_EVENTS_DLQ_QUEUE,
    JOB_EVENTS_EXCHANGE,
    JOB_EVENTS_QUEUE,
    JOB_EVENTS_ROUTING_KEY,
    EventTypes,
)

from .base_event_publisher import BaseEventPublisher


class JobEventPublisher(BaseEventPublisher):
    """Event publisher for job-related events."""

    def __init__(self):
        """Initialize the job event publisher with job-specific configuration."""
        super().__init__(
            exchange_name=JOB_EVENTS_EXCHANGE,
            queue_name=JOB_EVENTS_QUEUE,
            routing_key=JOB_EVENTS_ROUTING_KEY,
            dlq_exchange_name=JOB_EVENTS_DLQ_EXCHANGE,
            dlq_queue_name=JOB_EVENTS_DLQ_QUEUE,
        )

    async def publish_specific_event(self, event_data: JobActionRequested) -> None:
        """
        Publish a JobActionRequested event.

        Args:
            event_data: The JobActionRequested event to publish
        """
        try:
            # Convert event to dictionary for JSON serialization with datetime serialization
            event_payload = event_data.model_dump(mode="json")

            # Add job-specific headers
            headers = {
                "job_id": event_data.job_id,
                "user_id": event_data.user_id,
                "event_category": "job_execution",
            }

            # Publish using base class method
            await self.publish_event(event_payload, headers)

            logger.info(
                f"Job execution event published successfully: {event_data.event_id}"
            )

        except Exception as e:
            logger.error(f"Failed to publish job execution event: {e}")
            logger.error(
                f"Event ID: {event_data.event_id}, Job ID: {event_data.job_id}"
            )
            raise

    async def publish_job_action_requested(self, event: JobActionRequested) -> None:
        """
        Convenience method to publish a JobActionRequested event.

        Args:
            event: The JobActionRequested event to publish
        """
        await self.publish_specific_event(event)


# Global instance for easy access
_job_event_publisher: JobEventPublisher = None


def get_job_event_publisher() -> JobEventPublisher:
    """Get the global job event publisher instance."""
    global _job_event_publisher

    if _job_event_publisher is None:
        _job_event_publisher = JobEventPublisher()

    return _job_event_publisher
