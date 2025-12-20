"""
Knowledge services.

This subpackage contains all knowledge-related services for
managing knowledge ingestion and processing.
"""

try:
    from .knowledge_ingestion_service import KnowledgeIngestionService
except ImportError as e:
    # Handle missing dependencies gracefully
    import warnings
    warnings.warn(f"KnowledgeIngestionService not available: {e}")
    KnowledgeIngestionService = None
from .knowledge_source_service import KnowledgeSourceService, get_knowledge_source_service
from .knowledge_job_service import KnowledgeJobService, get_knowledge_job_service
from .document_splitter_service import DocumentSplitterService, get_document_splitter_service

__all__ = [
    # Knowledge Services
    "KnowledgeIngestionService",
    "KnowledgeSourceService",
    "get_knowledge_source_service",
    "KnowledgeJobService",
    "get_knowledge_job_service",
    "DocumentSplitterService",
    "get_document_splitter_service",
]
