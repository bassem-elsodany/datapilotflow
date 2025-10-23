"""
Vector Storage Service.

This service provides an abstraction for storing vectors in vector databases,
decoupling business logic from specific database implementations (Milvus, Pinecone, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from loguru import logger

from src.domain.rag.knowledge_chunk import KnowledgeChunk


class VectorStorageService(ABC):
    """
    Abstract interface for vector storage services.

    This allows swapping vector database implementations without changing business logic.
    """

    @abstractmethod
    async def store_vectors(
        self, chunks: List[KnowledgeChunk], vectors: List[List[float]]
    ) -> int:
        """
        Store knowledge chunks with their embedding vectors.

        Args:
            chunks: List of knowledge chunks
            vectors: List of embedding vectors (same length as chunks)

        Returns:
            Number of vectors stored

        Raises:
            VectorStorageError: If storage fails
        """
        pass

    @abstractmethod
    async def clear_collection(self) -> bool:
        """
        Clear all data from the collection.

        Returns:
            True if cleared successfully

        Raises:
            VectorStorageError: If clearing fails
        """
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, any]:
        """
        Get collection statistics.

        Returns:
            Dictionary with collection stats (count, etc.)
        """
        pass

    @abstractmethod
    def get_collection_info(self) -> dict:
        """
        Get information about the vector collection.

        Returns:
            Dictionary with collection details
        """
        pass


class VectorStorageError(Exception):
    """Exception raised when vector storage operations fail."""

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


class MilvusVectorStorageService(VectorStorageService):
    """
    Vector storage service implementation using Milvus.

    This service wraps the Milvus processor and provides a clean interface
    for the pipeline steps.
    """

    def __init__(
        self,
        collection_name: str,
        vector_dimension: int,
        milvus_processor: "MilvusProcessor" = None,
    ):
        """
        Initialize the Milvus vector storage service.

        Args:
            collection_name: Name of the Milvus collection
            vector_dimension: Dimension of embedding vectors
            milvus_processor: Optional Milvus processor (injected for testability)
        """
        self.collection_name = collection_name
        self.vector_dimension = vector_dimension
        self._milvus_processor = milvus_processor

        if not self._milvus_processor:
            self._initialize_processor()

    def _initialize_processor(self) -> None:
        """Initialize the Milvus processor."""
        from src.application.data.storage.milvus_processor import create_milvus_processor

        try:
            self._milvus_processor = create_milvus_processor(
                milvus_model=KnowledgeChunk,
                milvus_collection_name=self.collection_name,
                vector_dimension=self.vector_dimension,
            )
            logger.info(
                f"Initialized Milvus processor for collection: {self.collection_name}"
            )
        except Exception as e:
            raise VectorStorageError(
                f"Failed to initialize Milvus processor: {e}", original_error=e
            )

    async def store_vectors(
        self, chunks: List[KnowledgeChunk], vectors: List[List[float]]
    ) -> int:
        """
        Store chunks with vectors in Milvus.

        Args:
            chunks: List of knowledge chunks
            vectors: List of embedding vectors

        Returns:
            Number of vectors stored
        """
        if len(chunks) != len(vectors):
            raise VectorStorageError(
                f"Mismatch between chunks ({len(chunks)}) and vectors ({len(vectors)})"
            )

        if not chunks or not vectors:
            logger.warning("No chunks or vectors to store")
            return 0

        try:
            # Use the existing Milvus processor
            self._milvus_processor.process_documents(chunks, vectors)

            logger.info(f"Stored {len(vectors)} vectors in Milvus collection: {self.collection_name}")
            return len(vectors)

        except Exception as e:
            error_msg = f"Failed to store vectors in Milvus: {e}"
            logger.error(error_msg)
            raise VectorStorageError(error_msg, original_error=e)

    async def clear_collection(self) -> bool:
        """
        Clear the Milvus collection.

        Returns:
            True if cleared successfully
        """
        try:
            stats_before = self._milvus_processor.get_statistics()
            logger.info(f"Collection stats before clearing: {stats_before}")

            self._milvus_processor.clear_all()

            stats_after = self._milvus_processor.get_statistics()
            logger.info(f"Collection stats after clearing: {stats_after}")
            logger.info(f"Collection {self.collection_name} cleared successfully")

            return True

        except Exception as e:
            error_msg = f"Failed to clear Milvus collection: {e}"
            logger.error(error_msg)
            raise VectorStorageError(error_msg, original_error=e)

    def get_statistics(self) -> Dict[str, any]:
        """Get collection statistics from Milvus."""
        try:
            return self._milvus_processor.get_statistics()
        except Exception as e:
            logger.error(f"Failed to get Milvus statistics: {e}")
            return {"error": str(e)}

    def get_collection_info(self) -> dict:
        """Get collection information."""
        return {
            "collection_name": self.collection_name,
            "vector_dimension": self.vector_dimension,
            "type": "milvus",
        }
