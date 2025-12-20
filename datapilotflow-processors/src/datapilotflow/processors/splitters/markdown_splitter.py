"""
Markdown Splitter Implementation.

This module provides a markdown-based document splitter that uses
document structure (headers) for splitting while preserving semantic coherence.

Implements a HYBRID splitting strategy:
1. Primary split by markdown headers (preserves semantic structure)
2. Secondary split by token count (enforces embedding model limits)
"""

from typing import List, Optional

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from loguru import logger

from datapilotflow.domain.knowledge.document_splitter import DocumentSplitter

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
        model_name: Optional[str] = None,
        min_chunk_size: int = 250,  # Minimum tokens to prevent noisy chunks
    ):
        """Initialize the markdown splitter with hybrid splitting.

        This implements the LangChain recommended pattern:
        1. Primary split by markdown headers (preserves document structure)
        2. Merge small chunks into parent (prevents noisy low-information chunks)
        3. Secondary split using RecursiveCharacterTextSplitter (enforces token limits)

        Args:
            splitter_config: DocumentSplitter configuration (contains chunk_size/overlap for secondary split)
            max_tokens: Maximum tokens per chunk from embedding model (if None, no secondary splitting)
            model_name: Embedding model name for token counting
            min_chunk_size: Minimum tokens per chunk (default: 200)
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
        self.min_chunk_size = min_chunk_size

        # Initialize token counter if we have token limits
        self._token_counter = (
            TokenCounter(model_name=model_name) if max_tokens else None
        )

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
            # IMPORTANT: Use 80% of max_tokens as safety margin to match embedding service expectations
            # Embedding service uses 80% safety margin, so chunks must respect this limit
            # to avoid "chunk exceeds safe limit" warnings
            safe_max_tokens = int(self.max_tokens * 0.8)

            # Use the job's splitter config chunk_size and chunk_overlap for secondary splitting
            # If not specified in config, calculate from max_tokens
            if splitter_config.chunk_size:
                # Ensure user's chunk_size doesn't exceed safe limit (accounting for overlap)
                chunk_size = min(splitter_config.chunk_size, safe_max_tokens)
                chunk_overlap = splitter_config.get_effective_chunk_overlap()
            else:
                # Calculate safe chunk size (80% of max_tokens for safety margin)
                chunk_size = safe_max_tokens
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
                f"min_chunk_size={self.min_chunk_size}, "
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

    def split(self, text: str, source_url: str = "unknown") -> List[Document]:
        """Split text using HYBRID strategy: markdown headers + parent merging + token enforcement.

        Three-stage splitting process:
        1. STAGE 1: Split by markdown headers (preserves semantic structure and adds header metadata)
        2. STAGE 1.5: Merge small chunks into parent (prevents noisy low-information chunks)
           - If chunk < min_chunk_size AND parent + child <= max_tokens: Merge
           - Otherwise: Keep chunk as-is
        3. STAGE 2: Enforce token limits (only for oversized chunks after merging)
           - If chunk > max_tokens: Apply RecursiveCharacterTextSplitter using job's chunk_size/overlap

        Args:
            text: The markdown text content to split
            source_url: Source URL or identifier for logging purposes

        Returns:
            List[Document]: List of Document chunks with header metadata, all within token limits
        """
        if not text or not text.strip():
            logger.warning(f"Empty text provided to split for {source_url}")
            return []

        # STAGE 1: Split by markdown headers
        # This preserves document structure and adds header hierarchy to metadata
        markdown_chunks = self._markdown_splitter.split_text(text)

        logger.debug(
            f"Stage 1 (Markdown headers): Created {len(markdown_chunks)} chunks for {source_url}"
        )

        # If no token limits configured, return markdown chunks as-is
        if not self.max_tokens or not self._text_splitter:
            logger.info(
                f"No token limits configured - returning {len(markdown_chunks)} header-based chunks for {source_url}"
            )
            return markdown_chunks

        # STAGE 1.5: Merge small chunks into parent to prevent noisy low-information chunks
        merged_chunks = self._merge_small_into_parent(markdown_chunks, source_url)

        # STAGE 2: Enforce token limits with secondary splitting (only for oversized chunks)
        final_chunks = []
        oversized_count = 0

        for idx, chunk in enumerate(merged_chunks):
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
                        Document(page_content=sub_text, metadata=sub_metadata)
                    )

                logger.debug(
                    f"Split oversized chunk {idx} ({token_count} tokens) into {len(sub_chunks)} sub-chunks"
                )

        logger.info(
            f"Stage 2 (Token enforcement): {len(merged_chunks)} → {len(final_chunks)} chunks "
            f"({oversized_count} chunks required secondary splitting) for {source_url}"
        )

        return final_chunks

    def _merge_small_into_parent(
        self, chunks: List[Document], source_url: str = "unknown"
    ) -> List[Document]:
        """
        Merge small chunks into their direct parent (previous chunk) to prevent noisy low-information chunks.

        Algorithm:
        1. For each chunk < min_chunk_size:
           - Try to merge it into the previous chunk (direct parent)
           - If previous chunk + current chunk <= max_tokens: Merge
           - Otherwise: Keep as separate chunk

        Args:
            chunks: List of header-based chunks
            source_url: Source URL or identifier for logging purposes

        Returns:
            List[Document]: Chunks with small chunks merged into their previous chunk
        """
        if not chunks or not self.max_tokens:
            return chunks

        logger.debug(
            f"Stage 1.5 (Merge small chunks): Processing {len(chunks)} chunks "
            f"with min_chunk_size={self.min_chunk_size} for {source_url}"
        )

        # Track chunks and their token counts
        chunk_data = []
        for idx, chunk in enumerate(chunks):
            token_count = self._token_counter.count_tokens(chunk.page_content)
            chunk_data.append(
                {
                    "index": idx,
                    "chunk": chunk,
                    "token_count": token_count,
                    "merged": False,  # Track if this chunk was merged into previous
                }
            )

        # Process chunks from left to right, merging small chunks into previous chunk
        merged_count = 0
        final_chunks = []

        for i, current_data in enumerate(chunk_data):
            # Skip if this chunk was already merged into previous
            if current_data["merged"]:
                continue

            # If chunk is too small and there's a previous chunk, try to merge
            if current_data["token_count"] < self.min_chunk_size and i > 0:
                # Find the last non-merged chunk (direct parent)
                prev_data = None
                for j in range(i - 1, -1, -1):
                    if not chunk_data[j]["merged"]:
                        prev_data = chunk_data[j]
                        break

                if prev_data:
                    # Check if merging would exceed max_tokens
                    total_tokens = (
                        prev_data["token_count"] + current_data["token_count"]
                    )

                    if total_tokens <= self.max_tokens:
                        # Merge current chunk into previous chunk
                        prev_data["chunk"].page_content += (
                            "\n\n" + current_data["chunk"].page_content
                        )
                        prev_data["token_count"] = total_tokens
                        current_data["merged"] = True
                        merged_count += 1

                        logger.debug(
                            f"Merged chunk {i} ({current_data['token_count']} tokens) "
                            f"into previous chunk {prev_data['index']} "
                            f"(new total: {total_tokens} tokens)"
                        )
                        continue
                    else:
                        logger.debug(
                            f"Cannot merge chunk {i} ({current_data['token_count']} tokens) "
                            f"into previous chunk {prev_data['index']} ({prev_data['token_count']} tokens) "
                            f"- would exceed max_tokens ({total_tokens} > {self.max_tokens})"
                        )

            # Keep chunk as-is (either not small, or couldn't merge)
            final_chunks.append(current_data["chunk"])

        logger.info(
            f"Stage 1.5 (Merge small chunks): {len(chunks)} → {len(final_chunks)} chunks "
            f"({merged_count} small chunks merged into previous chunk) for {source_url}"
        )

        return final_chunks
