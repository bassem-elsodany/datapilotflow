"""
Document Processing Package.

This package contains all document processing logic including:
- Base document processor classes
- File processing and extraction
- Web document processing
- Document extraction APIs
"""

from .base_processor import BaseDocumentProcessor
from .file_processor import FileProcessor
from .web_document_processor import (
    WebDocumentProcessor,
    extract,
    extract_with_batch_processing_callback,
    get_extraction_generator,
    get_knowledge_source_documents
)
# Graph functionality removed - no longer used

__all__ = [
    # Base processor
    "BaseDocumentProcessor",
    
    # File processing
    "FileProcessor",
    
    # Web document processing
    "WebDocumentProcessor",
    "extract",
    "extract_with_batch_processing_callback",
    "get_extraction_generator",
    "get_knowledge_source_documents",
    
    # Graph functionality removed - no longer used
]
