"""
Job Event Listener.

This module provides specific functionality for listening to job-related events
from RabbitMQ, extending the base event listener.
"""

import asyncio
from typing import Any, Dict

from loguru import logger

from src.domain.events.job_events import JobActionRequested
from src.domain.knowledge.knowledge_job import JobStatus
from src.processors.knowledge_job.refactored_knowledge_job_event_processor import (
    RefactoredKnowledgeJobEventProcessor,
)
from src.processors.knowledge_job.feature_flags import get_feature_flags
from src.services.events import (
    JOB_EVENTS_DLQ_EXCHANGE,
    JOB_EVENTS_DLQ_QUEUE,
    JOB_EVENTS_EXCHANGE,
    JOB_EVENTS_QUEUE,
    JOB_EVENTS_ROUTING_KEY,
    EventTypes,
)

from .base_event_listener import BaseEventListener


class JobEventListener(BaseEventListener):
    """Event listener for job-related events - using NEW refactored architecture."""

    def __init__(self):
        """Initialize the job event listener with job-specific configuration."""
        super().__init__(
            exchange_name=JOB_EVENTS_EXCHANGE,
            queue_name=JOB_EVENTS_QUEUE,
            routing_key=JOB_EVENTS_ROUTING_KEY,
            dlq_exchange_name=JOB_EVENTS_DLQ_EXCHANGE,
            dlq_queue_name=JOB_EVENTS_DLQ_QUEUE,
        )
        # Use the new refactored processor with orchestrator and pipeline architecture
        self.job_processor = RefactoredKnowledgeJobEventProcessor()
        self.feature_flags = get_feature_flags()

        logger.info("JobEventListener initialized with NEW refactored architecture")
        logger.info(f"Feature flags: {self.feature_flags.__dict__}")

    async def handle_event(self, event_payload: Dict[str, Any]) -> bool:
        """
        Handle a job execution event using the NEW refactored architecture.

        Args:
            event_payload: The job event data to process

        Returns:
            True if event was processed successfully, False otherwise
        """
        try:
            logger.debug(f"Handling job event with NEW architecture: {event_payload}")

            # Extract event information
            event_type = event_payload.get("event_type")
            job_id = event_payload.get("job_id")
            user_id = event_payload.get("user_id")

            logger.info(
                f"[NEW ARCHITECTURE] Processing {event_type} for job {job_id} by user {user_id}"
            )

            # Handle different event types
            if event_type == EventTypes.KNOWLEDGE_JOB_ACTION_REQUESTED:
                logger.info(f"[NEW ARCHITECTURE] Delegating to RefactoredKnowledgeJobEventProcessor")
                return await self.job_processor.process_job_action_requested(
                    event_payload
                )
            elif event_type == "job_execution_requested":
                # Handle legacy event type for backward compatibility
                logger.info(f"[NEW ARCHITECTURE] Processing legacy event type: {event_type}")
                return await self.job_processor.process_job_action_requested(
                    event_payload
                )
            else:
                logger.error(f"Unknown job event type: {event_type}")
                return False

        except Exception as e:
            logger.error(f"Error handling job event with NEW architecture: {e}")
            return False


# Global instance for easy access
_job_event_listener: JobEventListener = None


def get_job_event_listener() -> JobEventListener:
    """Get the global job event listener instance."""
    global _job_event_listener

    if _job_event_listener is None:
        _job_event_listener = JobEventListener()

    return _job_event_listener


async def start_job_event_listener() -> None:
    """
    Convenience function to start the job event listener.
    """
    listener = get_job_event_listener()
    await listener.start_listening()
