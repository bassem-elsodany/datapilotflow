"""
Unified Model Provider domain models.

This module defines the Pydantic models for unified model provider configurations
that support both embedding and generative models from the same provider.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ModelType(str, Enum):
    """Enumeration of supported model types."""

    EMBEDDING = "embedding"
    GENERATIVE = "generative"
    RERANKER = "reranker"
    BOTH = "both"  # Provider supports multiple model types


class ModelTypeConfig(BaseModel):
    """Configuration for a specific model type."""

    models: List[str] = Field(description="List of supported model names for this type")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Configuration specific to this model type"
    )


class ModelProvider(BaseModel):
    """Model representing a unified model provider configuration."""

    id: str = Field(description="Unique identifier for the model provider")
    name: str = Field(
        description="Name of the model provider (e.g., 'OpenAI', 'Anthropic')"
    )
    provider_type: str = Field(
        description="Type of provider (e.g., 'openai', 'anthropic', 'google')"
    )
    endpoint: str = Field(description="Base API endpoint for the provider")
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication (can be None for providers like Ollama)",
    )
    api_key_env_var: Optional[str] = Field(
        default=None,
        description="Environment variable name for API key (e.g., 'OPENAI_API_KEY')",
    )
    description: Optional[str] = Field(
        default=None, description="Description of the model provider"
    )
    is_active: bool = Field(default=True, description="Whether the provider is active")

    # Model parameters
    timeout: int = Field(
        default=60,
        description="Request timeout in seconds for all model types",
        ge=1,
        le=300,
    )

    # Nested model type configurations
    embedding: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Embedding model configuration (models list and config)",
    )
    generative: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Generative model configuration (models list and config)",
    )
    reranker: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Reranker model configuration (models list and config)",
    )

    # Metadata
    created_at: datetime = Field(description="Timestamp when the provider was created")
    updated_at: datetime = Field(
        description="Timestamp when the provider was last updated"
    )
    created_by: str = Field(description="User ID who created the provider")
    updated_by: str = Field(description="User ID who last updated the provider")

    @property
    def supported_model_types(self) -> List[ModelType]:
        """Get list of supported model types based on available configurations."""
        types = []
        if self.embedding is not None:
            types.append(ModelType.EMBEDDING)
        if self.generative is not None:
            types.append(ModelType.GENERATIVE)
        if self.reranker is not None:
            types.append(ModelType.RERANKER)
        return types

    @property
    def embedding_models(self) -> List[str]:
        """Get list of embedding models."""
        return self.embedding.models if self.embedding else []

    @property
    def generative_models(self) -> List[str]:
        """Get list of generative models."""
        return self.generative.models if self.generative else []

    @property
    def reranker_models(self) -> List[str]:
        """Get list of reranker models."""
        return self.reranker.models if self.reranker else []

    @property
    def api_key_required(self) -> bool:
        """Property to indicate if API key is required for this provider."""
        return self.api_key_env_var is not None

    def get_api_key_env_var(self) -> Optional[str]:
        """Get the environment variable name for the API key."""
        return self.api_key_env_var

    def requires_api_key(self) -> bool:
        """Check if this provider requires an API key."""
        return self.api_key_required


class ModelProviderCreate(BaseModel):
    """Model for creating a new model provider configuration."""

    name: str = Field(description="Name of the model provider")
    provider_type: str = Field(description="Type of provider")
    endpoint: str = Field(description="Base API endpoint for the provider")
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication (can be None for providers like Ollama)",
    )
    api_key_env_var: Optional[str] = Field(
        default=None,
        description="Environment variable name for API key (e.g., 'OPENAI_API_KEY')",
    )
    description: Optional[str] = Field(
        default=None, description="Description of the model provider"
    )
    is_active: bool = Field(default=True, description="Whether the provider is active")

    # Model parameters
    timeout: int = Field(
        default=60,
        description="Request timeout in seconds for all model types",
        ge=1,
        le=300,
    )

    # Nested model type configurations
    embedding: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Embedding model configuration (models list and config)",
    )
    generative: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Generative model configuration (models list and config)",
    )
    reranker: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Reranker model configuration (models list and config)",
    )


# Use the same model for both create and update
ModelProviderUpdate = ModelProviderCreate


class ModelProviderResponse(BaseModel):
    """Response model for model provider that excludes sensitive information."""

    id: str = Field(description="Unique identifier for the model provider")
    name: str = Field(description="Name of the model provider")
    provider_type: str = Field(description="Type of provider")
    endpoint: str = Field(description="Base API endpoint for the provider")
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication (full key, UI will mask it for display)",
    )
    api_key_env_var: Optional[str] = Field(
        default=None,
        description="Environment variable name for API key (e.g., 'OPENAI_API_KEY')",
    )
    description: Optional[str] = Field(
        default=None, description="Description of the model provider"
    )
    is_active: bool = Field(description="Whether the provider is active")

    # Model parameters
    timeout: int = Field(description="Request timeout in seconds for all model types")

    # Nested model type configurations
    embedding: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Embedding model configuration (models list and config)",
    )
    generative: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Generative model configuration (models list and config)",
    )
    reranker: Optional[ModelTypeConfig] = Field(
        default=None,
        description="Reranker model configuration (models list and config)",
    )

    # Metadata
    created_at: datetime = Field(description="Timestamp when the provider was created")
    updated_at: datetime = Field(
        description="Timestamp when the provider was last updated"
    )
    created_by: str = Field(description="User ID who created the provider")
    updated_by: str = Field(description="User ID who last updated the provider")

    @property
    def supported_model_types(self) -> List[ModelType]:
        """Get list of supported model types based on available configurations."""
        types = []
        if self.embedding is not None:
            types.append(ModelType.EMBEDDING)
        if self.generative is not None:
            types.append(ModelType.GENERATIVE)
        if self.reranker is not None:
            types.append(ModelType.RERANKER)
        return types

    @property
    def embedding_models(self) -> List[str]:
        """Get list of embedding models."""
        return self.embedding.models if self.embedding else []

    @property
    def generative_models(self) -> List[str]:
        """Get list of generative models."""
        return self.generative.models if self.generative else []

    @property
    def reranker_models(self) -> List[str]:
        """Get list of reranker models."""
        return self.reranker.models if self.reranker else []

    @property
    def api_key_required(self) -> bool:
        """Property to indicate if API key is required for this provider."""
        return self.api_key_env_var is not None

    def get_api_key_env_var(self) -> Optional[str]:
        """Get the environment variable name for the API key."""
        return self.api_key_env_var

    def requires_api_key(self) -> bool:
        """Check if this provider requires an API key."""
        return self.api_key_required
