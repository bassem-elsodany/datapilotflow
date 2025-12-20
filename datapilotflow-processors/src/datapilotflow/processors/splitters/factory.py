"""
Splitter Factory Module.

This module provides a factory for creating splitter instances based on
DocumentSplitter configuration, ensuring the correct splitter type is used.
"""

from typing import Optional, Union

from loguru import logger

from datapilotflow.domain.knowledge.document_splitter import DocumentSplitter, SplitterType

from .base import BaseSplitter
from .html_splitter import HTMLSplitter
from .markdown_splitter import MarkdownSplitter
from .text_splitter import TextSplitter


def create_splitter(
    splitter_config: DocumentSplitter,
    max_tokens: Optional[int] = None,
    model_name: Optional[str] = None
) -> BaseSplitter:
    """Create a splitter instance based on DocumentSplitter configuration.

    This factory function creates the appropriate splitter implementation
    based on the splitter_type specified in the configuration.

    Args:
        splitter_config: DocumentSplitter configuration containing
            all necessary parameters for the specific splitter type
        max_tokens: Maximum tokens per chunk (for DOCUMENT splitters with hybrid splitting)
        model_name: Embedding model name for token counting (for DOCUMENT splitters)

    Returns:
        BaseSplitter: The appropriate splitter instance

    Raises:
        ValueError: If the splitter_type is not supported
    """
    logger.debug(f"Creating splitter for type: {splitter_config.splitter_type}")

    if splitter_config.splitter_type == SplitterType.TEXT:
        logger.debug("Creating TextSplitter instance")
        return TextSplitter(splitter_config)

    elif splitter_config.splitter_type == SplitterType.DOCUMENT:
        logger.debug(f"Creating MarkdownSplitter instance (max_tokens={max_tokens}, model={model_name})")
        return MarkdownSplitter(
            splitter_config,
            max_tokens=max_tokens,
            model_name=model_name
        )

    elif splitter_config.splitter_type == SplitterType.HTML:
        logger.debug("Creating HTMLSplitter instance")
        return HTMLSplitter(splitter_config)

    else:
        raise ValueError(f"Unsupported splitter_type: {splitter_config.splitter_type}")


def create_splitter_by_type(
    splitter_type: SplitterType,
    chunk_size: int = 256,
    chunk_overlap: int = 32,
    headers_to_split_on: list = None,
    name: str = "Default Splitter",
    description: str = None,
) -> BaseSplitter:
    """Create a splitter instance by type with direct parameters.

    This is a convenience function for creating splitters without
    a full DocumentSplitter configuration object.

    Args:
        splitter_type: The type of splitter to create
        chunk_size: Size of text chunks (for TEXT splitter)
        chunk_overlap: Overlap between chunks (for TEXT splitter)
        headers_to_split_on: Header patterns (for DOCUMENT splitter)
        name: Name for the splitter configuration
        description: Description for the splitter configuration

    Returns:
        BaseSplitter: The appropriate splitter instance

    Raises:
        ValueError: If the splitter_type is not supported
    """
    logger.debug(f"Creating splitter by type: {splitter_type}")

    # Create a minimal DocumentSplitter configuration
    splitter_config = DocumentSplitter(
        id="temp",  # Temporary ID for factory creation
        user_id="system",  # System user for factory creation
        name=name,
        description=description,
        splitter_type=splitter_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        headers_to_split_on=headers_to_split_on,
        created_by="system",
        updated_by="system",
    )

    return create_splitter(splitter_config)
