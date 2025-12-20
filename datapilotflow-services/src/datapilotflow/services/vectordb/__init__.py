"""
VectorDB services package.

This package contains services for interacting with vector databases,
including collection inspection and record retrieval.
"""

from .collection_service import (
    VectorDBCollectionService,
    get_vectordb_collection_service,
)

__all__ = [
    "VectorDBCollectionService",
    "get_vectordb_collection_service",
]
