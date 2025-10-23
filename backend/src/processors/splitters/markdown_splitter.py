"""
Markdown Splitter Implementation.

This module provides a markdown-based document splitter that uses
document structure (headers) for splitting while preserving semantic coherence.
"""

from typing import List

from langchain.schema import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter
from loguru import logger

from src.domain.knowledge.document_splitter import DocumentSplitter

from .base import BaseSplitter


class MarkdownSplitter(BaseSplitter):
    """Markdown splitter for structured content using header-based splitting.

    This splitter uses MarkdownHeaderTextSplitter to split documents based on
    markdown header structure, preserving semantic coherence by respecting
    document organization.
    """

    def __init__(self, splitter_config: DocumentSplitter):
        """Initialize the markdown splitter.

        Args:
            splitter_config: DocumentSplitter configuration
        """
        super().__init__(splitter_config)

        # Validate that this is a DOCUMENT splitter
        if splitter_config.splitter_type.value != "document":
            raise ValueError(
                f"MarkdownSplitter requires DOCUMENT splitter_type, got {splitter_config.splitter_type}"
            )

        # Get header configuration
        self.headers_to_split_on = splitter_config.get_effective_headers_to_split_on()

        # Create the underlying splitter once during initialization
        self._splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False,  # Keep headers in chunks for context
            return_each_line=False,  # Aggregate lines by headers
        )

        logger.debug(
            f"MarkdownSplitter configured with headers: {self.headers_to_split_on}"
        )

    def split(self, text: str) -> List[Document]:
        """Split text into chunks using markdown header structure.

        Args:
            text: The markdown text content to split

        Returns:
            List[Document]: List of Document chunks
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to split")
            return []
        # Use the pre-created splitter
        chunk_docs = self._splitter.split_text(text)

        return chunk_docs
