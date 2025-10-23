"""
Vector Storage Step.

This step stores chunks with their embeddings in the vector database.
"""

import time

from loguru import logger

from src.processors.knowledge_job.orchestration.job_context import JobContext
from src.processors.knowledge_job.pipeline.base import PipelineStep, StepResult
from src.processors.knowledge_job.services.vector_storage_service import (
    MilvusVectorStorageService,
    VectorStorageService,
)


class VectorStorageStep(PipelineStep):
    """
    Pipeline step for storing vectors in a vector database.

    This step stores the chunks and their embeddings in Milvus,
    optionally clearing the collection first if requested.
    """

    def __init__(self, storage_service: VectorStorageService = None):
        """
        Initialize the vector storage step.

        Args:
            storage_service: Optional storage service (injected for testability)
        """
        super().__init__(name="VectorStorage")
        self.storage_service = storage_service

    async def validate(self, context: JobContext) -> bool:
        """Validate that we have chunks and vectors to store."""
        if not context.chunks:
            logger.warning("No chunks available for storage")
            return False

        if not context.vectors:
            logger.warning("No vectors available for storage")
            return False

        if len(context.chunks) != len(context.vectors):
            logger.error(
                f"Mismatch between chunks ({len(context.chunks)}) "
                f"and vectors ({len(context.vectors)})"
            )
            return False

        return True

    async def execute(self, context: JobContext) -> StepResult:
        """
        Store chunks and vectors in the vector database.

        Args:
            context: Job execution context

        Returns:
            StepResult with storage statistics
        """
        try:
            logger.info(
                f"Starting vector storage for {len(context.chunks)} chunks "
                f"(job: {context.get_job_id()})"
            )

            start_time = time.time()

            # Get or create storage service
            if not self.storage_service:
                storage_service = self._create_storage_service(context)
            else:
                storage_service = self.storage_service

            # Clear collection if requested
            if context.is_collection_clear_requested():
                logger.info(
                    f"Clearing collection before storage (job: {context.get_job_id()})"
                )
                context.emit_status("Clearing existing data from collection...")

                stats_before = storage_service.get_statistics()
                logger.info(f"Collection stats before clearing: {stats_before}")

                await storage_service.clear_collection()

                stats_after = storage_service.get_statistics()
                logger.info(f"Collection stats after clearing: {stats_after}")
                logger.info("Collection cleared successfully")

            # Store vectors
            context.emit_status(
                f"Storing {len(context.vectors)} vectors in collection..."
            )

            vectors_stored = await storage_service.store_vectors(
                context.chunks, context.vectors
            )

            execution_time = time.time() - start_time

            # Get final statistics
            final_stats = storage_service.get_statistics()
            collection_info = storage_service.get_collection_info()

            # Update context stats
            context.update_stats(
                vectors_stored=vectors_stored,
                storage_time_seconds=execution_time,
                collection_info=collection_info,
                final_collection_stats=final_stats,
            )

            logger.info(
                f"Vector storage completed: {vectors_stored} vectors stored "
                f"in {execution_time:.2f}s to collection {collection_info.get('collection_name')} "
                f"(job: {context.get_job_id()})"
            )

            return StepResult.success_result(
                data={
                    "vectors_stored": vectors_stored,
                    "storage_time_seconds": execution_time,
                    "collection_info": collection_info,
                    "collection_stats": final_stats,
                }
            )

        except Exception as e:
            logger.error(f"Vector storage failed: {e}")
            context.add_error(f"Storage error: {e}")
            return StepResult.failure_result(error=f"Vector storage failed: {e}")

    def _create_storage_service(self, context: JobContext) -> VectorStorageService:
        """
        Create a storage service from the job configuration.

        Args:
            context: Job execution context

        Returns:
            Configured storage service
        """
        # Get VectorDB collection configuration
        from src.services.knowledge.vectordb_collection_service import (
            get_vectordb_collection_service,
        )

        vectordb_collection_service = get_vectordb_collection_service()
        vectordb_collection = vectordb_collection_service.get_collection(
            context.get_vectordb_collection_id(), context.get_user_id()
        )

        if not vectordb_collection:
            raise ValueError(
                f"VectorDB collection {context.get_vectordb_collection_id()} not found"
            )

        # Create Milvus storage service
        return MilvusVectorStorageService(
            collection_name=vectordb_collection.collection_name,
            vector_dimension=vectordb_collection.vector_dimension,
        )

    async def rollback(self, context: JobContext) -> None:
        """
        Rollback storage operation by clearing the collection.

        Args:
            context: Job execution context
        """
        try:
            logger.warning(
                f"Rolling back vector storage for job {context.get_job_id()}"
            )

            if self.storage_service:
                await self.storage_service.clear_collection()
                logger.info("Storage rollback completed - collection cleared")

        except Exception as e:
            logger.error(f"Error during storage rollback: {e}")
