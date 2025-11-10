"""
Routers Package

This package contains all the FastAPI routers for the SkillPilot API,
organized by functionality for better maintainability.
"""

# Import from subpackages
from .agent import rag_router, supervisor_router
from .auth import auth_router
from .conversation import conversation_router
from .health import health_router
from .knowledge import knowledge_source_router
from .knowledge.document_splitter_router import router as document_splitter_router
from .knowledge.knowledge_collection_router import knowledge_collection_router
from .knowledge.knowledge_job_router import router as knowledge_job_router
from .knowledge.knowledge_router import router as knowledge_router
from .knowledge.llm_content_filter_router import router as llm_content_filter_router
from .knowledge.pipeline_router import router as pipeline_router
from .model_provider import router as model_provider_router
from .notifications import notification_router, notification_websocket_router
from .tools import tools_router
from .vectordb.collection_router import router as vectordb_collection_router

__all__ = [
    "rag_router",
    "supervisor_router",
    "auth_router",
    "knowledge_router",
    "knowledge_source_router",
    "knowledge_job_router",
    "knowledge_collection_router",
    "document_splitter_router",
    "vectordb_collection_router",
    "llm_content_filter_router",
    "pipeline_router",
    "model_provider_router",
    "conversation_router",
    "tools_router",
    "notification_router",
    "notification_websocket_router",
    "health_router",
]
