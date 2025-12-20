"""
VectorDB Collection domain models.

This module defines Pydantic models for representing vector database
collections, schemas, statistics, and records.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FieldSchema(BaseModel):
    """Schema for a field in a vector collection."""

    name: str = Field(description="Field name")
    type: str = Field(
        description="Field data type (e.g., VARCHAR, INT64, FLOAT_VECTOR)"
    )
    is_primary: bool = Field(
        default=False, description="Whether this is the primary key"
    )
    auto_id: bool = Field(default=False, description="Whether ID is auto-generated")
    dimension: Optional[int] = Field(
        default=None, description="Vector dimension (for FLOAT_VECTOR type)"
    )
    max_length: Optional[int] = Field(
        default=None, description="Maximum length (for VARCHAR type)"
    )
    indexed: bool = Field(default=False, description="Whether field has an index")


class CollectionInfo(BaseModel):
    """Information about a vector collection."""

    id: str = Field(description="Collection ID (name)")
    name: str = Field(description="Collection display name")
    description: Optional[str] = Field(
        default=None, description="Collection description"
    )
    dimension: int = Field(description="Vector dimension")
    record_count: int = Field(description="Total number of records in collection")
    metric_type: Optional[str] = Field(
        default=None, description="Distance metric type (e.g., COSINE, L2)"
    )
    index_type: Optional[str] = Field(
        default=None, description="Index type (e.g., IVF_FLAT, HNSW)"
    )
    created_at: Optional[datetime] = Field(
        default=None, description="When the collection was created"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="When the collection was last updated"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class CollectionSchema(BaseModel):
    """Schema information for a vector collection."""

    collection_id: str = Field(description="Collection ID")
    fields: List[FieldSchema] = Field(description="List of field schemas")


class CollectionStats(BaseModel):
    """Statistical information about a vector collection."""

    collection_id: str = Field(description="Collection ID")
    total_records: int = Field(description="Total number of records")
    records_by_job: Dict[str, int] = Field(
        default_factory=dict,
        description="Number of records per job ID",
    )
    date_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range of records (earliest and latest)",
    )
    avg_content_length: Optional[int] = Field(
        default=None, description="Average content length"
    )
    unique_sources: Optional[int] = Field(
        default=None, description="Number of unique source URLs"
    )


class VectorRecord(BaseModel):
    """A single record from a vector collection (without the vector)."""

    id: str = Field(description="Record ID")
    source_url: Optional[str] = Field(default=None, description="Source URL")
    job_id: Optional[str] = Field(
        default=None, description="Job ID that created this record"
    )
    title: Optional[str] = Field(default=None, description="Document title")
    page_content: Optional[str] = Field(default=None, description="Page content")
    chunk_index: Optional[int] = Field(default=None, description="Chunk index")
    total_chunks: Optional[int] = Field(
        default=None, description="Total chunks in document"
    )
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    # Additional fields as dict for flexibility
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata fields"
    )

    class Config:
        extra = "allow"  # Allow additional fields


class RecordResponse(BaseModel):
    """Response model for paginated record retrieval."""

    collection_id: str = Field(description="Collection ID")
    total: int = Field(description="Total number of records matching the query")
    limit: int = Field(description="Number of records per page")
    offset: int = Field(description="Offset for pagination")
    records: List[VectorRecord] = Field(description="List of records")
