"""
Refactored Job Event Processor (New Architecture).

This module contains the refactored job event processor using the new
modular, pipeline-based architecture. This is significantly simpler and
cleaner than the old 367-line monolithic processor.
"""

import traceback
from typing import Any, Dict, Optional

from loguru import logger

from src.domain.events.job_events import JobActionRequested
from src.domain.knowledge.knowledge_job import JobStatus
from src.processors.knowledge_job.container import create_job_orchestrator
from src.processors.knowledge_job.orchestration.cancellation_manager import (
    JobCancelledException,
    get_cancellation_manager,
)
from src.services.knowledge import get_knowledge_job_service
from src.services.knowledge.job_timeline_service import get_job_timeline_service


class RefactoredKnowledgeJobEventProcessor:
    """
    Refactored processor for knowledge job events using the new architecture.

    This processor is much simpler than the old one - it just:
    1. Validates the job
    2. Delegates to the orchestrator
    3. Handles cancellation requests

    All the complex logic is now in modular, testable pipeline steps.
    """

    def __init__(self):
        """Initialize the refactored job event processor."""
        self.job_service = get_knowledge_job_service()
        self.timeline_service = get_job_timeline_service()
        self.cancellation_manager = get_cancellation_manager()
        # Note: orchestrator will be created per job with dynamic pipeline
        self.orchestrator = None

        logger.info("RefactoredKnowledgeJobEventProcessor initialized")

    async def process_job_action_requested(
        self, event_payload: Dict[str, Any]
    ) -> bool:
        """
        Process a job action requested event (execute or cancel).

        Args:
            event_payload: The job action event data

        Returns:
            True if event was processed successfully, False otherwise
        """
        try:
            # Parse the event
            event = JobActionRequested.model_validate(event_payload)

            # Check if this is a cancellation request
            execution_context = event.execution_context or {}
            action = execution_context.get("action", "execute")

            if action == "cancel":
                logger.info(f"Processing job cancellation request for job {event.job_id}")
                return await self._handle_job_cancellation(
                    event.job_id, event.user_id, execution_context
                )

            # Execute the job
            logger.info(f"Processing job execution request for job {event.job_id}")
            return await self._execute_job(event)

        except Exception as e:
            logger.error(f"Error processing job action request: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def _execute_job(self, event: JobActionRequested) -> bool:
        """
        Execute a knowledge processing job.

        Args:
            event: The job action event

        Returns:
            True if successful, False otherwise
        """
        try:
            # 1. Get the job details
            knowledge_job = self.job_service.get_knowledge_job(
                event.job_id, event.user_id
            )
            if not knowledge_job:
                logger.error(f"Job {event.job_id} not found for user {event.user_id}")
                return False

            # 2. Get current job status from timeline
            latest_timeline = self.timeline_service.get_latest_timeline_entry(
                event.job_id, event.user_id
            )
            current_status = (
                latest_timeline.status if latest_timeline else JobStatus.CREATED
            )

            # 3. Validate job is in a valid state for execution
            if current_status not in [
                JobStatus.CREATED,
                JobStatus.PENDING,
                JobStatus.FAILED,
                JobStatus.COMPLETED,
                JobStatus.CANCELLED,
            ]:
                logger.warning(
                    f"Job {event.job_id} is in invalid state for execution: {current_status}"
                )
                return False

            # 4. Get the knowledge source configuration
            knowledge_source_config = (
                self.job_service.knowledge_source_service.get_knowledge_source_config(
                    knowledge_job.knowledge_source_config_id, event.user_id
                )
            )
            if not knowledge_source_config:
                logger.error(
                    f"Knowledge source config {knowledge_job.knowledge_source_config_id} not found"
                )
                return False

            # 5. CRITICAL: Create timeline with RUNNING status IMMEDIATELY
            # This prevents race condition where user can start same job multiple times
            # If this timeline creation fails, we should NOT proceed with execution
            logger.info(f"Creating RUNNING timeline entry for job {event.job_id}")
            try:
                timeline_entry = self.timeline_service.start_job_execution(
                    job_id=event.job_id,
                    user_id=event.user_id,
                    execution_context=event.execution_context,
                    triggered_by="job_execution"
                )
                if not timeline_entry:
                    logger.error(f"Failed to create RUNNING timeline entry for job {event.job_id}")
                    return False

                logger.info(
                    f"Created timeline entry {timeline_entry.id} with status RUNNING for job {event.job_id}"
                )
            except Exception as timeline_error:
                logger.error(f"Error creating timeline for job {event.job_id}: {timeline_error}")
                return False

            # 6. Create orchestrator with dynamic pipeline based on source config
            # This allows different pipelines for web scraping vs local files
            logger.info(
                f"Creating orchestrator for job {event.job_id} with "
                f"content_source_type={knowledge_source_config.content_source_type}, "
                f"scraping_mode={knowledge_source_config.scraping_mode}"
            )
            orchestrator = create_job_orchestrator(
                enable_rollback=False,
                knowledge_source_config=knowledge_source_config,
            )

            # 7. Execute the job through the orchestrator
            # The orchestrator handles:
            # - Pipeline execution (with correct steps for the source type)
            # - Timeline management
            # - Error handling
            # - Progress tracking
            logger.info(f"Delegating job {event.job_id} to orchestrator")

            results = await orchestrator.execute_job(
                knowledge_job=knowledge_job,
                knowledge_source_config=knowledge_source_config,
                status_callback=self._create_status_callback(event.job_id),
            )

            logger.info(
                f"Job {event.job_id} execution completed: "
                f"{results.get('total_documents', 0)} docs, "
                f"{results.get('total_chunks', 0)} chunks"
            )

            return results.get("success", False)

        except JobCancelledException as e:
            logger.warning(f"Job {event.job_id} was cancelled: {e}")
            return False

        except Exception as e:
            logger.error(f"Error executing job {event.job_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def _handle_job_cancellation(
        self, job_id: str, user_id: str, execution_context: Dict[str, Any]
    ) -> bool:
        """
        Handle job cancellation.

        Args:
            job_id: The job ID to cancel
            user_id: The user ID
            execution_context: The execution context with cancellation details

        Returns:
            True if cancellation was processed successfully, False otherwise
        """
        try:
            cancellation_reason = execution_context.get(
                "cancellation_reason", "User requested cancellation"
            )

            logger.info(f"Requesting cancellation for job {job_id}")

            # Signal cancellation through the cancellation manager
            # This will cause any running pipeline steps to stop
            self.cancellation_manager.request_cancellation(
                job_id, reason=cancellation_reason
            )

            # Create CANCELLED timeline entry (status is tracked in timeline, not job object)
            from datetime import datetime
            from src.domain.knowledge.job_timeline import JobTimelineCreate

            logger.info(f"Creating CANCELLED timeline entry for job {job_id}")

            timeline_data = JobTimelineCreate(
                job_id=job_id,
                user_id=user_id,
                status=JobStatus.CANCELLED,
                completed_at=datetime.utcnow().isoformat(),
                error_message=cancellation_reason,
                triggered_by="user_cancellation",
            )

            # Create timeline entry
            timeline_id = self.timeline_service.create_timeline_entry(timeline_data, user_id)
            if timeline_id:
                logger.info(f"Job {job_id} cancelled successfully - timeline entry {timeline_id} created")
            else:
                logger.error(f"Failed to create cancellation timeline entry for job {job_id}")

            logger.info(f"Cancellation completed for job {job_id}")
            return True

        except Exception as e:
            logger.error(f"Error processing job cancellation: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _create_status_callback(self, job_id: str):
        """
        Create a status callback for the job.

        Args:
            job_id: The job ID

        Returns:
            Status callback function
        """

        def status_callback(message: str, batch_info: Optional[Dict[str, Any]] = None):
            """Log status updates."""
            if batch_info:
                logger.debug(
                    f"Job {job_id} progress: {message} - {batch_info}"
                )
            else:
                logger.debug(f"Job {job_id} status: {message}")

        return status_callback


# Global instance for easy access
_refactored_knowledge_job_event_processor: Optional[
    RefactoredKnowledgeJobEventProcessor
] = None


def get_refactored_knowledge_job_event_processor() -> RefactoredKnowledgeJobEventProcessor:
    """Get the global refactored knowledge job event processor instance."""
    global _refactored_knowledge_job_event_processor

    if _refactored_knowledge_job_event_processor is None:
        _refactored_knowledge_job_event_processor = (
            RefactoredKnowledgeJobEventProcessor()
        )

    return _refactored_knowledge_job_event_processor
