"""
HTML Splitter Implementation.

This module provides an HTML-based document splitter that uses
document structure (HTML headers) for splitting while preserving semantic coherence.
"""

from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import HTMLHeaderTextSplitter, HTMLSectionSplitter
from loguru import logger

from src.domain.knowledge.document_splitter import DocumentSplitter

from .base import BaseSplitter


class HTMLSplitter(BaseSplitter):
    """HTML splitter for structured content using header-based splitting.

    This splitter uses HTMLHeaderTextSplitter to split documents based on
    HTML header structure (h1, h2, h3, etc.), preserving semantic coherence by respecting
    document organization.
    """

    def __init__(self, splitter_config: DocumentSplitter):
        """Initialize the HTML splitter.

        Args:
            splitter_config: DocumentSplitter configuration
        """
        super().__init__(splitter_config)

        # Validate that this is a DOCUMENT splitter
        if splitter_config.splitter_type.value != "document":
            raise ValueError(
                f"HTMLSplitter requires DOCUMENT splitter_type, got {splitter_config.splitter_type}"
            )

        # Get section configuration for HTML
        self.sections_to_split_on = splitter_config.get_effective_sections_to_split_on()

        # Create the underlying splitter once during initialization
        self._splitter = HTMLSectionSplitter(
            sections_to_split_on=self.sections_to_split_on,
            strip_headers=False,  # Keep headers in chunks for context
            return_each_line=False,  # Aggregate lines by sections
        )

        logger.debug(
            f"HTMLSplitter configured with sections: {self.sections_to_split_on}"
        )

    def split(self, text: str) -> List[Document]:
        """Split text into chunks using HTML header structure.

        Args:
            text: The HTML text content to split

        Returns:
            List[Document]: List of Document chunks
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to split")
            return []

        logger.debug(f"Splitting HTML text of length {len(text)} with HTMLSplitter")

        # Use the pre-created splitter
        chunk_docs = self._splitter.split_text(text)

        logger.debug(f"HTMLSplitter created {len(chunk_docs)} chunks")

        # Log chunk statistics
        for i, chunk in enumerate(chunk_docs):
            chunk_length = len(chunk.page_content)
            headers = {
                k: v for k, v in chunk.metadata.items() if k.startswith("Header")
            }
            logger.debug(f"HTML CHUNK {i+1}: {chunk_length} chars | Headers: {headers}")

        return chunk_docs
