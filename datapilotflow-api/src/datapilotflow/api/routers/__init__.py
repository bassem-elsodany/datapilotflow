"""
API routers package.

Contains all REST endpoint routers for different domains organized by functionality.
"""

# Import from subpackages
from .agent import agent_router, assistant_router, rag_router
from .auth import auth_router
from .conversation import conversation_router
from .health import health_router
from .knowledge import knowledge_source_router
from .knowledge.document_splitter_router import router as document_splitter_router
from .knowledge.knowledge_collection_router import knowledge_collection_router
from .knowledge.knowledge_job_router import router as knowledge_job_router
from .knowledge.knowledge_router import router as knowledge_router
from .knowledge.knowledge_source_preview_router import (
    router as knowledge_source_preview_router,
)
from .knowledge.llm_content_filter_router import router as llm_content_filter_router
from .model_provider import router as model_provider_router
from .notifications import notification_router, notification_websocket_router
from .tools import mcp_servers_router, tools_router
from .vectordb.collection_router import router as vectordb_collection_router
from .users import roles_router, users_router

__all__ = [
    "agent_router",
    "rag_router",
    "assistant_router",
    "auth_router",
    "knowledge_router",
    "knowledge_source_router",
    "knowledge_source_preview_router",
    "knowledge_job_router",
    "knowledge_collection_router",
    "document_splitter_router",
    "vectordb_collection_router",
    "llm_content_filter_router",
    "model_provider_router",
    "conversation_router",
    "tools_router",
    "mcp_servers_router",
    "notification_router",
    "notification_websocket_router",
    "health_router",
    "roles_router",
    "users_router",
]
