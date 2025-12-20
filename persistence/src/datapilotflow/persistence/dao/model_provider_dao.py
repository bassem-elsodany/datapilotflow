"""
Model Provider DAO.

This module handles data access operations for unified model provider configurations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId

from src.domain.model_provider.model_provider import (
    ModelProvider,
    ModelProviderCreate,
    ModelProviderUpdate,
    ModelType,
)
from src.infrastructure.mongo.client import MongoClientWrapper


class ModelProviderDAO(MongoClientWrapper[ModelProvider]):
    """Data Access Object for model provider configurations."""

    def __init__(self):
        super().__init__(model=ModelProvider, collection_name="model_providers")

    def create_model_provider(
        self, provider_data: ModelProviderCreate, user_id: str
    ) -> Optional[str]:
        """Create a new model provider configuration."""

        # Create the model provider document
        provider_dict = {
            "name": provider_data.name,
            "provider_type": provider_data.provider_type,
            "endpoint": provider_data.endpoint,
            "api_key": provider_data.api_key,
            "description": provider_data.description,
            "is_active": provider_data.is_active,
            "timeout": provider_data.timeout,
            "embedding": (
                provider_data.embedding.model_dump()
                if provider_data.embedding
                else None
            ),
            "generative": (
                provider_data.generative.model_dump()
                if provider_data.generative
                else None
            ),
            "reranker": (
                provider_data.reranker.model_dump() if provider_data.reranker else None
            ),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": user_id,
            "updated_by": user_id,
        }

        # Insert into database
        result = self.collection.insert_one(provider_dict)
        return str(result.inserted_id) if result.inserted_id else None

    def get_model_provider(
        self, provider_id: str, user_id: str
    ) -> Optional[ModelProvider]:
        """Get a model provider configuration by ID."""
        try:
            from loguru import logger

            logger.debug(
                f"DAO: Looking for provider_id={provider_id}, user_id={user_id}"
            )

            document = self.collection.find_one(
                {"_id": ObjectId(provider_id), "created_by": user_id}
            )

            if document:
                logger.debug(f"DAO: Provider found: {document.get('name')}")
                return self._parse_single_document(document)
            else:
                # Check if provider exists for ANY user (debug only)
                any_provider = self.collection.find_one({"_id": ObjectId(provider_id)})
                if any_provider:
                    logger.error(
                        f"DAO: Provider {provider_id} exists but belongs to user: {any_provider.get('created_by')}, not {user_id}"
                    )
                else:
                    logger.error(
                        f"DAO: Provider {provider_id} not found in database at all"
                    )

            return None
        except Exception as e:
            from loguru import logger

            logger.error(f"DAO: Error in get_model_provider: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def list_model_providers(
        self,
        user_id: str,
        is_active: Optional[bool] = None,
        provider_type: Optional[str] = None,
        supported_model_type: Optional[ModelType] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelProvider]:
        """List model provider configurations for a user."""

        # Build query; values can be heterogeneous so type as Dict[str, Any]
        query: Dict[str, Any] = {"created_by": user_id}

        if is_active is not None:
            # mypy/pylance: dict value type is Any, so both bool and str are acceptable.
            query["is_active"] = bool(is_active)

        if provider_type is not None:
            query["provider_type"] = provider_type

        if supported_model_type is not None:
            query["supported_model_types"] = supported_model_type.value

        # Execute query
        cursor = (
            self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        )

        providers = []
        for document in cursor:
            providers.append(self._parse_single_document(document))

        return providers

    def update_model_provider(
        self, provider_id: str, user_id: str, update_data: ModelProviderUpdate
    ) -> bool:
        """Update an existing model provider configuration."""

        # Build update document; include only fields that are not None
        update_doc: Dict[str, Any] = {
            "updated_at": datetime.utcnow(),
            "updated_by": user_id,
        }

        for field, value in update_data.model_dump(exclude_unset=True).items():
            if value is None:
                continue
            if field in ["embedding", "generative", "reranker"]:
                # Convert ModelTypeConfig to plain dict
                update_doc[field] = (
                    value.model_dump() if hasattr(value, "model_dump") else value
                )
            else:
                update_doc[field] = value

        # Execute update
        result = self.collection.update_one(
            {"_id": ObjectId(provider_id), "created_by": user_id}, {"$set": update_doc}
        )

        return result.modified_count > 0

    def get_active_model_providers(self, user_id: str) -> List[ModelProvider]:
        """Get all active model providers for a user."""
        return self.list_model_providers(user_id, is_active=True)

    def get_providers_by_type(
        self, user_id: str, model_type: ModelType
    ) -> List[ModelProvider]:
        """Get model providers that support a specific model type."""
        return self.list_model_providers(user_id, supported_model_type=model_type)

    def get_provider_by_name(
        self, user_id: str, provider_name: str
    ) -> Optional[ModelProvider]:
        """Get a model provider by name."""
        document = self.collection.find_one(
            {"name": provider_name, "created_by": user_id}
        )

        if document:
            return self._parse_single_document(document)

        return None

    def get_provider_by_type_and_name(
        self, user_id: str, provider_type: str, provider_name: str
    ) -> Optional[ModelProvider]:
        """Get a model provider by type and name."""
        document = self.collection.find_one(
            {
                "provider_type": provider_type,
                "name": provider_name,
                "created_by": user_id,
            }
        )

        if document:
            return self._parse_single_document(document)

        return None
