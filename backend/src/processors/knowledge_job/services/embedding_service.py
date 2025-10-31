"""
Embedding Service.

This service provides an abstraction for generating embeddings from text,
decoupling the business logic from specific embedding providers (LiteLLM, OpenAI, etc.).
"""

import functools

# CRITICAL: Monkey-patch json module BEFORE any imports that might use it
import json as _json

_original_dumps = _json.dumps
_json.dumps = functools.partial(_original_dumps, ensure_ascii=False)

from abc import ABC, abstractmethod
from typing import List, Optional

from loguru import logger

from src.domain.knowledge.vectordb_collection import VectorDBCollection
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
        vector_collection: VectorDBCollection,
    ):
        """
        Initialize the embedding service.

        Args:
            provider_id: ID of the model provider
            model_name: Name of the embedding model
            user_id: User ID who owns the provider
            vector_collection: Vector database collection configuration with dimension
        """
        self.provider_id = provider_id
        self.model_name = model_name
        self.user_id = user_id
        self.vector_collection = vector_collection
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

            # Generate embeddings directly with LiteLLM (no adapter)
            import os

            import litellm

            # Force UTF-8 encoding at OS level
            os.environ["PYTHONIOENCODING"] = "utf-8"
            os.environ["LC_ALL"] = "en_US.UTF-8"
            os.environ["LANG"] = "en_US.UTF-8"

            logger.info(
                f"Generating embeddings for {len(valid_chunks)} chunks using {self._provider.provider_type}/{self.model_name} and dimension {self.vector_collection.vector_dimension}"
            )

            # Prepare texts - ensure they're UTF-8 strings
            texts = []
            for chunk in valid_chunks:
                # Ensure text is proper UTF-8 string
                text = chunk.page_content
                if isinstance(text, bytes):
                    text = text.decode("utf-8", errors="replace")
                texts.append(text)

            # Initialize token counter for batching
            from src.processors.splitters.token_counter import TokenCounter

            token_counter = TokenCounter(model_name=self.model_name)

            # Get model's max context (default to 8191 for text-embedding-3-*)
            max_context = TokenCounter.get_default_max_tokens(self.model_name)

            # Use 80% of max context for safety margin (API overhead, etc.)
            safe_batch_limit = int(max_context * 0.8)

            # Sub-batch the texts to avoid exceeding context window
            all_vectors = []
            current_batch = []
            current_batch_tokens = 0
            total_batches = 0

            for text in texts:
                text_tokens = token_counter.count_tokens(text)

                # If single text exceeds safe limit, we have a problem
                if text_tokens > safe_batch_limit:
                    logger.warning(
                        f"Single chunk has {text_tokens} tokens, exceeds safe limit {safe_batch_limit}. "
                        f"This should not happen if chunking is working correctly!"
                    )

                # Check if adding this text would exceed the batch limit
                if current_batch and (
                    current_batch_tokens + text_tokens > safe_batch_limit
                ):
                    # Process current batch
                    total_batches += 1
                    logger.debug(
                        f"Processing embedding sub-batch {total_batches}: {len(current_batch)} texts, ~{current_batch_tokens} tokens"
                    )

                    response = litellm.embedding(
                        model=f"{self._provider.provider_type}/{self.model_name}",
                        input=current_batch,
                        api_key=self._provider.api_key,
                        dimensions=self.vector_collection.vector_dimension,
                    )

                    # Extract vectors
                    for item in response.data:
                        if hasattr(item, "embedding"):
                            all_vectors.append(item.embedding)
                        elif isinstance(item, dict) and "embedding" in item:
                            all_vectors.append(item["embedding"])

                    # Reset batch
                    current_batch = []
                    current_batch_tokens = 0

                # Add text to current batch
                current_batch.append(text)
                current_batch_tokens += text_tokens

            # Process final batch if any
            if current_batch:
                total_batches += 1
                logger.debug(
                    f"Processing final embedding sub-batch {total_batches}: {len(current_batch)} texts, ~{current_batch_tokens} tokens"
                )

                response = litellm.embedding(
                    model=f"{self._provider.provider_type}/{self.model_name}",
                    input=current_batch,
                    api_key=self._provider.api_key,
                    dimensions=self.vector_collection.vector_dimension,
                )

                # Extract vectors
                for item in response.data:
                    if hasattr(item, "embedding"):
                        all_vectors.append(item.embedding)
                    elif isinstance(item, dict) and "embedding" in item:
                        all_vectors.append(item["embedding"])

            logger.info(
                f"Generated {len(all_vectors)} embeddings in {total_batches} sub-batches using {self._provider.name}/{self.model_name} and dimension {self.vector_collection.vector_dimension}"
            )

            return all_vectors

        except Exception as e:
            error_msg = f"Failed to generate embeddings: {e}"
            logger.error(error_msg)
            raise EmbeddingGenerationError(error_msg, original_error=e)

    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension from the vector collection configuration."""
        return self.vector_collection.vector_dimension

    def get_provider_info(self) -> dict:
        """Get provider information."""
        return {
            "provider_id": self.provider_id,
            "provider_name": self._provider.name if self._provider else "unknown",
            "provider_type": (
                self._provider.provider_type if self._provider else "unknown"
            ),
            "model_name": self.model_name,
        }
