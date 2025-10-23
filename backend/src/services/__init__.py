"""
Application services package containing business logic services.

This package is organized into logical subpackages:
- notification: Notification system services
- auth: Authentication and authorization services
- knowledge: Knowledge management services
- rag: RAG (Retrieval-Augmented Generation) services
- conversation: Conversation and chat services
- file_management: File upload and processing services
- users: User management and roles services
- model_provider: Unified model provider services (replaces old embedding/generative services)
"""

# Import and export all subpackages
from . import notification
from . import auth
from . import knowledge
from . import model_provider
from . import rag
from . import conversation
from . import file_management
from . import users
from . import events
from . import events_publisher
from . import events_listeners

__all__ = [
    "notification",
    "auth",
    "knowledge",
    "model_provider",
    "rag",
    "conversation",
    "file_management",
    "users",
    "events",
    "events_publisher",
    "events_listeners"
]
