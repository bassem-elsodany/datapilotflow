"""
Document Splitter domain models.

This module defines the domain models for managing document splitting configurations,
allowing for reusable and configurable text processing strategies.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SplitterType(str, Enum):
    """Type of text splitter to use for document processing."""

    TEXT = "text"  # Token-based splitting with size and overlap
    DOCUMENT = "document"  # Structure-based splitting for markdown
    HTML = "html"  # Structure-based splitting for HTML


class DocumentSplitter(BaseModel):
    """A reusable document splitting configuration.

    This model represents a splitter configuration that can be used across
    multiple knowledge jobs for consistent document processing.
    """

    id: str = Field(description="Unique identifier for the splitter configuration")
    user_id: str = Field(description="ID of the user who created this configuration")
    name: str = Field(description="Name of the splitter configuration")
    description: Optional[str] = Field(
        default=None, description="Description of the splitter configuration"
    )

    # Splitter type and configuration
    splitter_type: SplitterType = Field(
        description="Type of splitter to use for document processing"
    )

    # Text splitter configuration (when splitter_type = TEXT)
    chunk_size: Optional[int] = Field(
        default=None,
        description="Size of text chunks for document splitting (tokens)",
        ge=64,
        le=4096,
    )
    chunk_overlap: Optional[int] = Field(
        default=None,
        description="Overlap between consecutive chunks (tokens)",
        ge=0,
        le=512,
    )

    # Document splitter configuration (when splitter_type = DOCUMENT)
    headers_to_split_on: Optional[List[tuple[str, str]]] = Field(
        default=None,
        description="Header patterns for document structure splitting",
    )

    # HTML splitter configuration (when splitter_type = HTML)
    sections_to_split_on: Optional[List[tuple[str, str]]] = Field(
        default=None,
        description="HTML section patterns for structure splitting",
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the configuration was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the configuration was last updated",
    )
    created_by: str = Field(description="User ID who created this configuration")
    updated_by: str = Field(description="User ID who last updated this configuration")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def get_default_chunk_overlap(self) -> int:
        """Get default chunk overlap based on chunk size (15% of chunk_size)."""
        if self.chunk_size is None:
            return 32  # Default fallback
        return int(0.15 * self.chunk_size)

    def get_effective_chunk_overlap(self) -> int:
        """Get the effective chunk overlap (configured or calculated default)."""
        if self.chunk_overlap is not None:
            return self.chunk_overlap
        return self.get_default_chunk_overlap()

    def get_default_headers_to_split_on(self) -> List[tuple[str, str]]:
        """Get default header patterns for document splitting."""
        if self.splitter_type == SplitterType.HTML:
            return [
                ("h1", "Header 1"),
                ("h2", "Header 2"),
                ("h3", "Header 3"),
                ("h4", "Header 4"),
            ]
        else:  # DOCUMENT (markdown)
            return [
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
                ("####", "Header 4"),
            ]

    def get_effective_headers_to_split_on(self) -> List[tuple[str, str]]:
        """Get the effective headers (configured or default)."""
        if self.headers_to_split_on is not None:
            return self.headers_to_split_on
        return self.get_default_headers_to_split_on()

    def get_default_sections_to_split_on(self) -> List[tuple[str, str]]:
        """Get default section patterns for HTML splitting."""
        return [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
            ("h4", "Header 4"),
        ]

    def get_effective_sections_to_split_on(self) -> List[tuple[str, str]]:
        """Get the effective sections (configured or default)."""
        if self.sections_to_split_on is not None:
            return self.sections_to_split_on
        return self.get_default_sections_to_split_on()


class DocumentSplitterCreate(BaseModel):
    """Model for creating a new document splitter configuration."""

    name: str = Field(description="Name of the splitter configuration")
    description: Optional[str] = Field(
        default=None, description="Description of the splitter configuration"
    )

    splitter_type: SplitterType = Field(
        description="Type of splitter to use for document processing"
    )

    # Text splitter configuration (when splitter_type = TEXT)
    chunk_size: Optional[int] = Field(
        default=None,
        description="Size of text chunks for document splitting (tokens) - required for TEXT type",
        ge=64,
        le=4096,
    )
    chunk_overlap: Optional[int] = Field(
        default=None,
        description="Overlap between consecutive chunks (tokens). If None, uses 15% of chunk_size",
        ge=0,
        le=512,
    )

    # Document splitter configuration (when splitter_type = DOCUMENT)
    headers_to_split_on: Optional[List[tuple[str, str]]] = Field(
        default=None,
        description="Header patterns for document structure splitting. If None, uses default patterns",
    )


class DocumentSplitterUpdate(BaseModel):
    """Model for updating an existing document splitter configuration.

    All fields are optional to allow partial updates.
    """

    name: Optional[str] = Field(
        default=None, description="Name of the splitter configuration"
    )
    description: Optional[str] = Field(
        default=None, description="Description of the splitter configuration"
    )
    splitter_type: Optional[SplitterType] = Field(
        default=None, description="Type of splitter to use for document processing"
    )
    chunk_size: Optional[int] = Field(
        default=None,
        description="Size of text chunks for document splitting (tokens)",
        ge=64,
        le=4096,
    )
    chunk_overlap: Optional[int] = Field(
        default=None,
        description="Overlap between consecutive chunks (tokens)",
        ge=0,
        le=512,
    )
    headers_to_split_on: Optional[List[tuple[str, str]]] = Field(
        default=None, description="Header patterns for document structure splitting"
    )
