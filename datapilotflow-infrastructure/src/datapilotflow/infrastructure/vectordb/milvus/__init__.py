"""
Milvus infrastructure package.

This package contains the Milvus client wrapper and base infrastructure
for vector database operations.
"""

from .client import MilvusClientWrapper

__all__ = [
    "MilvusClientWrapper"
]
