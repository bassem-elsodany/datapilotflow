"""
Job Notification Helper

Provides convenience functions for emitting job progress notifications.
This module integrates the job processing pipeline with the notification system.
"""

from loguru import logger
from typing import Optional, Dict, Any

from src.domain.notification import NotificationType, NotificationPriority
from src.services.notification.notification_event_service import publish_notification_event


async def emit_job_started_notification(
    job_id: str,
    user_id: str,
    job_name: str,
    total_files: Optional[int] = None,
    content_source_type: Optional[str] = None
) -> None:
    """
    Emit notification when job starts.

    Args:
        job_id: The job identifier
        user_id: The user identifier
        job_name: The job name/title
        total_files: Optional total number of files to process
        content_source_type: Optional content source type (LOCAL_FILES, WEB_SCRAPING, etc.)
    """
    try:
        metadata = {
            "job_id": job_id,
            "job_name": job_name,
            "stage": "started"
        }
        if total_files:
            metadata["total_files"] = total_files
        if content_source_type:
            metadata["content_source_type"] = content_source_type

        message = f"Knowledge processing job '{job_name}' has started."
        if total_files:
            message += f" Processing {total_files} files."

        event_payload = {
            "event_type": "knowledge_job_notification",
            "user_id": user_id,
            "notification_type": NotificationType.KNOWLEDGE_JOB_STARTED,
            "priority": NotificationPriority.MEDIUM,
            "title": f"Job Started: {job_name}",
            "message": message,
            "metadata": metadata,
            "progress": 0.0
        }

        await publish_notification_event(event_payload)
        logger.debug(f"Emitted job started notification for job {job_id}")

    except Exception as e:
        logger.error(f"Error emitting job started notification: {e}")
        # Don't raise - notification failures shouldn't stop job execution


async def emit_job_progress_notification(
    job_id: str,
    user_id: str,
    job_name: str,
    batch_number: int,
    total_batches: Optional[int],
    documents_processed: int,
    chunks_created: int,
    current_stage: str = "processing"
) -> None:
    """
    Emit notification for job progress.

    Args:
        job_id: The job identifier
        user_id: The user identifier
        job_name: The job name/title
        batch_number: Current batch number
        total_batches: Optional total number of batches
        documents_processed: Number of documents processed so far
        chunks_created: Number of chunks created so far
        current_stage: Current processing stage
    """
    try:
        # Calculate progress percentage
        if total_batches:
            progress = (batch_number / total_batches) * 100
        else:
            progress = None

        metadata = {
            "job_id": job_id,
            "job_name": job_name,
            "batch_number": batch_number,
            "documents_processed": documents_processed,
            "chunks_created": chunks_created,
            "stage": current_stage
        }
        if total_batches:
            metadata["total_batches"] = total_batches

        # For web crawling (no total_batches), show cumulative progress
        # For local files (with total_batches), show batch progress
        if total_batches:
            message = f"Processing batch {batch_number} of {total_batches} - {documents_processed} documents, {chunks_created} chunks created"
        else:
            message = f"Processed {documents_processed} documents, {chunks_created} chunks created (batch {batch_number})"

        event_payload = {
            "event_type": "knowledge_job_notification",
            "user_id": user_id,
            "notification_type": NotificationType.KNOWLEDGE_JOB_PROGRESS,
            "priority": NotificationPriority.LOW,
            "title": f"Job Progress: {job_name}",
            "message": message,
            "metadata": metadata,
            "progress": progress
        }

        await publish_notification_event(event_payload)
        logger.debug(f"Emitted job progress notification for job {job_id}: batch {batch_number}")

    except Exception as e:
        logger.error(f"Error emitting job progress notification: {e}")
        # Don't raise - notification failures shouldn't stop job execution


