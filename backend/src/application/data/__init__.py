"""
Data processing module for SkillPilot.

This module provides comprehensive data processing capabilities including:
- Document extraction and processing
- Text chunking and splitting
- Storage and retrieval operations
- Deduplication and quality control
"""

# Core processing components (moved to processors.document)
# Note: Import these directly from src.processors.document.* to avoid circular imports
# from src.processors.document.base_processor import BaseDocumentProcessor
# from src.processors.document.file_processor import FileProcessor, extract_content, extract_text, extract_markdown

# Text processing and chunking
from .utils.chunk_manager import ChunkManager

# LLM components (removed - no longer supported)

# Storage and retrieval
from .storage import (
    MilvusProcessor,
    create_milvus_processor,
    DuplicateDetector,
    write_enriched_documents_to_file,
    write_enriched_markdown_to_file
)

# Deduplication
from .deduplicate_documents import deduplicate_documents

# Batch processing utilities (moved to processors.document)
# Note: Import these directly from src.processors.document.* to avoid circular imports
# from src.processors.document.web_document_processor import get_extraction_generator, extract_with_batch_processing_callback

# Domain models
from src.domain.rag.knowledge_chunk import KnowledgeChunk

# Configuration
from src.config import settings

__all__ = [
    # Core processing (moved to processors.document - import directly)
    # "BaseDocumentProcessor",
    # "FileProcessor",
    
    # File processing utilities (moved to processors.document - import directly)
    # "extract_content",
    # "extract_text", 
    # "extract_markdown",
    
    # Text processing
    "ChunkManager",
    
    # LLM components (removed - no longer supported)
    
    # Storage and retrieval
    "MilvusProcessor",
    "create_milvus_processor",
    "DuplicateDetector",
    "write_enriched_documents_to_file",
    "write_enriched_markdown_to_file",
    
    # Deduplication
    "deduplicate_documents",
    
    # Batch processing (moved to processors.document - import directly)
    # "get_extraction_generator",
    # "extract_with_batch_processing_callback",
    
    # Domain models
    "KnowledgeChunk",
    
    # Configuration
    "settings",
]
