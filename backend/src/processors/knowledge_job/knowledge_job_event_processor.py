"""
Job Event Processor.

This module contains the actual processing logic for job-related events,
separated from the event listening infrastructure.

MIGRATION NOTE: This processor now supports routing to both old and new architectures
based on feature flags. See feature_flags.py for configuration.
"""

import asyncio
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from loguru import logger

from src.domain.events.job_events import JobActionRequested
from src.domain.knowledge.knowledge_job import JobStatus
from src.services.knowledge import get_knowledge_job_service
from src.services.knowledge.job_timeline_service import get_job_timeline_service

from .feature_flags import get_feature_flags
from .knowledge_job_processor import get_knowledge_job_processor


class KnowledgeJobEventProcessor:
    """
    Processor for knowledge job-related events.

    This processor now supports both old and new architectures,
    with feature flags controlling which one is used.
    """

    def __init__(self):
        """Initialize the job event processor."""
        self.job_service = get_knowledge_job_service()
        self.job_processor = get_knowledge_job_processor()
        self.timeline_service = get_job_timeline_service()
        self.feature_flags = get_feature_flags()

        # Lazy-load new processor to avoid circular imports
        self._new_processor = None

        logger.info(
            f"KnowledgeJobEventProcessor initialized "
            f"(new_architecture_enabled: {self.feature_flags.use_new_architecture})"
        )

    def _get_new_processor(self):
        """Lazy load the new processor."""
        if self._new_processor is None:
            from .refactored_knowledge_job_event_processor import (
                get_refactored_knowledge_job_event_processor,
            )
            self._new_processor = get_refactored_knowledge_job_event_processor()
        return self._new_processor

    async def process_job_action_requested(self, event_payload: Dict[str, Any]) -> bool:
        """
        Process a job action requested event (execute or cancel).

        This method routes to either old or new architecture based on feature flags.

        Args:
            event_payload: The job action event data

        Returns:
            True if event was processed successfully, False otherwise
        """
        try:
            # Parse the event to get job_id
            event = JobActionRequested.model_validate(event_payload)

            # Check if we should use new architecture
            use_new = self.feature_flags.should_use_new_architecture(event.job_id)

            if use_new:
                logger.info(
                    f"Using NEW architecture for job {event.job_id} "
                    f"(feature flag enabled)"
                )
                return await self._get_new_processor().process_job_action_requested(
                    event_payload
                )
            else:
                logger.info(
                    f"Using OLD architecture for job {event.job_id} "
                    f"(feature flag disabled)"
                )
                return await self._process_with_old_architecture(event_payload)

        except Exception as e:
            logger.error(f"Error in routing logic: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Fall back to old architecture on routing errors
            return await self._process_with_old_architecture(event_payload)

    async def _process_with_old_architecture(self, event_payload: Dict[str, Any]) -> bool:
        """
        Process event using the OLD architecture (original implementation).

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
                logger.info(
                    f"Processing job cancellation request for job {event.job_id}"
                )
                return await self._handle_job_cancellation(
                    event.job_id, event.user_id, execution_context
                )

            logger.debug(f"Processing job execution request for job {event.job_id}")

            # 1. Get the job details from the database
            knowledge_job = self.job_service.get_knowledge_job(
                event.job_id, event.user_id
            )
            if not knowledge_job:
                logger.error(f"Job {event.job_id} not found for user {event.user_id}")
                return False

            # 2. Get the current job status from timeline
            latest_timeline = self.timeline_service.get_latest_timeline_entry(
                event.job_id, event.user_id
            )
            current_status = (
                latest_timeline.status if latest_timeline else JobStatus.CREATED
            )

            # 3. Validate the job is in a valid state for execution
            if current_status not in [
                JobStatus.CREATED,
                JobStatus.PENDING,
                JobStatus.FAILED,
                JobStatus.COMPLETED,
                JobStatus.CANCELLED,
            ]:
                logger.debug(
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

            # 5. Create timeline entry for this execution
            try:
                timeline_entry = self.timeline_service.start_job_execution(
                    job_id=event.job_id,
                    user_id=event.user_id,
                    execution_context=event.execution_context,
                    triggered_by=(
                        event.execution_context.get("source", "unknown")
                        if event.execution_context
                        else "unknown"
                    ),
                )
                if timeline_entry:
                    logger.info(
                        f"Created timeline entry {timeline_entry.id} for job {event.job_id}"
                    )
                else:
                    logger.error(
                        f"Failed to create timeline entry for job {event.job_id}"
                    )
                    return False
            except Exception as timeline_error:
                logger.error(f"Error creating timeline entry: {timeline_error}")
                return False

            # 6. Process the job using our dedicated job processor
            try:
                # Enhanced status callback that emits timeline events
                def enhanced_status_callback(
                    message: str, batch_info: Optional[Dict[str, Any]] = None
                ):
                    logger.debug(f"Job {event.job_id}: {message}")

                    if batch_info:
                        # Update timeline record directly with batch progress
                        try:
                            from src.domain.knowledge.job_timeline import (
                                JobTimelineUpdate,
                            )

                            timeline_update = JobTimelineUpdate(
                                documents_processed=batch_info.get(
                                    "total_processed", 0
                                ),
                                chunks_created=batch_info.get("total_chunks", 0),
                                processing_time_seconds=batch_info.get(
                                    "processing_time", 0.0
                                ),
                            )

                            updated_timeline = (
                                self.timeline_service.update_timeline_entry(
                                    timeline_id=timeline_entry.id,
                                    user_id=event.user_id,
                                    update_data=timeline_update,
                                )
                            )

                            if updated_timeline:
                                logger.debug(
                                    f"Updated timeline {timeline_entry.id} with batch progress: {batch_info.get('total_processed', 0)} docs, {batch_info.get('total_chunks', 0)} chunks"
                                )
                            else:
                                logger.error(
                                    f"Failed to update timeline {timeline_entry.id} with batch progress"
                                )

                        except Exception as timeline_update_error:
                            logger.error(
                                f"Error updating timeline with batch progress: {timeline_update_error}"
                            )

                # Process the job
                results = await self.job_processor.process_job(
                    knowledge_job=knowledge_job,
                    knowledge_source_config=knowledge_source_config,
                    status_callback=enhanced_status_callback,
                )

                logger.debug(f"Job {event.job_id} processing results: {results}")

                # 7. Complete timeline entry with statistics
                try:
                    completed_timeline = self.timeline_service.complete_job_execution(
                        timeline_id=timeline_entry.id,
                        user_id=event.user_id,
                        documents_processed=results.get("total_documents", 0),
                        chunks_created=results.get("total_chunks", 0),
                        processing_time_seconds=results.get(
                            "processing_time_seconds", 0.0
                        ),
                    )
                    if completed_timeline:
                        logger.info(
                            f"Timeline entry {timeline_entry.id} completed successfully"
                        )
                    else:
                        logger.error(
                            f"Failed to complete timeline entry {timeline_entry.id}"
                        )
                except Exception as timeline_completion_error:
                    logger.error(
                        f"Error completing timeline entry: {timeline_completion_error}"
                    )

                # Timeline status is already updated to completed via complete_job_execution above

                logger.debug(f"Job {event.job_id} completed successfully")

            except Exception as processing_error:
                logger.error(f"Error during job processing: {processing_error}")
                logger.error(f"Traceback: {traceback.format_exc()}")

                # Update timeline entry to failed
                try:
                    if "timeline_entry" in locals():
                        failed_timeline = self.timeline_service.fail_job_execution(
                            timeline_id=timeline_entry.id,
                            user_id=event.user_id,
                            error_message=str(processing_error),
                            error_traceback=traceback.format_exc(),
                        )
                        if failed_timeline:
                            logger.info(
                                f"Timeline entry {timeline_entry.id} marked as failed"
                            )
                        else:
                            logger.error(
                                f"Failed to mark timeline entry {timeline_entry.id} as failed"
                            )
                except Exception as timeline_failure_error:
                    logger.error(
                        f"Error updating timeline entry to FAILED: {timeline_failure_error}"
                    )
                    logger.error(
                        f"Timeline failure traceback: {traceback.format_exc()}"
                    )

                return False

            logger.debug(
                f"Job execution request processed successfully for job {event.job_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error processing job execution request: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Try to create a failed timeline entry if we have the job_id
            try:
                if "event" in locals():
                    # Create a new timeline entry for the failure
                    from src.domain.knowledge.job_timeline import JobTimelineCreate

                    failed_timeline_data = JobTimelineCreate(
                        job_id=event.job_id,
                        user_id=event.user_id,
                        status=JobStatus.FAILED,
                        started_at=datetime.utcnow(),
                        completed_at=datetime.utcnow(),
                        error_message=str(e),
                        error_traceback=traceback.format_exc(),
                        triggered_by="error_handler",
                    )
                    failed_timeline = self.timeline_service.create_timeline_entry(
                        failed_timeline_data, event.user_id
                    )
                    if failed_timeline:
                        logger.info(
                            f"Successfully created failed timeline entry for job {event.job_id}"
                        )
                    else:
                        logger.error(
                            f"Failed to create failed timeline entry for job {event.job_id}"
                        )
                else:
                    logger.error(
                        "Cannot create failed timeline entry - event not available in locals"
                    )
            except Exception as timeline_error:
                logger.error(
                    f"Error creating failed timeline entry (outer exception): {timeline_error}"
                )
                logger.error(f"Timeline error traceback: {traceback.format_exc()}")

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

            logger.info(f"Cancelling job {job_id} for user {user_id}")

            # Signal the job processor to stop if it's currently running this job
            if (
                hasattr(self.job_processor, "_current_job_id")
                and self.job_processor._current_job_id == job_id
            ):
                logger.info(f"Signaling job processor to stop job {job_id}")
                self.job_processor._cancellation_requested = True
            else:
                logger.info(
                    f"Job {job_id} is not currently running, creating cancellation timeline only"
                )

            # Create a cancelled timeline entry
            from datetime import datetime

            from src.domain.knowledge.job_timeline import JobTimelineCreate

            timeline_data = JobTimelineCreate(
                job_id=job_id,
                user_id=user_id,
                status=JobStatus.CANCELLED,
                completed_at=datetime.utcnow().isoformat(),
                error_message=cancellation_reason,
                triggered_by="user_cancellation",
            )

            # Create timeline entry
            timeline_id = self.timeline_service.create_timeline_entry(
                timeline_data, user_id
            )
            if not timeline_id:
                logger.error(
                    f"Failed to create cancellation timeline entry for job {job_id}"
                )
                return False

            logger.info(f"Job {job_id} cancelled successfully by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error processing job cancellation: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False


# Global instance for easy access
_knowledge_job_event_processor: Optional[KnowledgeJobEventProcessor] = None


def get_knowledge_job_event_processor() -> KnowledgeJobEventProcessor:
    """Get the global knowledge job event processor instance."""
    global _knowledge_job_event_processor

    if _knowledge_job_event_processor is None:
        _knowledge_job_event_processor = KnowledgeJobEventProcessor()

    return _knowledge_job_event_processor
