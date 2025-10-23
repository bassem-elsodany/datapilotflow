"""
Knowledge chunk domain model for SkillPilot.

This module defines the KnowledgeChunk model used for storing and retrieving
document chunks in vector databases with enhanced knowledge graph properties.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class KnowledgeChunk(BaseModel):
    """
    Model representing a document chunk stored in vector databases.

    This model includes standard document properties as well as enhanced
    knowledge graph properties for improved search and retrieval capabilities.

    Attributes:
        id: Unique identifier from the vector database
        page_content: The actual text content of the chunk
        source_url: URL where the content was extracted from
        job_id: Identifier of the knowledge processing job that created this chunk
        knowledge_source: Identifier for the knowledge source
        title: Title of the document or section
        chunk_id: Unique identifier for this chunk
        chunk_index: Position of this chunk within the document
        total_chunks: Total number of chunks in the document
        entities: List of entities extracted from the content
        relationships: List of relationships between entities
        tags: List of tags for categorization
    """

    id: Optional[str] = None  # UUID from Weaviate
    page_content: Optional[str]
    source_url: Optional[str]
    job_id: Optional[str] = None  # Knowledge processing job ID
    knowledge_source: Optional[str]
    title: Optional[str]
    chunk_id: Optional[str]
    chunk_index: Optional[int]
    total_chunks: Optional[int]
    # Enhanced searchable knowledge graph properties
    entities: Optional[List[str]] = None  # ["OAuth2:IS:PROTOCOL", "API:IS:SERVICE"]
    relationships: Optional[List[str]] = None  # ["OAuth2:IMPLEMENTS:Authentication"]
    tags: Optional[List[str]] = None  # ["security", "authentication"]
    model_config = ConfigDict(extra="ignore")
