"""
Base Splitter Module.

This module defines the abstract base class for all document splitters,
providing a unified interface for different splitting strategies.
"""

from abc import ABC, abstractmethod
from typing import List

from langchain.schema import Document
from loguru import logger

from src.domain.knowledge.document_splitter import DocumentSplitter


class BaseSplitter(ABC):
    """Abstract base class for all document splitters.

    This class defines the common interface that all splitter implementations
    must follow, ensuring consistency across different splitting strategies.
    """

    def __init__(self, splitter_config: DocumentSplitter):
        """Initialize the splitter with configuration.

        Args:
            splitter_config: The DocumentSplitter configuration containing
                all necessary parameters for the specific splitter type.
        """
        self.config = splitter_config
        logger.debug(
            f"Initialized {self.__class__.__name__} with config: {splitter_config.name}"
        )

    @abstractmethod
    def split(self, text: str) -> List[Document]:
        """Split text into smaller document chunks.

        Each splitter implementation handles the splitting logic according to its type:
        - TextSplitter: Uses token-based chunking with size and overlap
        - MarkdownSplitter: Uses header structure for semantic splitting

        Args:
            text: The text content to split

        Returns:
            List[Document]: List of Document chunks
        """
        pass

    def get_config(self) -> DocumentSplitter:
        """Get the splitter configuration.

        Returns:
            DocumentSplitter: The configuration object
        """
        return self.config
