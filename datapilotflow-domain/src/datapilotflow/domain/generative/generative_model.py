"""
Generative Model domain models.

This module defines the Pydantic models for generative model configurations.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class GenerativeModel(BaseModel):
    """Model representing a generative model configuration."""

    id: str = Field(description="Unique identifier for the generative model")
    name: str = Field(description="Name of the generative model")
    endpoint: str = Field(description="API endpoint for the generative model")
    supported_models: List[str] = Field(description="List of supported model names")
    api_key: str = Field(description="API key for authentication")
    description: Optional[str] = Field(
        default=None, description="Description of the generative model"
    )
    is_active: bool = Field(default=True, description="Whether the model is active")
    created_at: datetime = Field(description="Timestamp when the model was created")
    updated_at: datetime = Field(
        description="Timestamp when the model was last updated"
    )
    created_by: str = Field(description="User ID who created the model")
    updated_by: str = Field(description="User ID who last updated the model")


class GenerativeModelCreate(BaseModel):
    """Model for creating a new generative model configuration."""

    name: str = Field(description="Name of the generative model")
    endpoint: str = Field(description="API endpoint for the generative model")
    supported_models: List[str] = Field(description="List of supported model names")
    api_key: str = Field(description="API key for authentication")
    description: Optional[str] = Field(
        default=None, description="Description of the generative model"
    )
    is_active: bool = Field(default=True, description="Whether the model is active")


# Use the same model for both create and update
GenerativeModelUpdate = GenerativeModelCreate
