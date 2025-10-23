"""
Embedding Generation Step.

This step generates embeddings for document chunks using the configured model provider.
"""

import time

from loguru import logger

from src.processors.knowledge_job.orchestration.job_context import JobContext
from src.processors.knowledge_job.pipeline.base import PipelineStep, StepResult
from src.processors.knowledge_job.services.embedding_service import (
    EmbeddingService,
    ModelProviderEmbeddingService,
)


class EmbeddingGenerationStep(PipelineStep):
    """
    Pipeline step for generating embeddings from document chunks.

    This step uses the embedding service to generate vector embeddings
    for all chunks, which can then be stored in a vector database.
    """

    def __init__(self, embedding_service: EmbeddingService = None):
        """
        Initialize the embedding generation step.

        Args:
            embedding_service: Optional embedding service (injected for testability)
        """
        super().__init__(name="EmbeddingGeneration")
        self.embedding_service = embedding_service

    async def validate(self, context: JobContext) -> bool:
        """Validate that we have chunks to embed."""
        if not context.chunks:
            logger.warning("No chunks available for embedding generation")
            return False

        if not context.get_vectordb_collection_id():
            logger.error("No VectorDB collection configuration provided")
            return False

        return True

    async def execute(self, context: JobContext) -> StepResult:
        """
        Generate embeddings for all chunks.

        Args:
            context: Job execution context

        Returns:
            StepResult with embedding statistics
        """
        try:
            logger.info(
                f"Starting embedding generation for {len(context.chunks)} chunks "
                f"(job: {context.get_job_id()})"
            )

            start_time = time.time()

            # Get or create embedding service
            if not self.embedding_service:
                embedding_service = self._create_embedding_service(context)
            else:
                embedding_service = self.embedding_service

            # Generate embeddings
            vectors = await embedding_service.generate_embeddings(context.chunks)

            if len(vectors) != len(context.chunks):
                raise ValueError(
                    f"Mismatch between chunks ({len(context.chunks)}) "
                    f"and vectors ({len(vectors)})"
                )

            # Store vectors in context
            context.vectors = vectors

            execution_time = time.time() - start_time

            # Calculate statistics
            vector_dimension = len(vectors[0]) if vectors else 0
            provider_info = embedding_service.get_provider_info()

            # Update context stats
            context.update_stats(
                total_vectors=len(vectors),
                embedding_time_seconds=execution_time,
                vector_dimension=vector_dimension,
                embedding_provider=provider_info.get("provider_name", "unknown"),
                embedding_model=provider_info.get("model_name", "unknown"),
            )

            logger.info(
                f"Embedding generation completed: {len(vectors)} vectors "
                f"(dimension: {vector_dimension}) in {execution_time:.2f}s "
                f"using {provider_info.get('provider_name')}/{provider_info.get('model_name')} "
                f"(job: {context.get_job_id()})"
            )

            return StepResult.success_result(
                data={
                    "vectors_generated": len(vectors),
                    "vector_dimension": vector_dimension,
                    "embedding_time_seconds": execution_time,
                    "provider_info": provider_info,
                }
            )

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            context.add_error(f"Embedding error: {e}")
            return StepResult.failure_result(
                error=f"Embedding generation failed: {e}"
            )

    def _create_embedding_service(self, context: JobContext) -> EmbeddingService:
        """
        Create an embedding service from the job configuration.

        Args:
            context: Job execution context

        Returns:
            Configured embedding service
        """
        # Get VectorDB collection to retrieve embedding model configuration
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

        # Create embedding service with provider configuration
        return ModelProviderEmbeddingService(
            provider_id=vectordb_collection.embedding_model_provider_id,
            model_name=vectordb_collection.embedding_model_name,
            user_id=context.get_user_id(),
        )
