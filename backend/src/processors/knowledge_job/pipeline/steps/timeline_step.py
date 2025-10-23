"""
Timeline Recording Step.

This step records job execution progress in the timeline for tracking and audit purposes.
"""

import time
from datetime import datetime

from loguru import logger

from src.processors.knowledge_job.orchestration.job_context import JobContext
from src.processors.knowledge_job.pipeline.base import PipelineStep, StepResult


class TimelineRecordingStep(PipelineStep):
    """
    Pipeline step for recording execution progress in the job timeline.

    This step creates and updates timeline entries to track job execution,
    providing visibility into job progress and history.
    """

    def __init__(self, timeline_service=None):
        """
        Initialize the timeline recording step.

        Args:
            timeline_service: Optional timeline service (injected for testability)
        """
        super().__init__(name="TimelineRecording")
        self.timeline_service = timeline_service

    async def validate(self, context: JobContext) -> bool:
        """Validate that we have execution stats to record."""
        # Timeline recording is always valid - we record even empty executions
        return True

    async def execute(self, context: JobContext) -> StepResult:
        """
        Record job execution progress in the timeline.

        Args:
            context: Job execution context

        Returns:
            StepResult indicating success or failure
        """
        try:
            logger.info(
                f"Recording timeline entry for job {context.get_job_id()}"
            )

            start_time = time.time()

            # Get or create timeline service
            if not self.timeline_service:
                from src.services.knowledge.job_timeline_service import (
                    get_job_timeline_service,
                )

                timeline_service = get_job_timeline_service()
            else:
                timeline_service = self.timeline_service

            # If we don't have a timeline entry yet, create one
            if not context.timeline_id:
                logger.info(
                    f"Creating timeline entry for job {context.get_job_id()}"
                )

                timeline_entry = timeline_service.start_job_execution(
                    job_id=context.get_job_id(),
                    user_id=context.get_user_id(),
                    execution_context=context.execution_context,
                    triggered_by=context.execution_context.get("source", "unknown")
                    if context.execution_context
                    else "unknown",
                )

                if timeline_entry:
                    context.timeline_id = timeline_entry.id
                    context.started_at = timeline_entry.started_at
                    logger.info(
                        f"Created timeline entry {timeline_entry.id} for job {context.get_job_id()}"
                    )
                else:
                    raise Exception("Failed to create timeline entry")

            # Update timeline with final statistics
            from src.domain.knowledge.job_timeline import JobTimelineUpdate

            # Calculate total processing time
            if context.started_at:
                processing_time = (
                    datetime.utcnow() - context.started_at
                ).total_seconds()
            else:
                processing_time = context.stats.get("processing_time_seconds", 0.0)

            timeline_update = JobTimelineUpdate(
                documents_processed=context.stats.get("total_documents", 0),
                chunks_created=context.stats.get("total_chunks", 0),
                processing_time_seconds=processing_time,
            )

            updated_timeline = timeline_service.update_timeline_entry(
                timeline_id=context.timeline_id,
                user_id=context.get_user_id(),
                update_data=timeline_update,
            )

            if updated_timeline:
                logger.info(
                    f"Updated timeline {context.timeline_id} with final stats: "
                    f"{context.stats.get('total_documents', 0)} docs, "
                    f"{context.stats.get('total_chunks', 0)} chunks"
                )
            else:
                logger.warning(
                    f"Failed to update timeline {context.timeline_id} with final stats"
                )

            # Complete the timeline entry
            completed_timeline = timeline_service.complete_job_execution(
                timeline_id=context.timeline_id,
                user_id=context.get_user_id(),
                documents_processed=context.stats.get("total_documents", 0),
                chunks_created=context.stats.get("total_chunks", 0),
                processing_time_seconds=processing_time,
            )

            if completed_timeline:
                context.completed_at = completed_timeline.completed_at
                logger.info(
                    f"Timeline entry {context.timeline_id} marked as completed"
                )
            else:
                logger.warning(
                    f"Failed to complete timeline entry {context.timeline_id}"
                )

            execution_time = time.time() - start_time

            return StepResult.success_result(
                data={
                    "timeline_id": context.timeline_id,
                    "timeline_recording_time_seconds": execution_time,
                    "documents_processed": context.stats.get("total_documents", 0),
                    "chunks_created": context.stats.get("total_chunks", 0),
                }
            )

        except Exception as e:
            logger.error(f"Timeline recording failed: {e}")
            context.add_error(f"Timeline error: {e}")

            # Try to create a failed timeline entry
            try:
                if not self.timeline_service:
                    from src.services.knowledge.job_timeline_service import (
                        get_job_timeline_service,
                    )

                    timeline_service = get_job_timeline_service()
                else:
                    timeline_service = self.timeline_service

                from src.domain.knowledge.job_timeline import JobTimelineCreate
                from src.domain.knowledge.knowledge_job import JobStatus

                failed_timeline_data = JobTimelineCreate(
                    job_id=context.get_job_id(),
                    user_id=context.get_user_id(),
                    status=JobStatus.FAILED,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error_message=str(e),
                    triggered_by="timeline_error",
                )

                timeline_service.create_timeline_entry(
                    failed_timeline_data, context.get_user_id()
                )

            except Exception as timeline_error:
                logger.error(f"Failed to create error timeline entry: {timeline_error}")

            return StepResult.failure_result(error=f"Timeline recording failed: {e}")
