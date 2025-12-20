"""
MongoDB infrastructure package.

This package contains the MongoDB client wrapper and base infrastructure.
The actual DAO services have been moved to their respective application service packages.
"""

from .client import MongoClientWrapper

__all__ = [
    "MongoClientWrapper"
]
