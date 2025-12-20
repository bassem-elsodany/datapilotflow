"""Compatibility layer for langgraph version differences."""

try:
    from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
except ImportError:
    # Fallback for langgraph versions that don't have AsyncMongoDBSaver
    from langgraph.checkpoint.mongodb import MongoDBSaver as AsyncMongoDBSaver

__all__ = ["AsyncMongoDBSaver"]
