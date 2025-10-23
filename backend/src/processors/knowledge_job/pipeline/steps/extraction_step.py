"""
Document Extraction Step.

This step extracts documents from the knowledge source configuration
using a clean async generator pattern (NO callbacks).
"""

import time

from loguru import logger

from src.processors.knowledge_job.orchestration.job_context import JobContext
from src.processors.knowledge_job.pipeline.base import PipelineStep, StepResult
from src.processors.knowledge_job.services.document_extraction_service import (
    get_document_extraction_service,
)


class DocumentExtractionStep(PipelineStep):
    """
    Pipeline step for extracting documents from knowledge sources.

    Uses a clean async generator pattern instead of callbacks.
    """

    def __init__(self, batch_size: int = 10):
        """
        Initialize the extraction step.

        Args:
            batch_size: Number of documents to process per batch
        """
        super().__init__(name="DocumentExtraction")
        self.batch_size = batch_size
        self.extraction_service = get_document_extraction_service()

    async def validate(self, context: JobContext) -> bool:
        """Validate that we have a knowledge source configuration."""
        if not context.knowledge_source_config:
            logger.error("No knowledge source configuration provided")
            return False
        return True

    async def execute(self, context: JobContext) -> StepResult:
        """
        Extract documents from the knowledge source using async generators.

        NO CALLBACKS! Clean, composable async generator pattern.

        Args:
            context: Job execution context

        Returns:
            StepResult with extracted document count
        """
        try:
            logger.info(
                f"[NO CALLBACKS] Starting document extraction from "
                f"{context.knowledge_source_config.name} (job: {context.get_job_id()})"
            )

            start_time = time.time()
            total_documents = 0
            batch_count = 0

            # Clean async generator pattern - NO callbacks!
            async for batch in self.extraction_service.extract_documents(
                knowledge_job=context.job,
                knowledge_source_config=context.knowledge_source_config,
                batch_size=self.batch_size,
            ):
                # Store documents in context
                context.documents.extend(batch)
                total_documents += len(batch)
                batch_count += 1

                # Emit progress
                context.emit_status(
                    f"Extracted batch {batch_count}: {len(batch)} documents "
                    f"(total: {total_documents})"
                )

                logger.debug(
                    f"Extraction batch {batch_count}: {len(batch)} documents "
                    f"(total: {total_documents})"
                )

            execution_time = time.time() - start_time

            # Update context stats
            context.update_stats(
                total_documents=total_documents,
                extraction_time_seconds=execution_time,
                extraction_batches=batch_count,
            )

            logger.info(
                f"[NO CALLBACKS] Document extraction completed: {total_documents} documents "
                f"in {execution_time:.2f}s (job: {context.get_job_id()})"
            )

            return StepResult.success_result(
                data={
                    "documents_extracted": total_documents,
                    "batches_processed": batch_count,
                    "extraction_time_seconds": execution_time,
                }
            )

        except Exception as e:
            logger.error(f"Document extraction failed: {e}")
            context.add_error(f"Extraction error: {e}")
            return StepResult.failure_result(
                error=f"Document extraction failed: {e}"
            )
