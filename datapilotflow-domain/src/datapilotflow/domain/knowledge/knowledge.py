"""
Knowledge domain models for SkillPilot.

This module defines the core domain models for knowledge sources, including
KnowledgeExtract for raw knowledge data and Knowledge for enriched knowledge
with memory capabilities.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Note: src.config removed - domain models should not depend on backend config
# from src.config import settings


class KnowledgeExtract(BaseModel):
    """A class representing raw knowledge data extracted from external sources.

    This class follows the structure of the knowledge.json file and contains
    basic information about knowledge sources before enrichment.

    Args:
        id (str): Unique identifier for the knowledge source.
        name (str): Name of the knowledge source.
        description (str): Description of the knowledge source.
        url (str): Base URL of the knowledge source.
        enabled (bool): Whether the knowledge source is enabled for crawling.
        scraping_mode (str): Mode of scraping - either 'single_page' or 'crawl'.
        allowed_subdomains (List[str]): List of allowed subdomains for crawling.
        blocked_subdomains (List[str]): List of blocked subdomains for crawling.
        url_patterns (List[Dict[str, Any]]): List of URL patterns for crawling.
        crawl_depth (int): Maximum depth for crawling.
        target_elements (List[str]): List of target elements for content extraction.
        content_filter_threshold (float): Threshold for content filtering.
    """

    id: str = Field(description="Unique identifier for the knowledge source")
    name: str = Field(description="Name of the knowledge source")
    description: str = Field(description="Description of the knowledge source")
    url: str = Field(description="Base URL of the knowledge source")
    enabled: bool = Field(
        default=True, description="Whether the knowledge source is enabled for crawling"
    )
    scraping_mode: str = Field(
        default="crawl",
        description="Mode of scraping - either 'single_page' or 'crawl'",
        pattern="^(single_page|crawl)$",
    )
    allowed_subdomains: List[str] = Field(
        default_factory=list, description="List of allowed subdomains for crawling"
    )
    blocked_subdomains: List[str] = Field(
        default_factory=list, description="List of blocked subdomains for crawling"
    )
    url_patterns: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of URL patterns for crawling"
    )
    crawl_depth: int = Field(default=4, description="Maximum depth for crawling")
    target_elements: List[str] = Field(
        default_factory=list,
        description="List of target elements for content extraction",
    )
    content_filter_threshold: float = Field(
        default=0.6, description="Threshold for content filtering"
    )

    @classmethod
    def from_json(cls, metadata_file: Path) -> list["KnowledgeExtract"]:
        """Load knowledge sources from a JSON file.

        Args:
            metadata_file: Path to the JSON file containing knowledge source data.

        Returns:
            list[KnowledgeExtract]: List of knowledge source objects.
        """
        with open(metadata_file, "r") as f:
            knowledge_data = json.load(f)

        return [cls(**knowledge) for knowledge in knowledge_data]


class Knowledge(BaseModel):
    """A class representing knowledge with memory capabilities.

    This class represents knowledge that can be processed and reasoned about,
    with specific perspectives and communication styles.

    Args:
        id (str): Unique identifier for the knowledge.
        name (str): Name of the knowledge source.
        description (str): Description of the knowledge source.
        url (str): Base URL of the knowledge source.
        enabled (bool): Whether the knowledge source is enabled for crawling.
        scraping_mode (str): Mode of scraping - either 'single_page' or 'crawl'.
        allowed_subdomains (List[str]): List of allowed subdomains for crawling.
        blocked_subdomains (List[str]): List of blocked subdomains for crawling.
        url_patterns (List[Dict[str, Any]]): List of URL patterns for crawling.
        crawl_depth (int): Maximum depth for crawling.
        target_elements (List[str]): List of target elements for content extraction.
        content_filter_threshold (float): Threshold for content filtering.
        metadata (Dict[str, Any]): Optional metadata for storing processing information.
    """

    id: str = Field(description="Unique identifier for the knowledge")
    knowledge_source: Optional[str] = Field(
        default=None, description="Knowledge source identifier for Weaviate mapping"
    )
    name: str = Field(description="Name of the knowledge source")
    description: str = Field(description="Description of the knowledge source")
    url: str = Field(description="Base URL of the knowledge source")
    enabled: bool = Field(
        default=True, description="Whether the knowledge source is enabled for crawling"
    )
    scraping_mode: str = Field(
        default="crawl",
        description="Mode of scraping - either 'single_page' or 'crawl'",
        pattern="^(single_page|crawl)$",
    )
    url_source: Optional[Dict[str, Any]] = Field(
        default=None, description="URL source configuration for single_page mode"
    )
    allowed_subdomains: List[str] = Field(
        default_factory=list, description="List of allowed subdomains for crawling"
    )
    blocked_subdomains: List[str] = Field(
        default_factory=list, description="List of blocked subdomains for crawling"
    )
    url_patterns: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of URL patterns for crawling"
    )
    crawl_depth: int = Field(default=4, description="Maximum depth for crawling")
    target_elements: List[str] = Field(
        default_factory=list,
        description="List of target elements for content extraction",
    )
    content_filter_threshold: float = Field(
        default=0.6, description="Threshold for content filtering"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata for storing processing information",
    )

    def __str__(self) -> str:
        return (
            f"Knowledge(id={self.id}, name={self.name}, "
            f"description={self.description}, url={self.url}, "
            f"enabled={self.enabled}, scraping_mode={self.scraping_mode}, "
            f"crawl_depth={self.crawl_depth})"
        )

    @classmethod
    def load_all(cls) -> list["Knowledge"]:
        """Load all knowledge sources from the configuration file."""
        with open(settings.KNOWLEDGE_METADATA_FILE_PATH) as f:
            knowledge_data = json.load(f)

        return [cls(**knowledge) for knowledge in knowledge_data]
