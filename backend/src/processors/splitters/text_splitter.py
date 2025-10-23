"""
Text Splitter Implementation.

This module provides a text-based document splitter that uses token-based
chunking with configurable size and overlap for unstructured content.
"""

from typing import List

from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from src.domain.knowledge.document_splitter import DocumentSplitter

from .base import BaseSplitter


class TextSplitter(BaseSplitter):
    """Text splitter for unstructured content using token-based chunking.

    This splitter uses RecursiveCharacterTextSplitter with tiktoken encoding
    to split documents into chunks based on token count with configurable overlap.
    """

    def __init__(self, splitter_config: DocumentSplitter):
        """Initialize the text splitter.

        Args:
            splitter_config: DocumentSplitter configuration
        """
        super().__init__(splitter_config)

        # Validate that this is a TEXT splitter
        if splitter_config.splitter_type.value != "text":
            raise ValueError(
                f"TextSplitter requires TEXT splitter_type, got {splitter_config.splitter_type}"
            )

        # Get configuration values
        self.chunk_size = splitter_config.chunk_size or 256
        self.chunk_overlap = splitter_config.get_effective_chunk_overlap() or 32

        # Create the underlying splitter once during initialization
        self._splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        logger.debug(
            f"TextSplitter configured: chunk_size={self.chunk_size}, "
            f"chunk_overlap={self.chunk_overlap}"
        )

    def split(self, text: str) -> List[Document]:
        """Split text into document chunks using token-based splitting.

        Args:
            text: The text content to split

        Returns:
            List[Document]: List of Document chunks
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to split")
            return []

        logger.debug(f"Splitting text of length {len(text)} with TextSplitter")

        # Use the pre-created splitter
        text_chunks = self._splitter.split_text(text)

        # Convert text chunks to Document objects
        document_chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk_doc = Document(
                page_content=chunk_text,
                metadata={"chunk_index": i, "splitter_type": "text"},
            )
            document_chunks.append(chunk_doc)

        logger.debug(f"TextSplitter created {len(document_chunks)} chunks")

        # Log chunk statistics
        for i, chunk in enumerate(document_chunks):
            chunk_length = len(chunk.page_content)
            try:
                import tiktoken

                encoding = tiktoken.get_encoding("cl100k_base")
                chunk_tokens = len(encoding.encode(chunk.page_content))
                percentage = (
                    (chunk_tokens / self.chunk_size) * 100 if self.chunk_size > 0 else 0
                )
                logger.debug(
                    f"TEXT CHUNK {i+1}: {chunk_length} chars ({chunk_tokens} tokens, "
                    f"{percentage:.1f}% of target {self.chunk_size} tokens)"
                )
            except Exception as e:
                logger.warning(f"Could not calculate tokens for chunk {i+1}: {e}")

        return document_chunks
