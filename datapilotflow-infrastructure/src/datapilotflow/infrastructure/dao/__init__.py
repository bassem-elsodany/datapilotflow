"""
Data Access Objects (DAOs) - Central access point for all database operations.

This package contains all MongoDB Data Access Objects (DAOs) organized by domain.
Each domain has its own subpackage for better organization and separation of concerns.
"""

# Auth DAOs
from .auth import AuthDAO, RolesDAO

# File Management DAOs
from .file_management import RagFailedEventService, RagFileUploadService

# Knowledge DAOs
from .knowledge import (
    DocumentSplitterDAO,
    JobTimelineDAO,
    KnowledgeJobDAO,
    KnowledgeSourceDAO,
    LLMContentFilterDAO,
    UrlSourceDAO,
)

# Model Provider DAOs
from .model_provider import ModelProviderDAO

# Notification DAOs
from .notification import NotificationService

# Tool DAOs
from .tool import MCPServerDAO, ToolDAO

# Vector DB DAOs
from .vectordb import VectorDBCollectionDAO

__all__ = [
    # Auth DAOs
    "AuthDAO",
    "RolesDAO",
    # Knowledge DAOs
    "KnowledgeJobDAO",
    "KnowledgeSourceDAO",
    "UrlSourceDAO",
    "DocumentSplitterDAO",
    "JobTimelineDAO",
    "LLMContentFilterDAO",
    # File Management DAOs
    "RagFileUploadService",
    "RagFailedEventService",
    # Model Provider DAOs
    "ModelProviderDAO",
    # Notification DAOs
    "NotificationService",
    # Tool DAOs
    "ToolDAO",
    "MCPServerDAO",
    # Vector DB DAOs
    "VectorDBCollectionDAO",
]
