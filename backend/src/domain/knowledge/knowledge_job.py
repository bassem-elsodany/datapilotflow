"""
Knowledge Job domain models.

This module defines the domain models for managing knowledge processing jobs,
including job status, execution details, and results.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Status of a knowledge processing job."""

    CREATED = "created"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class KnowledgeJob(BaseModel):
    """A knowledge processing job created from a knowledge source configuration.

    This model represents a job that processes a knowledge source configuration
    to extract and store knowledge data.
    """

    id: str = Field(description="Unique identifier for the job")
    knowledge_source_config_id: str = Field(
        description="ID of the knowledge source configuration this job is based on"
    )
    vectordb_collection_id: str = Field(
        description="ID of the vector database collection configuration to use"
    )
    user_id: str = Field(description="ID of the user who created this job")
    name: str = Field(description="Name of the job")
    description: Optional[str] = Field(
        default=None, description="Description of the job"
    )

    # Document splitter configuration reference
    splitter_id: Optional[str] = Field(
        default=None,
        description="ID of the document splitter configuration to use for this job",
    )

    # Optional overrides for splitter configuration (for text splitters)
    custom_chunk_size: Optional[int] = Field(
        default=None,
        description="Override chunk size for text splitters (if different from splitter config)",
        ge=64,
        le=4096,
    )
    custom_chunk_overlap: Optional[int] = Field(
        default=None,
        description="Override chunk overlap for text splitters (if different from splitter config)",
        ge=0,
        le=512,
    )

    # Job processing configuration
    batch_size: int = Field(
        default=100,
        description="Number of documents to process in each batch",
        ge=1,
        le=1000,
    )

    # File output configuration
    save_to_file: bool = Field(
        default=False, description="Whether to save extracted content to files"
    )
    write_consolidated_file: bool = Field(
        default=False,
        description="Whether to write all content to a single consolidated file (memory intensive)",
    )

    # Collection management
    clear_collection_before_start: bool = Field(
        default=False,
        description="Whether to clear all existing data from the collection before starting the job",
    )
    check_duplicates_before_insert: bool = Field(
        default=False,
        description="Whether to check for duplicate URLs before inserting new records",
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the job was created"
    )
    created_by: str = Field(description="User ID who created this job")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class KnowledgeJobCreate(BaseModel):
    """Model for creating a new knowledge processing job."""

    name: str = Field(description="Name of the job")
    description: Optional[str] = Field(
        default=None, description="Description of the job"
    )

    # Document splitter configuration reference (use existing splitter)
    splitter_id: Optional[str] = Field(
        default=None,
        description="ID of the document splitter configuration to use for this job",
    )

    # Inline splitter creation (alternative to splitter_id)
    splitter_name: Optional[str] = Field(
        default=None,
        description="Name for new splitter configuration (if creating inline)",
    )
    splitter_description: Optional[str] = Field(
        default=None,
        description="Description for new splitter configuration",
    )
    splitter_type: Optional[str] = Field(
        default=None,
        description="Type of splitter: 'text' or 'document'",
    )

    # Optional overrides for splitter configuration (for text splitters)
    custom_chunk_size: Optional[int] = Field(
        default=None,
        description="Chunk size for text splitters (tokens)",
        ge=64,
        le=4096,
    )
    custom_chunk_overlap: Optional[int] = Field(
        default=None,
        description="Chunk overlap for text splitters (tokens)",
        ge=0,
        le=512,
    )

    # Vector DB Collection Configuration (embedded in job creation)
    vectordb_collection_description: Optional[str] = Field(
        default=None,
        description="Description of the vector DB collection configuration",
    )
    embedding_model_provider_id: Optional[str] = Field(
        default=None, description="ID of the model provider for embedding generation"
    )
    embedding_model_name: Optional[str] = Field(
        default=None, description="Name of the specific embedding model to use"
    )
    vector_dimension: Optional[int] = Field(
        default=None,
        description="Dimension of the vector embeddings generated by the model",
        ge=1,
        le=4096,
    )
    collection_name: Optional[str] = Field(
        default=None, description="Name of the vector database collection"
    )

    # Existing collection option
    existing_collection_id: Optional[str] = Field(
        default=None, description="ID of existing vector DB collection to use"
    )

    # Job processing configuration
    batch_size: int = Field(
        default=100,
        description="Number of documents to process in each batch",
        ge=1,
        le=1000,
    )
    save_to_file: bool = Field(
        default=False, description="Whether to save extracted content to files"
    )
    write_consolidated_file: bool = Field(
        default=False,
        description="Whether to write all content to a single consolidated file (memory intensive)",
    )

    # Collection management
    clear_collection_before_start: bool = Field(
        default=False,
        description="Whether to clear all existing data from the collection before starting the job",
    )
    check_duplicates_before_insert: bool = Field(
        default=False,
        description="Whether to check for duplicate URLs before inserting new records",
    )


# Use the same model for both create and update
KnowledgeJobUpdate = KnowledgeJobCreate


class KnowledgeJobExpanded(KnowledgeJob):
    """Expanded knowledge job model with related data."""

    # Related data (optional, populated based on query parameters)
    knowledge_source_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Full knowledge source configuration data"
    )
    vectordb_collection: Optional[Dict[str, Any]] = Field(
        default=None, description="Full vector database collection data"
    )
    document_splitter: Optional[Dict[str, Any]] = Field(
        default=None, description="Full document splitter configuration data"
    )
    timeline: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Job execution timeline entries"
    )
    execution_stats: Optional[Dict[str, Any]] = Field(
        default=None, description="Job execution statistics"
    )
