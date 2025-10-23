"""
Embedding Service.

This service provides an abstraction for generating embeddings from text,
decoupling the business logic from specific embedding providers (LiteLLM, OpenAI, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from loguru import logger

from src.domain.rag.knowledge_chunk import KnowledgeChunk


class EmbeddingService(ABC):
    """
    Abstract interface for embedding generation services.

    This allows swapping embedding providers without changing business logic.
    """

    @abstractmethod
    async def generate_embeddings(
        self, chunks: List[KnowledgeChunk]
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of knowledge chunks.

        Args:
            chunks: List of knowledge chunks to embed

        Returns:
            List of embedding vectors (one per chunk)

        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        pass

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this service.

        Returns:
            Embedding vector dimension
        """
        pass

    @abstractmethod
    def get_provider_info(self) -> dict:
        """
        Get information about the embedding provider.

        Returns:
            Dictionary with provider details (name, model, etc.)
        """
        pass


class EmbeddingGenerationError(Exception):
    """Exception raised when embedding generation fails."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """
        Initialize the error.

        Args:
            message: Error message
            original_error: Original exception that caused this error
        """
        self.message = message
        self.original_error = original_error
        super().__init__(message)


class ModelProviderEmbeddingService(EmbeddingService):
    """
    Embedding service that uses the model provider infrastructure.

    This service retrieves provider configuration from the database
    and delegates to the appropriate adapter based on provider type.
    """

    def __init__(
        self,
        provider_id: str,
        model_name: str,
        user_id: str,
        embedding_adapter: "EmbeddingAdapter" = None,
    ):
        """
        Initialize the embedding service.

        Args:
            provider_id: ID of the model provider
            model_name: Name of the embedding model
            user_id: User ID who owns the provider
            embedding_adapter: Optional embedding adapter (injected for testability)
        """
        self.provider_id = provider_id
        self.model_name = model_name
        self.user_id = user_id
        self._embedding_adapter = embedding_adapter
        self._provider = None
        self._load_provider()

    def _load_provider(self) -> None:
        """Load the model provider configuration from the database."""
        from src.services.model_provider.model_provider_service import (
            ModelProviderService,
        )

        model_provider_service = ModelProviderService()
        provider = model_provider_service.get_model_provider(
            self.provider_id, self.user_id
        )

        if not provider:
            raise EmbeddingGenerationError(
                f"Model provider with ID {self.provider_id} not found"
            )

        # Convert to domain object if needed
        if isinstance(provider, dict):
            from src.domain.model_provider.model_provider import ModelProvider

            provider = ModelProvider.model_validate(provider)

        if not provider.embedding:
            raise EmbeddingGenerationError(
                f"Model provider {provider.name} does not support embedding models"
            )

        if self.model_name not in provider.embedding.models:
            raise EmbeddingGenerationError(
                f"Model {self.model_name} not available in provider {provider.name}. "
                f"Available models: {provider.embedding.models}"
            )

        self._provider = provider
        logger.info(
            f"Loaded embedding provider: {provider.name} (model: {self.model_name})"
        )

    async def generate_embeddings(
        self, chunks: List[KnowledgeChunk]
    ) -> List[List[float]]:
        """
        Generate embeddings using the configured model provider.

        Args:
            chunks: List of knowledge chunks to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingGenerationError: If generation fails
        """
        if not chunks:
            logger.warning("No chunks provided for embedding generation")
            return []

        # Get or create adapter
        if not self._embedding_adapter:
            from src.processors.knowledge_job.adapters.litellm_adapter import (
                LiteLLMEmbeddingAdapter,
            )

            self._embedding_adapter = LiteLLMEmbeddingAdapter(
                provider=self._provider, model_name=self.model_name
            )

        try:
            # Filter valid content
            valid_chunks = []
            for chunk in chunks:
                if chunk.page_content and chunk.page_content.strip():
                    valid_chunks.append(chunk)
                else:
                    logger.warning(
                        f"Skipping chunk with empty content: {chunk.chunk_id}"
                    )

            if not valid_chunks:
                logger.warning("No valid chunks found for embedding generation")
                return []

            # Generate embeddings via adapter
            vectors = await self._embedding_adapter.generate_embeddings(valid_chunks)

            logger.info(
                f"Generated {len(vectors)} embeddings using {self._provider.name}/{self.model_name}"
            )

            return vectors

        except Exception as e:
            error_msg = f"Failed to generate embeddings: {e}"
            logger.error(error_msg)
            raise EmbeddingGenerationError(error_msg, original_error=e)

    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension from the provider."""
        # This would ideally come from provider config or be detected from first embedding
        # For now, return a placeholder
        return getattr(self._provider.embedding, "dimension", 1536)

    def get_provider_info(self) -> dict:
        """Get provider information."""
        return {
            "provider_id": self.provider_id,
            "provider_name": self._provider.name if self._provider else "unknown",
            "provider_type": self._provider.provider_type if self._provider else "unknown",
            "model_name": self.model_name,
        }
