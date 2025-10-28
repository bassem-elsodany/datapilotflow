"""
Markdown Splitter Implementation.

This module provides a markdown-based document splitter that uses
document structure (headers) for splitting while preserving semantic coherence.

Implements a HYBRID splitting strategy:
1. Primary split by markdown headers (preserves semantic structure)
2. Secondary split by token count (enforces embedding model limits)
"""

from typing import List, Optional

from langchain.schema import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from loguru import logger

from src.domain.knowledge.document_splitter import DocumentSplitter

from .base import BaseSplitter
from .token_counter import TokenCounter


class MarkdownSplitter(BaseSplitter):
    """Markdown splitter for structured content using HYBRID splitting strategy.

    This splitter implements a two-stage approach:
    1. Primary split: Uses markdown headers to preserve semantic structure
    2. Secondary split: Enforces token limits for embedding models

    This ensures chunks never exceed the embedding model's max_input_tokens
    while preserving document structure as much as possible.
    """

    def __init__(
        self,
        splitter_config: DocumentSplitter,
        max_tokens: Optional[int] = None,
        model_name: Optional[str] = None
    ):
        """Initialize the markdown splitter with hybrid splitting.

        This implements the LangChain recommended pattern:
        1. Primary split by markdown headers (preserves document structure)
        2. Secondary split using RecursiveCharacterTextSplitter (enforces token limits)

        Args:
            splitter_config: DocumentSplitter configuration (contains chunk_size/overlap for secondary split)
            max_tokens: Maximum tokens per chunk from embedding model (if None, no secondary splitting)
            model_name: Embedding model name for token counting
        """
        super().__init__(splitter_config)

        # Validate that this is a DOCUMENT splitter
        if splitter_config.splitter_type.value != "document":
            raise ValueError(
                f"MarkdownSplitter requires DOCUMENT splitter_type, got {splitter_config.splitter_type}"
            )

        # Get header configuration
        self.headers_to_split_on = splitter_config.get_effective_headers_to_split_on()

        # Token limit configuration from embedding model
        self.max_tokens = max_tokens
        self.model_name = model_name

        # Initialize token counter if we have token limits
        self._token_counter = TokenCounter(model_name=model_name) if max_tokens else None

        # Create the primary markdown splitter
        # Following LangChain best practices: strip_headers=False keeps context
        self._markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False,  # Keep headers in chunks for context
            return_each_line=False,  # Aggregate lines by headers
        )

        # Create secondary text splitter for oversized chunks (only if max_tokens specified)
        self._text_splitter = None
        if self.max_tokens:
            # Use the job's splitter config chunk_size and chunk_overlap for secondary splitting
            # If not specified in config, calculate from max_tokens
            if splitter_config.chunk_size:
                chunk_size = min(splitter_config.chunk_size, self.max_tokens)
                chunk_overlap = splitter_config.get_effective_chunk_overlap()
            else:
                # Calculate safe chunk size (90% of max_tokens for safety margin)
                chunk_size = int(self.max_tokens * 0.9)
                chunk_overlap = min(50, chunk_size // 10)  # 10% overlap, max 50 tokens

            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=self._token_counter.count_tokens,
                separators=["\n\n", "\n", " ", ""],  # Natural boundaries
            )

            logger.info(
                f"MarkdownSplitter initialized with HYBRID strategy: "
                f"headers={len(self.headers_to_split_on)}, "
                f"max_tokens={self.max_tokens}, "
                f"secondary_chunk_size={chunk_size}, "
                f"secondary_overlap={chunk_overlap}"
            )
        else:
            logger.info(
                f"MarkdownSplitter initialized with HEADER-ONLY strategy: "
                f"headers={len(self.headers_to_split_on)} "
                f"(no token limits)"
            )

    def split(self, text: str) -> List[Document]:
        """Split text using HYBRID strategy: markdown headers + token enforcement.

        Following LangChain best practices:
        1. Split by markdown headers (preserves semantic structure and adds header metadata)
        2. ONLY if max_tokens is configured: Check each chunk's token count
        3. If chunk exceeds max_tokens: Apply RecursiveCharacterTextSplitter using job's chunk_size/overlap

        Args:
            text: The markdown text content to split

        Returns:
            List[Document]: List of Document chunks with header metadata, all within token limits
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to split")
            return []

        # STAGE 1: Split by markdown headers
        # This preserves document structure and adds header hierarchy to metadata
        markdown_chunks = self._markdown_splitter.split_text(text)

        logger.debug(
            f"Stage 1 (Markdown headers): Created {len(markdown_chunks)} chunks"
        )

        # If no token limits configured, return markdown chunks as-is
        if not self.max_tokens or not self._text_splitter:
            logger.info(
                f"No token limits configured - returning {len(markdown_chunks)} header-based chunks"
            )
            return markdown_chunks

        # STAGE 2: Enforce token limits with secondary splitting (only for oversized chunks)
        final_chunks = []
        oversized_count = 0

        for idx, chunk in enumerate(markdown_chunks):
            chunk_text = chunk.page_content
            token_count = self._token_counter.count_tokens(chunk_text)

            # If chunk is within limits, keep it as-is
            if token_count <= self.max_tokens:
                final_chunks.append(chunk)
            else:
                # Chunk exceeds limit - apply secondary splitting
                oversized_count += 1
                logger.debug(
                    f"Chunk {idx} has {token_count} tokens (max: {self.max_tokens}), "
                    f"applying secondary split with RecursiveCharacterTextSplitter"
                )

                # Split using RecursiveCharacterTextSplitter with token counting
                # This uses the job's configured chunk_size and chunk_overlap
                sub_chunks = self._text_splitter.split_text(chunk_text)

                # Convert back to Document objects, preserving original header metadata
                for sub_idx, sub_text in enumerate(sub_chunks):
                    # Copy metadata from original chunk (includes header hierarchy)
                    # and add sub-chunk indicator
                    sub_metadata = chunk.metadata.copy() if chunk.metadata else {}
                    sub_metadata["sub_chunk"] = f"{idx}.{sub_idx}"
                    sub_metadata["original_token_count"] = token_count

                    final_chunks.append(
                        Document(
                            page_content=sub_text,
                            metadata=sub_metadata
                        )
                    )

                logger.debug(
                    f"Split oversized chunk {idx} ({token_count} tokens) into {len(sub_chunks)} sub-chunks"
                )

        logger.info(
            f"Stage 2 (Token enforcement): {len(markdown_chunks)} → {len(final_chunks)} chunks "
            f"({oversized_count} chunks required secondary splitting)"
        )

        return final_chunks
