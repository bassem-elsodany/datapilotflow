"""
Domain layer containing core business logic and entities.

This package is organized into logical subpackages:
- core: Core domain models and exceptions
- notification: Notification system models
- knowledge: Knowledge management models
- rag: RAG (Retrieval-Augmented Generation) models
- llm_prompts: LLM prompt management
- user: User and role management models
"""

# Import and export all subpackages
from . import core
from . import notification
from . import knowledge
from . import embedding
from . import generative
from . import rag
from . import llm_prompts
from . import user
from . import events

__all__ = [
    "core",
    "notification",
    "knowledge",
    "embedding",
    "generative",
    "rag",
    "llm_prompts",
    "user",
    "events"
] 