async def emit_job_completed_notification(
    job_id: str,
    user_id: str,
    job_name: str,
    total_documents: int,
    total_chunks: int,
    total_vectors: int,
    execution_time: float,
    batch_count: Optional[int] = None
) -> None:
    """
    Emit notification when job completes successfully.

    Args:
        job_id: The job identifier
        user_id: The user identifier
        job_name: The job name/title
        total_documents: Total number of documents processed
        total_chunks: Total number of chunks created
        total_vectors: Total number of vectors stored
        execution_time: Total execution time in seconds
        batch_count: Optional number of batches processed
    """
    try:
        metadata = {
            "job_id": job_id,
            "job_name": job_name,
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "total_vectors": total_vectors,
            "execution_time_seconds": execution_time,
            "stage": "completed"
        }
        if batch_count:
            metadata["batch_count"] = batch_count

        message = f"Successfully processed {total_documents} documents into {total_chunks} chunks"
        if batch_count:
            message += f" ({batch_count} batches)"
        message += f" in {execution_time:.1f}s"

        event_payload = {
            "event_type": "knowledge_job_notification",
            "user_id": user_id,
            "notification_type": NotificationType.KNOWLEDGE_JOB_COMPLETED,
            "priority": NotificationPriority.MEDIUM,
            "title": f"Job Completed: {job_name}",
            "message": message,
            "metadata": metadata,
            "progress": 100.0
        }

        await publish_notification_event(event_payload)
        logger.info(f"Emitted job completed notification for job {job_id}")

    except Exception as e:
        logger.error(f"Error emitting job completed notification: {e}")
        # Don't raise - notification failures shouldn't stop job execution


async def emit_job_failed_notification(
    job_id: str,
    user_id: str,
    job_name: str,
    error_message: str,
    batch_number: Optional[int] = None,
    documents_processed: Optional[int] = None,
    chunks_created: Optional[int] = None
) -> None:
    """
    Emit notification when job fails.

    Args:
        job_id: The job identifier
        user_id: The user identifier
        job_name: The job name/title
        error_message: The error message
        batch_number: Optional batch number where failure occurred
        documents_processed: Optional number of documents processed before failure
        chunks_created: Optional number of chunks created before failure
    """
    try:
        metadata = {
            "job_id": job_id,
            "job_name": job_name,
            "error_message": error_message,
            "stage": "failed"
        }
        if batch_number:
            metadata["failed_at_batch"] = batch_number
        if documents_processed:
            metadata["documents_processed"] = documents_processed
        if chunks_created:
            metadata["chunks_created"] = chunks_created

        message = f"Job failed: {error_message}"
        if batch_number:
            message = f"Job failed at batch {batch_number}: {error_message}"

        event_payload = {
            "event_type": "knowledge_job_notification",
            "user_id": user_id,
            "notification_type": NotificationType.KNOWLEDGE_JOB_FAILED,
            "priority": NotificationPriority.HIGH,
            "title": f"Job Failed: {job_name}",
            "message": message,
            "metadata": metadata
        }

        await publish_notification_event(event_payload)
        logger.warning(f"Emitted job failed notification for job {job_id}")

    except Exception as e:
        logger.error(f"Error emitting job failed notification: {e}")
        # Don't raise - notification failures shouldn't stop job execution


async def emit_job_cancelled_notification(
    job_id: str,
    user_id: str,
    job_name: str,
    cancellation_reason: str,
    batch_number: Optional[int] = None,
    documents_processed: Optional[int] = None,
    chunks_created: Optional[int] = None
) -> None:
    """
    Emit notification when job is cancelled.

    Args:
        job_id: The job identifier
        user_id: The user identifier
        job_name: The job name/title
        cancellation_reason: The reason for cancellation
        batch_number: Optional batch number when cancelled
        documents_processed: Optional number of documents processed before cancellation
        chunks_created: Optional number of chunks created before cancellation
    """
    try:
        metadata = {
            "job_id": job_id,
            "job_name": job_name,
            "cancellation_reason": cancellation_reason,
            "stage": "cancelled"
        }
        if batch_number:
            metadata["cancelled_at_batch"] = batch_number
        if documents_processed:
            metadata["documents_processed"] = documents_processed
        if chunks_created:
            metadata["chunks_created"] = chunks_created

        message = f"Job was cancelled: {cancellation_reason}"
        if batch_number:
            message = f"Job was cancelled at batch {batch_number}: {cancellation_reason}"

        event_payload = {
            "event_type": "knowledge_job_notification",
            "user_id": user_id,
            "notification_type": NotificationType.KNOWLEDGE_JOB_CANCELLED,
            "priority": NotificationPriority.MEDIUM,
            "title": f"Job Cancelled: {job_name}",
            "message": message,
            "metadata": metadata
        }

        await publish_notification_event(event_payload)
        logger.info(f"Emitted job cancelled notification for job {job_id}")

    except Exception as e:
        logger.error(f"Error emitting job cancelled notification: {e}")
        # Don't raise - notification failures shouldn't stop job execution
