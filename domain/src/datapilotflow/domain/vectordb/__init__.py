"""
VectorDB domain models package.

This package contains domain models for vector database operations,
including collection management, schema inspection, and record retrieval.
"""

from .collection_models import (
    CollectionInfo,
    CollectionSchema,
    CollectionStats,
    FieldSchema,
    RecordResponse,
    VectorRecord,
)

__all__ = [
    "CollectionInfo",
    "CollectionSchema",
    "CollectionStats",
    "FieldSchema",
    "RecordResponse",
    "VectorRecord",
]
