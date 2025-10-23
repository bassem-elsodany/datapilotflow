"""
File Upload Event Processor.

This module contains the actual processing logic for file upload-related events,
separated from the event listening infrastructure.
"""

import asyncio
import traceback
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger
from src.processors.document.file_processor import FileProcessor
from src.services.file_management.dao.rag_file_upload_service import RagFileUploadService
from src.config import settings
from src.services.events import RetryConfig


class FileUploadEventProcessor:
    """Processor for file upload-related events."""
    
    def __init__(self):
        """Initialize the file upload event processor."""
        # File processing configuration
        self.upload_inbound_dir = settings.RAG_FILE_UPLOAD_INBOUND_DIR
        self.archive_dir = settings.RAG_FILE_UPLOAD_ARCHIVE_DIR
        self.failed_dir = settings.RAG_FILE_UPLOAD_FAILED_DIR
        logger.info("FileUploadEventProcessor initialized")
    
    async def process_file_upload(self, event_payload: Dict[str, Any]) -> bool:
        """
        Process a file upload event.
        
        Args:
            event_payload: The file upload event data
            
        Returns:
            True if file was processed successfully, False otherwise
        """
        try:
            file_path = event_payload.get('location')
            file_id = event_payload.get('file_id')
            user_id = event_payload.get('user_id')
            original_filename = event_payload.get('original_filename')
            
            # Check retry attempts to prevent infinite loops
            retry_count = event_payload.get('retry_count', RetryConfig.DEFAULT_RETRY_COUNT)
            max_retries = RetryConfig.MAX_RETRIES
            
            logger.info(f"Processing file: {file_path} | Event: {event_payload} | Retry: {retry_count}/{max_retries}")

            # Diagnostic: check file existence at processing start
            if not Path(file_path).exists():
                logger.error(f"File {file_path} does not exist at processing start!")
                return False
            else:
                logger.info(f"File {file_path} exists at processing start.")

            # Initialize MongoDB service
            mongo_service = RagFileUploadService()
            
            # Idempotency check: skip if already processed and archived
            record = mongo_service.get_file_by_id(file_id)
            from src.domain.rag.rag_file_upload import FileUploadStatus
            if record and (record.status == FileUploadStatus.COMPLETED or (record.file_locations and record.file_locations.archive)):
                logger.warning(f"File {file_id} already processed and archived. Skipping duplicate processing.")
                return True

            # Update status to processing
            mongo_service.update_status(
                file_id=file_id,
                status="processing",
                message="File processing started",
                step="extraction"
            )

            # Explicitly extract markdown and log it
            processor = FileProcessor()
            try:
                markdown = processor.extract_markdown(Path(file_path))
                logger.info(f"Extracted markdown (first 500 chars): {markdown[:500]}")
            except FileNotFoundError as fnf:
                logger.error(f"File not found: {file_path}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                mongo_service.update_status(
                    file_id=file_id,
                    status="failed",
                    message=f"File not found: {file_path}",
                    step="extraction",
                    error=str(fnf),
                    traceback=traceback.format_exc()
                )
                mongo_service.update_error_details(
                    file_id=file_id,
                    error_type=type(fnf).__name__,
                    error_message=str(fnf),
                    traceback=traceback.format_exc(),
                    failed_step="extraction"
                )
                return False

            # Continue with the rest of the pipeline
            knowledge = await processor.process_uploaded_file_async(
                file_path=Path(file_path),
                user_id=user_id,
                original_filename=original_filename,
                enable_llm_enrichment=False,
                write_to_file=False,
                llm_max_workers=settings.RAG_LLM_ENRICHMENT_MAX_WORKERS
            )
            logger.info(f"File processed successfully: {file_path}")

            # Extract document IDs from knowledge metadata
            document_id = None
            chunk_ids = []
            processing_stats = {}
            
            if hasattr(knowledge, 'metadata') and knowledge.metadata:
                document_id = knowledge.metadata.get("document_id")
                chunk_ids = knowledge.metadata.get("chunk_ids", [])
                processing_stats = knowledge.metadata.get("processing_stats", {})
            
            logger.info(f"Captured document ID: {document_id}")
            logger.info(f"Captured chunk IDs: {chunk_ids}")

            # Update status to completed with processing results
            mongo_service.update_processing_results(
                file_id=file_id,
                chunks_created=processing_stats.get("total_chunks", 0),
                enriched_chunks=processing_stats.get("weaviate_processed", 0),
                processing_time_seconds=processing_stats.get("processing_time_seconds", 0.0),
                document_id=document_id,
                chunk_ids=chunk_ids
            )
            
            mongo_service.update_status(
                file_id=file_id,
                status="completed",
                message="File processing completed successfully",
                step="completed"
            )

            # On success, move file to archive
            archive_path = self._move_file(file_path, self.archive_dir)
            if archive_path:
                mongo_service.update_file_location(file_id, "archive", archive_path)
            logger.info(f"File archived to: {archive_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing file event: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Check retry count to prevent infinite loops
            retry_count = event_payload.get('retry_count', RetryConfig.DEFAULT_RETRY_COUNT)
            max_retries = RetryConfig.MAX_RETRIES
            
            # Initialize MongoDB service for error handling
            try:
                mongo_service = RagFileUploadService()
                
                # Update MongoDB status to failed
                mongo_service.update_status(
                    file_id=file_id,
                    status="failed",
                    message=f"File processing failed: {str(e)}",
                    step="processing",
                    error=str(e),
                    traceback=traceback.format_exc()
                )
                
                # Update error details
                mongo_service.update_error_details(
                    file_id=file_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    traceback=traceback.format_exc(),
                    failed_step="processing"
                )
            except Exception as mongo_err:
                logger.error(f"Failed to update MongoDB status: {mongo_err}")
                logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Move file to failed folder if it exists
            if 'file_path' in locals() and file_path and Path(file_path).exists():
                failed_path = self._move_file(file_path, self.failed_dir)
                if failed_path and 'mongo_service' in locals():
                    try:
                        mongo_service.update_file_location(file_id, "failed", failed_path)
                    except Exception as mongo_err:
                        logger.error(f"Failed to update file location in MongoDB: {mongo_err}")
                logger.info(f"File moved to failed folder: {failed_path}")
            
            # If we've exceeded max retries, don't re-raise to prevent requeue
            if retry_count >= max_retries:
                logger.warning(f"Max retries ({max_retries}) exceeded for file {file_id}. Not requeuing.")
                return False
            else:
                # For retryable errors, re-raise to trigger requeue
                logger.info(f"Retry {retry_count + 1}/{max_retries} will be attempted for file {file_id}")
                raise
    
    def _move_file(self, src_path: str, dest_dir: str) -> str:
        """Move a file to the destination directory, creating it if needed."""
        import os
        os.makedirs(dest_dir, exist_ok=True)
        if os.path.exists(src_path):
            dest_path = os.path.join(dest_dir, os.path.basename(src_path))
            shutil.move(src_path, dest_path)
            return dest_path
        return None


# Global instance for easy access
_file_upload_event_processor: Optional[FileUploadEventProcessor] = None


def get_file_upload_event_processor() -> FileUploadEventProcessor:
    """Get the global file upload event processor instance."""
    global _file_upload_event_processor
    
    if _file_upload_event_processor is None:
        _file_upload_event_processor = FileUploadEventProcessor()
    
    return _file_upload_event_processor
