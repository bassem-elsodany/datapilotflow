"""
API routers package.

Contains all REST endpoint routers for different domains organized by functionality.
"""

# Import all routers
from . import health, auth, agents, conversations, knowledge, model_provider, notifications, tools, users, vectordb

__all__ = [
    "health",
    "auth",
    "agents",
    "conversations",
    "knowledge",
    "model_provider",
    "notifications",
    "tools",
    "users",
    "vectordb",
]
