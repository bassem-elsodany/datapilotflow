"""
Job Orchestrator.

This module implements the main orchestrator that coordinates job execution
through the pipeline, managing state transitions, error recovery, and progress tracking.
"""

import time
import traceback
from typing import Any, Dict, Optional

from loguru import logger

from datapilotflow.domain.knowledge.knowledge_job import KnowledgeJob, JobStatus
from datapilotflow.domain.knowledge.knowledge_source_config import KnowledgeSourceConfig
from datapilotflow.processors.knowledge_job.orchestration.cancellation_manager import (
    CancellationManager,
    JobCancelledException,
    get_cancellation_manager,
)
from datapilotflow.processors.knowledge_job.orchestration.job_context import JobContext
from datapilotflow.processors.knowledge_job.pipeline.pipeline import JobPipeline
from datapilotflow.processors.knowledge_job.pipeline.base import PipelineResult


class JobOrchestrator:
    """
    Orchestrates job execution through a pipeline of steps.

    This class is the main entry point for job execution. It:
    - Creates the execution context
    - Manages the pipeline execution
    - Handles errors and cancellation
    - Tracks progress and emits status updates
    - Records timeline events
    """

    def __init__(
        self,
        pipeline: JobPipeline,
        cancellation_manager: Optional[CancellationManager] = None,
    ):
        """
        Initialize the job orchestrator.

        Args:
            pipeline: The job processing pipeline
            cancellation_manager: Optional cancellation manager
        """
        self.pipeline = pipeline
        self.cancellation_manager = cancellation_manager or get_cancellation_manager()

    async def execute_job(
        self,
        knowledge_job: KnowledgeJob,
        knowledge_source_config: KnowledgeSourceConfig,
        status_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute a knowledge processing job.

        For local files, uses batch-wise execution (Extract→Chunk→Embed→Store per batch).
        For web scraping, uses traditional pipeline execution (Extract all → Chunk all → etc).

        Args:
            knowledge_job: The job to execute
            knowledge_source_config: The knowledge source configuration
            status_callback: Optional callback for status updates

        Returns:
            Dictionary containing execution results and statistics

        Raises:
            JobCancelledException: If the job is cancelled
            Exception: If job execution fails
        """
        from datapilotflow.domain.knowledge.knowledge_source_config import ContentSourceType

        # Check if batch_size is configured - use batch-wise execution
        # This allows for memory-efficient processing and progress tracking
        if knowledge_job.batch_size and knowledge_job.batch_size > 0:
            logger.info(
                f"Using batch-wise execution for job {knowledge_job.id} "
                f"(batch_size: {knowledge_job.batch_size}, source: {knowledge_source_config.content_source_type})"
            )
            return await self._execute_job_batch_wise(
                knowledge_job, knowledge_source_config, status_callback
            )

        # Otherwise use traditional pipeline execution (all docs at once)
        logger.info(f"Using traditional execution for job {knowledge_job.id}")
        return await self._execute_job_traditional(
            knowledge_job, knowledge_source_config, status_callback
        )

    async def _execute_job_traditional(
        self,
        knowledge_job: KnowledgeJob,
        knowledge_source_config: KnowledgeSourceConfig,
        status_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute job using traditional pipeline (all data through all steps sequentially).

        Args:
            knowledge_job: The job to execute
            knowledge_source_config: The knowledge source configuration
            status_callback: Optional callback for status updates

        Returns:
            Dictionary containing execution results and statistics
        """
        from datapilotflow.services.notification.job_notification_helper import (
            emit_job_started_notification,
            emit_job_completed_notification,
            emit_job_failed_notification,
            emit_job_cancelled_notification
        )

        job_id = knowledge_job.id
        user_id = knowledge_job.user_id
        job_name = knowledge_source_config.name

        logger.info(f"Starting traditional pipeline orchestration for job {job_id}")

        # Clear any previous cancellation state for this job
        self.cancellation_manager.clear_cancellation(job_id)

        # Create execution context
        context = JobContext(
            job=knowledge_job,
            knowledge_source_config=knowledge_source_config,
            user_id=user_id,
            status_callback=status_callback,
        )

        start_time = time.time()

        try:
            # Emit job started notification
            await emit_job_started_notification(
                job_id=job_id,
                user_id=user_id,
                job_name=job_name,
                content_source_type=knowledge_source_config.content_source_type.value
            )

            # Execute the pipeline
            result = await self.pipeline.execute(context)

            total_time = time.time() - start_time

            # Build result dictionary
            job_result = self._build_job_result(result, context, total_time)

            if result.success:
                logger.info(
                    f"Job {job_id} completed successfully in {total_time:.2f}s: "
                    f"{context.stats.get('total_documents', 0)} docs, "
                    f"{context.stats.get('total_chunks', 0)} chunks"
                )

                # Emit job completed notification
                await emit_job_completed_notification(
                    job_id=job_id,
                    user_id=user_id,
                    job_name=job_name,
                    total_documents=context.stats.get('total_documents', 0),
                    total_chunks=context.stats.get('total_chunks', 0),
                    total_vectors=context.stats.get('total_vectors', 0),
                    execution_time=total_time
                )
            else:
                logger.error(
                    f"Job {job_id} failed at step '{result.failed_step}' "
                    f"after {total_time:.2f}s"
                )

                # Emit failure notification
                await emit_job_failed_notification(
                    job_id=job_id,
                    user_id=user_id,
                    job_name=job_name,
                    error_message=result.failed_step or "Unknown error",
                    documents_processed=context.stats.get('total_documents', 0),
                    chunks_created=context.stats.get('total_chunks', 0)
                )

                # Handle failure timeline recording if not already handled
                await self._handle_job_failure(context, result)

            return job_result

        except JobCancelledException as e:
            logger.warning(f"Job {job_id} was cancelled: {e}")

            # Emit cancellation notification
            await emit_job_cancelled_notification(
                job_id=job_id,
                user_id=user_id,
                job_name=job_name,
                cancellation_reason=str(e),
                documents_processed=context.stats.get('total_documents', 0) if context.stats else None,
                chunks_created=context.stats.get('total_chunks', 0) if context.stats else None
            )

            # Record cancellation in timeline
            await self._handle_job_cancellation(context, str(e))

            # Re-raise to be handled by event processor
            raise

        except Exception as e:
            logger.error(f"Unexpected error during job orchestration: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Emit failure notification
            await emit_job_failed_notification(
                job_id=job_id,
                user_id=user_id,
                job_name=job_name,
                error_message=str(e),
                documents_processed=context.stats.get('total_documents', 0) if context.stats else None,
                chunks_created=context.stats.get('total_chunks', 0) if context.stats else None
            )

            # Record failure in timeline
            await self._handle_job_error(context, e)

            # Re-raise to be handled by event processor
            raise

        finally:
            # Clear cancellation state
            self.cancellation_manager.clear_cancellation(job_id)

    def _build_job_result(
        self, pipeline_result: PipelineResult, context: JobContext, total_time: float
    ) -> Dict[str, Any]:
        """
        Build the job result dictionary from pipeline result and context.

        Args:
            pipeline_result: Result from pipeline execution
            context: Job execution context
            total_time: Total execution time in seconds

        Returns:
            Dictionary with job execution results
        """
        return {
            "success": pipeline_result.success,
            "total_documents": context.stats.get("total_documents", 0),
            "total_chunks": context.stats.get("total_chunks", 0),
            "total_vectors": context.stats.get("total_vectors", 0),
            "processing_time_seconds": total_time,
            "stats": context.stats,
            "errors": context.errors,
            "pipeline_result": {
                "completed_steps": pipeline_result.completed_steps,
                "total_steps": len(self.pipeline.steps),
                "failed_step": pipeline_result.failed_step,
                "step_results": [
                    {
                        "step_name": result.metadata.get("step_name", "unknown"),
                        "success": result.success,
                        "execution_time": result.execution_time_seconds,
                    }
                    for result in pipeline_result.step_results
                ],
            },
            "timeline_id": context.timeline_id,
        }

    async def _handle_job_failure(
        self, context: JobContext, pipeline_result: PipelineResult
    ) -> None:
        """
        Handle job failure by recording in timeline.

        Args:
            context: Job execution context
            pipeline_result: Pipeline execution result
        """
        try:
            # Check if a timeline entry exists
            if not context.timeline_id:
                # Create a timeline entry for the failure
                from datapilotflow.services.knowledge.job_timeline_service import (
                    get_job_timeline_service,
                )

                timeline_service = get_job_timeline_service()

                timeline_entry = timeline_service.start_job_execution(
                    job_id=context.get_job_id(),
                    user_id=context.get_user_id(),
                    execution_context=context.execution_context,
                    triggered_by="job_failure",
                )

                if timeline_entry:
                    context.timeline_id = timeline_entry.id

            # Mark as failed
            if context.timeline_id:
                from datapilotflow.services.knowledge.job_timeline_service import (
                    get_job_timeline_service,
                )

                timeline_service = get_job_timeline_service()

                # Get error from failed step
                error_message = pipeline_result.failed_step or "Unknown error"
                error_traceback = ""

                for result in pipeline_result.step_results:
                    if not result.success and result.error:
                        error_message = result.error
                        error_traceback = result.error_traceback or ""
                        break

                timeline_service.fail_job_execution(
                    timeline_id=context.timeline_id,
                    user_id=context.get_user_id(),
                    error_message=error_message,
                    error_traceback=error_traceback,
                )

                logger.info(
                    f"Marked timeline {context.timeline_id} as failed "
                    f"for job {context.get_job_id()}"
                )

        except Exception as e:
            logger.error(f"Error handling job failure timeline: {e}")

    async def _handle_job_cancellation(self, context: JobContext, reason: str) -> None:
        """
        Handle job cancellation by recording in timeline.

        Args:
            context: Job execution context
            reason: Cancellation reason
        """
        try:
            from datetime import datetime

            from datapilotflow.domain.knowledge.job_timeline import JobTimelineCreate
            from datapilotflow.domain.knowledge.knowledge_job import JobStatus
            from datapilotflow.services.knowledge.job_timeline_service import (
                get_job_timeline_service,
            )

            timeline_service = get_job_timeline_service()

            timeline_data = JobTimelineCreate(
                job_id=context.get_job_id(),
                user_id=context.get_user_id(),
                status=JobStatus.CANCELLED,
                completed_at=datetime.utcnow().isoformat(),
                error_message=reason,
                triggered_by="cancellation",
            )

            timeline_service.create_timeline_entry(timeline_data, context.get_user_id())

            logger.info(
                f"Created cancellation timeline entry for job {context.get_job_id()}"
            )

        except Exception as e:
            logger.error(f"Error handling job cancellation timeline: {e}")

    async def _handle_job_error(self, context: JobContext, error: Exception) -> None:
        """
        Handle unexpected job error by recording in timeline.

        Args:
            context: Job execution context
            error: The exception that occurred
        """
        try:
            from datetime import datetime

            from datapilotflow.domain.knowledge.job_timeline import JobTimelineCreate
            from datapilotflow.domain.knowledge.knowledge_job import JobStatus
            from datapilotflow.services.knowledge.job_timeline_service import (
                get_job_timeline_service,
            )

            timeline_service = get_job_timeline_service()

            timeline_data = JobTimelineCreate(
                job_id=context.get_job_id(),
                user_id=context.get_user_id(),
                status=JobStatus.FAILED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                error_message=str(error),
                error_traceback=traceback.format_exc(),
                triggered_by="error_handler",
            )

            timeline_service.create_timeline_entry(timeline_data, context.get_user_id())

            logger.info(
                f"Created error timeline entry for job {context.get_job_id()}"
            )

        except Exception as e:
            logger.error(f"Error handling job error timeline: {e}")

    async def _execute_job_batch_wise(
        self,
        knowledge_job: KnowledgeJob,
        knowledge_source_config: KnowledgeSourceConfig,
        status_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute job batch-wise: each batch goes through all pipeline steps before next batch.

        This is used for local files to avoid loading all files into memory.

        Flow: Batch1(Extract→Chunk→Embed→Store) → Batch2(Extract→Chunk→Embed→Store) → ...

        Args:
            knowledge_job: The job to execute
            knowledge_source_config: The knowledge source configuration
            status_callback: Optional callback for status updates

        Returns:
            Dictionary containing execution results and statistics
        """
        from datapilotflow.services.notification.job_notification_helper import (
            emit_job_started_notification,
            emit_job_progress_notification,
            emit_job_completed_notification,
            emit_job_failed_notification,
            emit_job_cancelled_notification
        )

        job_id = knowledge_job.id
        user_id = knowledge_job.user_id
        job_name = knowledge_source_config.name

        logger.info(f"Starting batch-wise pipeline orchestration for job {job_id}")

        # Clear any previous cancellation state
        self.cancellation_manager.clear_cancellation(job_id)

        start_time = time.time()

        # Accumulators for all batches
        total_documents = 0
        total_chunks = 0
        total_vectors = 0
        batch_count = 0

        # Timeline ID for tracking
        timeline_id = None

        # Flag to track if collection has been cleared (once per job)
        collection_cleared = False

        try:
            # Get the extraction step (should be FileExtractionStep)
            extraction_step = self.pipeline.steps[0]

            # Get other steps
            chunking_step = self.pipeline.steps[1]
            embedding_step = self.pipeline.steps[2]
            storage_step = self.pipeline.steps[3]
            timeline_step = self.pipeline.steps[4]

            # Create a context for extraction to get the generator
            extraction_context = JobContext(
                job=knowledge_job,
                knowledge_source_config=knowledge_source_config,
                user_id=user_id,
                status_callback=status_callback,
            )

            # Get the latest timeline entry (should already exist from event processor)
            # The event processor creates a RUNNING timeline immediately to prevent race conditions
            from datapilotflow.services.knowledge.job_timeline_service import get_job_timeline_service
            timeline_service = get_job_timeline_service()
            latest_timeline = timeline_service.get_latest_timeline_entry(job_id, user_id)

            if latest_timeline and latest_timeline.status == JobStatus.RUNNING:
                # Use existing timeline created by event processor
                logger.info(f"Using existing timeline {latest_timeline.id} for job {job_id}")
                extraction_context.timeline_id = latest_timeline.id
                timeline_id = latest_timeline.id
            else:
                # Fallback: create timeline if it doesn't exist (shouldn't happen normally)
                logger.warning(f"No RUNNING timeline found for job {job_id}, creating one")
                timeline_result = await timeline_step.execute(extraction_context)
                if timeline_result.success:
                    timeline_id = extraction_context.timeline_id
                else:
                    logger.error(f"Failed to create timeline for job {job_id}")
                    timeline_id = None

            # Get batch_size from job
            batch_size = knowledge_job.batch_size

            # Calculate total files and batches for progress tracking
            total_files = len(knowledge_source_config.local_files) if knowledge_source_config.local_files else None
            total_batches = None
            if total_files and batch_size:
                total_batches = (total_files + batch_size - 1) // batch_size

            # Emit job started notification
            await emit_job_started_notification(
                job_id=job_id,
                user_id=user_id,
                job_name=job_name,
                total_files=total_files,
                content_source_type=knowledge_source_config.content_source_type.value
            )

            # Get document batches from extraction service
            # This works for both LOCAL_FILES (FileExtractionStep) and WEB_SCRAPING (DocumentExtractionStep)
            from datapilotflow.processors.knowledge_job.services.document_extraction_service import (
                get_document_extraction_service,
            )
            extraction_service = get_document_extraction_service()

            async for doc_batch in extraction_service.extract_documents(
                knowledge_job=knowledge_job,
                knowledge_source_config=knowledge_source_config,
                batch_size=batch_size,
            ):
                batch_count += 1

                # Check for cancellation
                self.cancellation_manager.check_and_raise(job_id)

                logger.info(
                    f"Processing batch {batch_count}: {len(doc_batch)} documents "
                    f"(job: {job_id})"
                )

                # Create a fresh context for this batch
                batch_context = JobContext(
                    job=knowledge_job,
                    knowledge_source_config=knowledge_source_config,
                    user_id=user_id,
                    status_callback=status_callback,
                )
                batch_context.timeline_id = timeline_id
                batch_context.documents = doc_batch  # Set batch documents

                # CRITICAL: Carry over the collection_cleared flag from orchestrator
                # This prevents clearing the collection on every batch
                if collection_cleared:
                    batch_context._collection_cleared = True

                # Step 2: Chunk the documents in this batch
                chunk_result = await chunking_step.execute(batch_context)
                if not chunk_result.success:
                    raise Exception(f"Chunking failed for batch {batch_count}: {chunk_result.error}")

                # Step 3: Generate embeddings for this batch's chunks
                embed_result = await embedding_step.execute(batch_context)
                if not embed_result.success:
                    raise Exception(f"Embedding failed for batch {batch_count}: {embed_result.error}")

                # Step 4: Store this batch's vectors
                storage_result = await storage_step.execute(batch_context)
                if not storage_result.success:
                    raise Exception(f"Storage failed for batch {batch_count}: {storage_result.error}")

                # CRITICAL: Sync the collection_cleared flag back from context
                # After first batch, this will be True and prevent clearing in subsequent batches
                if batch_context._collection_cleared:
                    collection_cleared = True

                # Accumulate stats
                total_documents += len(doc_batch)
                total_chunks += len(batch_context.chunks)
                total_vectors += len(batch_context.vectors)

                logger.info(
                    f"Batch {batch_count} completed: {len(doc_batch)} docs, "
                    f"{len(batch_context.chunks)} chunks, {len(batch_context.vectors)} vectors"
                )

                # Emit progress notification after each batch
                await emit_job_progress_notification(
                    job_id=job_id,
                    user_id=user_id,
                    job_name=job_name,
                    batch_number=batch_count,
                    total_batches=total_batches,
                    documents_processed=total_documents,
                    chunks_created=total_chunks,
                    current_stage="processing"
                )

                # Update timeline with progress after each batch
                # This allows the UI to show real-time progress (documents/chunks processed so far)
                if timeline_id:
                    from datapilotflow.domain.knowledge.job_timeline import JobTimelineUpdate

                    elapsed_time = time.time() - start_time
                    timeline_update = JobTimelineUpdate(
                        documents_processed=total_documents,
                        chunks_created=total_chunks,
                        processing_time_seconds=elapsed_time
                    )

                    updated_timeline = timeline_service.update_timeline_entry(
                        timeline_id=timeline_id,
                        user_id=user_id,
                        update_data=timeline_update
                    )

                    if updated_timeline:
                        logger.debug(
                            f"Updated timeline {timeline_id} with progress: "
                            f"{total_documents} docs, {total_chunks} chunks, {elapsed_time:.2f}s"
                        )
                    else:
                        logger.warning(f"Failed to update timeline {timeline_id} with progress")

                # Emit progress
                if status_callback:
                    status_callback(
                        f"Processed batch {batch_count}: {total_documents} documents total",
                        {"batch": batch_count, "total_documents": total_documents}
                    )

            total_time = time.time() - start_time

            # Update timeline with completion
            final_context = JobContext(
                job=knowledge_job,
                knowledge_source_config=knowledge_source_config,
                user_id=user_id,
            )
            final_context.timeline_id = timeline_id
            final_context.stats = {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "total_vectors": total_vectors,
                "batches_processed": batch_count,
            }

            # Mark timeline as completed
            from datapilotflow.services.knowledge.job_timeline_service import get_job_timeline_service
            timeline_service = get_job_timeline_service()
            if timeline_id:
                timeline_service.complete_job_execution(
                    timeline_id=timeline_id,
                    user_id=user_id,
                    documents_processed=total_documents,
                    chunks_created=total_chunks,
                    processing_time_seconds=total_time
                )

            logger.info(
                f"Batch-wise job {job_id} completed successfully in {total_time:.2f}s: "
                f"{total_documents} docs, {total_chunks} chunks across {batch_count} batches"
            )

            # Emit job completed notification
            await emit_job_completed_notification(
                job_id=job_id,
                user_id=user_id,
                job_name=job_name,
                total_documents=total_documents,
                total_chunks=total_chunks,
                total_vectors=total_vectors,
                execution_time=total_time,
                batch_count=batch_count
            )

            return {
                "success": True,
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "total_vectors": total_vectors,
                "processing_time_seconds": total_time,
                "batches_processed": batch_count,
                "stats": final_context.stats,
                "errors": [],
                "timeline_id": timeline_id,
            }

        except JobCancelledException as e:
            logger.warning(f"Batch-wise job {job_id} was cancelled: {e}")

            # Emit cancellation notification
            await emit_job_cancelled_notification(
                job_id=job_id,
                user_id=user_id,
                job_name=job_name,
                cancellation_reason=str(e),
                batch_number=batch_count if batch_count > 0 else None,
                documents_processed=total_documents if total_documents > 0 else None,
                chunks_created=total_chunks if total_chunks > 0 else None
            )

            await self._handle_job_cancellation(extraction_context, str(e))
            raise

        except Exception as e:
            logger.error(f"Batch-wise job {job_id} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Emit failure notification
            await emit_job_failed_notification(
                job_id=job_id,
                user_id=user_id,
                job_name=job_name,
                error_message=str(e),
                batch_number=batch_count if batch_count > 0 else None,
                documents_processed=total_documents if total_documents > 0 else None,
                chunks_created=total_chunks if total_chunks > 0 else None
            )

            # Mark timeline as failed
            if timeline_id:
                from datapilotflow.services.knowledge.job_timeline_service import get_job_timeline_service
                timeline_service = get_job_timeline_service()
                timeline_service.fail_job_execution(
                    timeline_id=timeline_id,
                    user_id=user_id,
                    error_message=str(e),
                    error_traceback=traceback.format_exc()
                )

            raise

        finally:
            self.cancellation_manager.clear_cancellation(job_id)
