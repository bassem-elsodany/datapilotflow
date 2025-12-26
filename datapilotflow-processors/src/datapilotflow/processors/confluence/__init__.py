"""
Confluence API integration module.

Provides client and extractor for integrating Confluence Cloud API
for document extraction as an alternative to web crawling.
"""

from .confluence_api_client import (
    ConfluenceApiClient,
    ConfluenceAuthenticationError,
    ConfluencePageNotFoundError,
    ConfluenceRateLimitError,
    ConfluencePage,
    ConfluenceServerError,
)
from .confluence_document_extractor import ConfluenceDocumentExtractor

__all__ = [
    # API Client
    "ConfluenceApiClient",
    "ConfluencePage",
    # Exceptions
    "ConfluenceAuthenticationError",
    "ConfluencePageNotFoundError",
    "ConfluenceRateLimitError",
    "ConfluenceServerError",
    # Document Extractor
    "ConfluenceDocumentExtractor",
]
