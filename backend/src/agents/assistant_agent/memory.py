"""
Long-term Memory Integration for Deep Agent.

Implements persistent memory using LangGraph's Store.
Allows agents to remember information across conversations.
"""

from typing import Optional

from langgraph.store.memory import InMemoryStore
from loguru import logger

from src.config import settings

# Global memory store instance
_memory_store: Optional[InMemoryStore] = None


def get_memory_store() -> InMemoryStore:
    """
    Get or create the global memory store.

    Returns:
        InMemoryStore instance for long-term memory
    """
    global _memory_store

    if _memory_store is None:
        logger.info("Initializing long-term memory store for deep agents")

        # TODO: Use MongoDB-backed store for production
        # For now, use InMemoryStore (ephemeral)
        _memory_store = InMemoryStore()

        logger.info("Memory store initialized (InMemoryStore)")

    return _memory_store


def create_memory_namespace(user_id: str, conversation_id: Optional[str] = None) -> str:
    """
    Create a namespace for memory storage.

    Args:
        user_id: User ID
        conversation_id: Optional conversation ID (for conversation-specific memory)

    Returns:
        Namespace string for memory store
    """
    if conversation_id:
        return f"user:{user_id}:conversation:{conversation_id}"
    else:
        return f"user:{user_id}:global"


# TODO: Implement MongoDBStore for production
# from langgraph.store.mongodb import MongoDBStore
#
# def get_production_memory_store() -> MongoDBStore:
#     """Get MongoDB-backed memory store for production."""
#     return MongoDBStore(
#         connection_string=settings.MONGO_URI,
#         db_name="agent_memory",
#     )
