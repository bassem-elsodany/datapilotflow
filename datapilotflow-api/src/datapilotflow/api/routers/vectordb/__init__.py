"""
VectorDB API routers package.

This package contains FastAPI routers for vector database operations.
"""

from .collection_router import router as collection_router

__all__ = ["collection_router"]
