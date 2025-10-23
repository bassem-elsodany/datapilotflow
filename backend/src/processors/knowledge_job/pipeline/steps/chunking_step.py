"""
Document Chunking Step.

This step chunks documents using the configured splitter.
"""

import time

from loguru import logger

from src.processors.knowledge_job.orchestration.job_context import JobContext
from src.processors.knowledge_job.pipeline.base import PipelineStep, StepResult


class DocumentChunkingStep(PipelineStep):
    """
    Pipeline step for chunking documents into smaller pieces.

    This step uses the splitter configuration from the job to split
    documents into chunks suitable for embedding.
    """

    def __init__(self):
        """Initialize the chunking step."""
        super().__init__(name="DocumentChunking")

    async def validate(self, context: JobContext) -> bool:
        """Validate that we have documents to chunk."""
        if not context.documents:
            logger.warning("No documents available for chunking")
            return False

        if not context.get_splitter_id():
            logger.error("No splitter configuration provided")
            return False

        return True

    async def execute(self, context: JobContext) -> StepResult:
        """
        Chunk documents using the configured splitter.

        Args:
            context: Job execution context

        Returns:
            StepResult with chunk count and statistics
        """
        try:
            logger.info(
                f"Starting document chunking for {len(context.documents)} documents "
                f"(job: {context.get_job_id()})"
            )

            start_time = time.time()

            # Get splitter configuration
            from src.processors.splitters import create_splitter
            from src.services.knowledge.document_splitter_service import (
                get_document_splitter_service,
            )

            splitter_service = get_document_splitter_service()
            splitter_config = splitter_service.get_splitter_for_job(
                context.get_splitter_id()
            )

            if not splitter_config:
                raise ValueError(
                    f"Splitter configuration not found: {context.get_splitter_id()}"
                )

            # Create splitter
            splitter = create_splitter(splitter_config)

            logger.info(
                f"Using splitter: {splitter_config.name} "
                f"(type: {splitter_config.splitter_type})"
            )

            # Split documents into chunks
            from src.domain.rag.knowledge_chunk import KnowledgeChunk

            chunks_created = 0
            for doc_index, doc in enumerate(context.documents):
                # Skip empty documents
                if not doc.page_content or not doc.page_content.strip():
                    logger.warning(
                        f"Skipping empty document {doc_index} from {doc.metadata.get('source_url', 'unknown')}"
                    )
                    continue

                # Split the document using splitter.split(text) method
                # Note: splitter.split() takes text and returns List[Document]
                split_docs = splitter.split(doc.page_content)
                # Convert to KnowledgeChunk objects
                # Preserve metadata from original document
                for chunk_index, chunk_doc in enumerate(split_docs):
                    knowledge_chunk = KnowledgeChunk(
                        page_content=chunk_doc.page_content,
                        source_url=doc.metadata.get("source_url", ""),
                        job_id=context.get_job_id(),
                        knowledge_source=context.knowledge_source_config.name,
                        title=doc.metadata.get("title", ""),
                        chunk_id=f"{context.knowledge_source_config.id}_doc_{doc_index}_chunk_{chunk_index}",
                        chunk_index=chunk_index,
                        total_chunks=len(split_docs),
                    )
                    context.chunks.append(knowledge_chunk)
                    chunks_created += 1

            execution_time = time.time() - start_time

            # Update context stats
            context.update_stats(
                total_chunks=chunks_created,
                chunking_time_seconds=execution_time,
                avg_chunks_per_doc=(
                    chunks_created / len(context.documents) if context.documents else 0
                ),
            )

            logger.info(
                f"Document chunking completed: {chunks_created} chunks from "
                f"{len(context.documents)} documents in {execution_time:.2f}s "
                f"(job: {context.get_job_id()})"
            )

            return StepResult.success_result(
                data={
                    "chunks_created": chunks_created,
                    "documents_chunked": len(context.documents),
                    "chunking_time_seconds": execution_time,
                    "splitter_used": splitter_config.name,
                }
            )

        except Exception as e:
            logger.error(f"Document chunking failed: {e}")
            context.add_error(f"Chunking error: {e}")
            return StepResult.failure_result(error=f"Document chunking failed: {e}")
