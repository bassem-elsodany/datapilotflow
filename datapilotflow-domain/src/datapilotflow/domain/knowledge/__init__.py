"""
Knowledge domain models.

This subpackage contains all knowledge-related domain models for
managing knowledge sources, extraction, and factory patterns.
"""

from .document_splitter import *
from .job_timeline import *
from .knowledge import *
from .knowledge_job import *

# from .knowledge_factory import *  # Deprecated - removed as part of API migration
from .knowledge_source_config import *
from .llm_content_filter_config import *
from .vectordb_collection import *

__all__ = [
    # Knowledge Models
    "KnowledgeExtract",
    "Knowledge",
    # Knowledge Factory (deprecated - removed as part of API migration)
    # "MarkdownGeneratorConfig",
    # "CrawlerConfig",
    # "BrowserConfig",
    # "URLPattern",
    # "URLSourceConfig",
    # "KnowledgeConfig",
    # "KnowledgeFactory",
    # Knowledge Source Configuration
    "ContentSourceType",
    "ScrapingMode",
    "ConfluenceConfig",
    "KnowledgeSourceConfig",
    "KnowledgeSourceConfigCreate",
    "KnowledgeSourceConfigUpdate",
    # Document Splitter Configuration
    "DocumentSplitter",
    "DocumentSplitterCreate",
    "DocumentSplitterUpdate",
    "SplitterType",
    # Knowledge Job
    "JobStatus",
    "KnowledgeJob",
    "KnowledgeJobCreate",
    "KnowledgeJobUpdate",
    # Vector DB Collection Configuration
    "VectorDBCollection",
    "VectorDBCollectionCreate",
    "VectorDBCollectionUpdate",
    # Job Timeline
    "JobTimeline",
    "JobTimelineCreate",
    "JobTimelineUpdate",
    # LLM Content Filter Configuration
    "LLMContentFilterConfig",
    "LLMContentFilterConfigCreate",
    "LLMContentFilterConfigUpdate",
]
