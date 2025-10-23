from typing import Optional

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from loguru import logger

Splitter = RecursiveCharacterTextSplitter


def get_text_splitter(chunk_size: int, chunk_overlap: Optional[int] = None) -> Splitter:
    """Returns a token-based text splitter with overlap for unstructured content.

    Args:
        chunk_size: Number of tokens for each text chunk.
        chunk_overlap: Overlap between consecutive chunks. If None, uses 15% of chunk_size.

    Returns:
        Splitter: A configured text splitter instance that
            splits text into overlapping chunks based on token count.
    """

    if chunk_overlap is None:
        chunk_overlap = int(0.15 * chunk_size)

    logger.debug(
        f"Getting text splitter with chunk size: {chunk_size} and overlap: {chunk_overlap}"
    )

    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def get_markdown_splitter(
    headers_to_split_on: list[tuple[str, str]] = None,
) -> MarkdownHeaderTextSplitter:
    """Returns a markdown splitter based on document structure.

    This splitter respects markdown structure (headers, paragraphs, etc.) and is
    optimized for content generated from web crawling. It splits by headers only,
    ignoring arbitrary size limits to preserve semantic coherence.

    Args:
        headers_to_split_on: List of (header_pattern, header_name) tuples to split on.
                            If None, uses default header patterns.

    Returns:
        MarkdownHeaderTextSplitter: A configured markdown splitter instance that
            splits markdown content based on header structure.
    """
    if headers_to_split_on is None:
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]

    logger.debug(f"Getting markdown splitter with headers: {headers_to_split_on}")

    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,  # Keep headers in chunks for context
        return_each_line=False,  # Aggregate lines by headers (default behavior)
    )


def split_markdown_by_structure(
    markdown_content: str, headers_to_split_on: list[tuple[str, str]] = None
) -> list:
    """Split markdown content by document structure, ignoring arbitrary size limits.

    This function focuses on preserving document structure rather than enforcing
    chunk size limits. It splits by markdown headers to maintain semantic coherence.

    Args:
        markdown_content: The markdown content to split
        headers_to_split_on: List of (header_pattern, header_name) tuples to split on.
                            If None, uses default header patterns.

    Returns:
        list: List of Document objects with proper metadata
    """
    logger.debug("Splitting markdown by document structure (no size constraints)")

    # Create markdown splitter that only uses header structure
    markdown_splitter = get_markdown_splitter(headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(markdown_content)

    logger.debug(f"Markdown structure splitting created {len(md_header_splits)} chunks")

    # Log each chunk with its structure
    for i, chunk in enumerate(md_header_splits):
        headers = {k: v for k, v in chunk.metadata.items() if k.startswith("Header")}
        logger.debug(
            f"MARKDOWN CHUNK {i+1}: {len(chunk.page_content)} chars | Headers: {headers}"
        )

    return md_header_splits
