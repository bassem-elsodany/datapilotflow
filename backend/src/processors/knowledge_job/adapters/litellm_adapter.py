"""
LiteLLM Embedding Adapter.

This adapter implements the embedding generation using LiteLLM,
extracted from the old monolithic processor for better separation of concerns.
"""

from typing import List

import litellm
from loguru import logger

from src.domain.rag.knowledge_chunk import KnowledgeChunk


class EmbeddingAdapter:
    """Base class for embedding adapters."""

    async def generate_embeddings(
        self, chunks: List[KnowledgeChunk]
    ) -> List[List[float]]:
        """Generate embeddings for chunks."""
        raise NotImplementedError


class LiteLLMEmbeddingAdapter(EmbeddingAdapter):
    """
    Embedding adapter using LiteLLM.

    This adapter handles the actual API calls to embedding providers
    through the LiteLLM library.
    """

    def __init__(self, provider, model_name: str):
        """
        Initialize the LiteLLM adapter.

        Args:
            provider: Model provider configuration (domain object)
            model_name: Name of the embedding model to use
        """
        self.provider = provider
        self.model_name = model_name

    async def generate_embeddings(
        self, chunks: List[KnowledgeChunk]
    ) -> List[List[float]]:
        """
        Generate embeddings using LiteLLM.

        Args:
            chunks: List of knowledge chunks to embed

        Returns:
            List of embedding vectors

        Raises:
            Exception: If embedding generation fails
        """
        if not chunks:
            return []

        # Extract and validate texts
        texts = []
        for chunk in chunks:
            text = chunk.page_content
            if text and text.strip():
                texts.append(text)
            else:
                logger.warning(f"Skipping chunk {chunk.chunk_id} with empty content")

        if not texts:
            logger.warning("No valid texts found for embedding generation")
            return []

        # Prepare LiteLLM parameters
        litellm_params = {
            "model": f"{self.provider.provider_type}/{self.model_name}",
            "input": texts,
        }

        # Add API key
        if not self.provider.api_key:
            raise ValueError(
                f"No API key configured for provider: {self.provider.name}. "
                f"Please set the API key in your model provider configuration."
            )
        litellm_params["api_key"] = self.provider.api_key

        # Add custom endpoint if provided
        if self.provider.endpoint:
            litellm_params["api_base"] = self.provider.endpoint

        # Add timeout
        if self.provider.timeout:
            litellm_params["timeout"] = self.provider.timeout

        # Add additional configuration
        if self.provider.embedding and self.provider.embedding.config:
            litellm_params.update(self.provider.embedding.config)

        try:
            # Generate embeddings
            logger.debug(
                f"Generating embeddings for {len(texts)} texts using "
                f"{self.provider.provider_type}/{self.model_name}"
            )

            response = litellm.embedding(**litellm_params)

            # Extract vectors from response
            if not hasattr(response, "data") or not response.data:
                raise ValueError("No embedding data received from LiteLLM response")

            vectors = []
            for item in response.data:
                if hasattr(item, "embedding"):
                    vectors.append(item.embedding)
                elif isinstance(item, dict) and "embedding" in item:
                    vectors.append(item["embedding"])
                else:
                    raise ValueError(f"Unexpected response item format: {type(item)}")

            logger.debug(
                f"Successfully generated {len(vectors)} embeddings "
                f"(dimension: {len(vectors[0]) if vectors else 0})"
            )

            return vectors

        except Exception as e:
            logger.error(f"LiteLLM embedding generation failed: {e}")
            raise
