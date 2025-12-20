"""
Splitters Package.

This package contains text splitting utilities for document processing,
supporting multiple splitting strategies through a unified interface:
1. BaseSplitter - Abstract base class for all splitters
2. TextSplitter - Token-based splitting for unstructured content
3. MarkdownSplitter - Structure-based splitting for markdown content
4. Factory functions for creating splitters from configuration
"""

# New modular splitter system
from .base import BaseSplitter
from .factory import create_splitter, create_splitter_by_type
from .markdown_splitter import MarkdownSplitter

# Legacy imports for backward compatibility
from .splitters import (
    Splitter,
    get_markdown_splitter,
    get_text_splitter,
    split_markdown_by_structure,
)
from .text_splitter import TextSplitter

__all__ = [
    # Legacy functions (for backward compatibility)
    "get_text_splitter",
    "get_markdown_splitter",
    "split_markdown_by_structure",
    "Splitter",
    # New modular system
    "BaseSplitter",
    "TextSplitter",
    "MarkdownSplitter",
    "create_splitter",
    "create_splitter_by_type",
]
