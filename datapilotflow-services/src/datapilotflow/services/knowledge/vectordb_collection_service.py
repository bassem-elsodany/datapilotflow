"""
VectorDB Collection Service.

This service handles business logic for vector database collection configurations.
"""

from typing import List, Optional

from loguru import logger

from datapilotflow.domain.knowledge.vectordb_collection import (
    VectorDBCollection,
    VectorDBCollectionCreate,
    VectorDBCollectionUpdate,
)
from datapilotflow.infrastructure.dao.vectordb import VectorDBCollectionDAO


class VectorDBCollectionService:
    """Service for managing vector database collection configurations."""

    def __init__(self):
        self.vectordb_collection_dao = VectorDBCollectionDAO()

    def create_collection(
        self, collection_data: VectorDBCollectionCreate, user_id: str
    ) -> Optional[VectorDBCollection]:
        """Create a new vector DB collection configuration."""

        # Validate embedding model
        self._validate_embedding_model(
            collection_data.embedding_model_provider_id,
            collection_data.embedding_model_name,
            user_id,
        )

        # Note: Chunking configuration is now handled at the job level, not collection level

        # Check if collection name already exists
        existing_collection = self.vectordb_collection_dao.get_collection_by_name(
            collection_data.collection_name
        )
        if existing_collection:
            raise ValueError(
                f"Collection name '{collection_data.collection_name}' already exists. Please choose a different name."
            )

        # Create the collection configuration
        collection_id = self.vectordb_collection_dao.create_collection(
            collection_data, user_id
        )
        if not collection_id:
            raise ValueError("Failed to create vector DB collection configuration")

        # Get and return the created collection
        collection = self.vectordb_collection_dao.get_collection(collection_id, user_id)
        if not collection:
            raise ValueError(
                "Failed to retrieve created vector DB collection configuration"
            )

        return collection

    def get_collection(
        self, collection_id: str, user_id: str
    ) -> Optional[VectorDBCollection]:
        """Get a vector DB collection configuration by ID."""
        return self.vectordb_collection_dao.get_collection(collection_id, user_id)

    def get_collection_by_name(
        self, collection_name: str
    ) -> Optional[VectorDBCollection]:
        """Get a vector DB collection configuration by collection name."""
        return self.vectordb_collection_dao.get_collection_by_name(collection_name)

    def list_collections(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[VectorDBCollection]:
        """List vector DB collection configurations for a user."""
        return self.vectordb_collection_dao.list_collections(user_id, skip, limit)

    def update_collection(
        self, collection_id: str, user_id: str, update_data: VectorDBCollectionUpdate
    ) -> Optional[VectorDBCollection]:
        """Update a vector DB collection configuration."""
        try:
            logger.debug(
                f"Updating vector DB collection {collection_id} with data: {update_data.dict()}"
            )

            # Validate embedding model if provided
            if (
                update_data.embedding_model_provider_id
                and update_data.embedding_model_name
            ):
                self._validate_embedding_model(
                    update_data.embedding_model_provider_id,
                    update_data.embedding_model_name,
                    user_id,
                )

            # Note: Chunking configuration is handled at the job level via document splitter,
            # not at the vector DB collection level

            result = self.vectordb_collection_dao.update_collection(
                collection_id, user_id, update_data
            )
            if not result:
                raise ValueError(
                    f"Failed to update vector DB collection {collection_id} - collection not found or access denied"
                )

            logger.debug(f"Successfully updated vector DB collection {collection_id}")
            return result

        except ValueError as e:
            logger.error(
                f"Validation error updating vector DB collection {collection_id}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error updating vector DB collection {collection_id}: {e}"
            )
            raise ValueError(
                f"Failed to update vector DB collection configuration: {e}"
            )

    def delete_collection(self, collection_id: str, user_id: str) -> bool:
        """Delete a vector DB collection configuration."""
        return self.vectordb_collection_dao.delete_collection(collection_id, user_id)

    def _validate_embedding_model(
        self, provider_id: str, model_name: str, user_id: str
    ):
        """Validate embedding model configuration."""
        # TODO: Add validation logic for embedding model provider and model
        # This could check against available providers and models
        logger.debug(
            f"Validating embedding model: {provider_id}/{model_name} for user {user_id}"
        )


def get_vectordb_collection_service() -> VectorDBCollectionService:
    """Get a VectorDBCollectionService instance."""
    return VectorDBCollectionService()
