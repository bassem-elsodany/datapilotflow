"""
Knowledge Source Configuration domain models.

This module defines the domain models for managing knowledge source configurations
in MongoDB, including user ownership and job linking capabilities.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ContentSourceType(str, Enum):
    """Content source type options."""

    WEB_SCRAPING = "web_scraping"  # Web scraping content
    LOCAL_FILES = "local_files"  # Local uploaded files
    CONFLUENCE = "confluence"  # Confluence API integration


class ScrapingMode(str, Enum):
    """Scraping mode options."""

    # Web scraping modes
    SINGLE_PAGE = "single_page"  # Process one specific page
    MULTIPLE_PAGES = "multiple_pages"  # User uploads list of specific pages
    WEBSITE = "website"  # Crawl entire website

    # Local files modes
    HTML_FILES = "html_files"  # HTML files only
    MARKDOWN_FILES = "markdown_files"  # Markdown files only
    PDF_FILES = "pdf_files"  # PDF files only
    DOCX_FILES = "docx_files"  # DOCX files only
    TXT_FILES = "txt_files"  # TXT files only


class ConfluenceScrapingMode(str, Enum):
    """Confluence API extraction mode options."""

    SPECIFIC_PAGES = "specific_pages"  # Extract specific page IDs
    SPACE_PAGES = "space_pages"  # Extract all pages in specific spaces
    PAGES_WITH_LABEL = "pages_with_label"  # Extract pages matching labels
    RECENTLY_MODIFIED = "recently_modified"  # Extract recently modified pages


class OutputFormat(str, Enum):
    """Output format options."""

    HTML = "html"  # Raw HTML content
    MARKDOWN = "markdown"  # Structured markdown content
    LLM_MARKDOWN = "llm_markdown"  # LLM-powered markdown content


class ConfluenceConfig(BaseModel):
    """Configuration for Confluence API integration."""

    # Confluence instance details
    cloud_url: str = Field(
        description="Confluence cloud URL (e.g., https://company.atlassian.net/wiki)"
    )
    username_or_email: str = Field(
        description="Confluence username or email for Basic Auth"
    )
    api_token: str = Field(
        description="Confluence API token (encrypted in database)"
    )

    # Source specification
    confluence_mode: ConfluenceScrapingMode = Field(
        description="Confluence extraction mode"
    )
    space_keys: Optional[List[str]] = Field(
        default=None, description="Space keys to extract (for space_pages mode)"
    )
    page_ids: Optional[List[str]] = Field(
        default=None, description="Page IDs to extract (for specific_pages mode)"
    )
    labels: Optional[List[str]] = Field(
        default=None, description="Page labels to match (for pages_with_label mode)"
    )

    # Filtering
    include_attachments: bool = Field(
        default=False, description="Include page attachments as separate chunks"
    )
    include_comments: bool = Field(
        default=False, description="Include page comments and discussions"
    )
    max_pages_per_space: Optional[int] = Field(
        default=None, description="Limit pages per space (optional)"
    )

    # Processing
    expand_child_pages: bool = Field(
        default=True, description="Include child pages in hierarchy"
    )
    follow_page_links: bool = Field(
        default=False, description="Follow links to other pages within Confluence"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UrlSourceType(str, Enum):
    """URL source type for multiple_pages mode."""

    FILE_UPLOAD = "file_upload"  # Upload a .txt file with URLs


class UrlSourceConfig(BaseModel):
    """Configuration for URL source in multiple_pages mode - stored in separate collection.

    Note: One-way relationship only (config.url_source_id → url_source._id).
    No bidirectional link needed.
    """

    id: str = Field(description="Unique identifier for the URL source configuration")
    file_name: str = Field(description="Original file name")
    urls: List[str] = Field(
        default_factory=list,
        description="List of URLs to process",
        max_items=50000,  # Maximum 50,000 URLs
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the URL source was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the URL source was last updated",
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class KnowledgeSourceConfig(BaseModel):
    """A knowledge source configuration stored in MongoDB.

    This model represents a user-created knowledge source configuration
    that can be used to create processing jobs.
    """

    id: str = Field(
        description="Unique identifier for the knowledge source configuration"
    )
    user_id: str = Field(description="ID of the user who owns this configuration")
    name: str = Field(description="Name of the knowledge source")
    description: Optional[str] = Field(
        default="", description="Description of the knowledge source"
    )
    content_source_type: ContentSourceType = Field(
        default=ContentSourceType.WEB_SCRAPING, description="Type of content source"
    )
    url: Optional[str] = Field(
        default=None,
        description="Base URL of the knowledge source (required for web scraping)",
    )
    scraping_mode: Optional[ScrapingMode] = Field(
        default=None, description="Mode of scraping"
    )
    url_source_id: Optional[str] = Field(
        default=None,
        description="ID of the URL source configuration for multiple_pages mode",
    )
    allowed_subdomains: Optional[List[str]] = Field(
        default=None,
        description="List of allowed subdomains for crawling (web scraping only)",
    )
    blocked_subdomains: Optional[List[str]] = Field(
        default=None,
        description="List of blocked subdomains for crawling (web scraping only)",
    )
    url_patterns: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of URL patterns for crawling (web scraping only)",
    )
    crawl_depth: Optional[int] = Field(
        default=None,
        description="Maximum crawling depth: 0=exact URL only (no link following), 1=URL+1 level of links, 2+=deeper crawling. For single_page/multiple_pages use 0 for exact URLs only. For website mode use higher values for recursive discovery. (web scraping only)",
    )
    target_elements: List[str] = Field(
        default_factory=list,
        description="List of CSS selectors for content to include (preserves page context)",
    )
    exclude_elements: List[str] = Field(
        default_factory=list,
        description="List of CSS selectors for content to exclude (removes from extraction)",
    )
    content_filter_threshold: float = Field(
        default=0.6, description="Threshold for content filtering"
    )

    # Output Format Configuration
    output_format: OutputFormat = Field(
        default=OutputFormat.HTML, description="Output format for processed content"
    )

    # LLM Content Filter Configuration
    llm_content_filter_id: Optional[str] = Field(
        default=None,
        description="ID of the LLM content filter configuration to apply during crawling",
    )

    # Local Files Configuration
    local_files: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of uploaded local files with metadata (local files only)",
    )
    file_types: Optional[List[str]] = Field(
        default=None,
        description="Supported file types: ['html', 'markdown'] (local files only)",
    )

    # Confluence Configuration
    confluence_credential_id: Optional[str] = Field(
        default=None,
        description="ID of the Confluence credential (confluence only)",
    )
    confluence_config: Optional[ConfluenceConfig] = Field(
        default=None,
        description="Confluence API configuration (confluence only)",
    )

    # Metadata fields
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the configuration was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the configuration was last updated",
    )
    created_by: str = Field(description="User ID who created this configuration")
    updated_by: str = Field(description="User ID who last updated this configuration")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UrlSourceConfigCreate(BaseModel):
    """Model for creating a new URL source configuration."""

    file_name: str = Field(description="Original file name")
    urls: List[str] = Field(
        default_factory=list,
        description="List of URLs to process",
        max_items=50000,  # Maximum 50,000 URLs
    )


class KnowledgeSourceConfigCreate(BaseModel):
    """Model for creating a new knowledge source configuration."""

    name: str = Field(description="Name of the knowledge source")
    description: Optional[str] = Field(
        default=None, description="Description of the knowledge source"
    )
    content_source_type: ContentSourceType = Field(
        default=ContentSourceType.WEB_SCRAPING, description="Type of content source"
    )
    url: Optional[str] = Field(
        default=None,
        description="Base URL of the knowledge source (required for web scraping)",
    )
    scraping_mode: Optional[ScrapingMode] = Field(
        default=None, description="Mode of scraping"
    )
    url_source: Optional[UrlSourceConfigCreate] = Field(
        default=None,
        description="URL source configuration for multiple_pages mode (will be stored separately)",
    )
    url_source_id: Optional[str] = Field(
        default=None,
        description="ID of the URL source configuration for multiple_pages mode",
    )
    allowed_subdomains: Optional[List[str]] = Field(
        default=None,
        description="List of allowed subdomains for crawling (web scraping only)",
    )
    blocked_subdomains: Optional[List[str]] = Field(
        default=None,
        description="List of blocked subdomains for crawling (web scraping only)",
    )
    url_patterns: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of URL patterns for crawling (web scraping only)",
    )
    crawl_depth: Optional[int] = Field(
        default=None,
        description="Maximum crawling depth: 0=exact URL only (no link following), 1=URL+1 level of links, 2+=deeper crawling. For single_page/multiple_pages use 0 for exact URLs only. For website mode use higher values for recursive discovery. (web scraping only)",
    )
    target_elements: List[str] = Field(
        default_factory=list,
        description="List of target elements for content extraction (preserves page context)",
    )
    content_filter_threshold: float = Field(
        default=0.6, description="Threshold for content filtering"
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.HTML, description="Output format for processed content"
    )
    llm_content_filter_id: Optional[str] = Field(
        default=None,
        description="ID of the LLM content filter configuration to apply during crawling",
    )

    # Local Files Configuration
    local_files: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of uploaded local files with metadata (local files only)",
    )
    file_types: Optional[List[str]] = Field(
        default=None,
        description="Supported file types: ['html', 'markdown'] (local files only)",
    )

    # Confluence Configuration
    confluence_credential_id: Optional[str] = Field(
        default=None,
        description="ID of the Confluence credential (confluence only)",
    )
    confluence_config: Optional[ConfluenceConfig] = Field(
        default=None,
        description="Confluence API configuration (confluence only)",
    )


class KnowledgeSourceConfigUpdate(BaseModel):
    """Model for updating an existing knowledge source configuration.

    All fields are optional to allow partial updates.
    """

    name: Optional[str] = Field(
        default=None, description="Name of the knowledge source"
    )
    description: Optional[str] = Field(
        default=None, description="Description of the knowledge source"
    )
    content_source_type: Optional[ContentSourceType] = Field(
        default=None, description="Type of content source"
    )
    url: Optional[str] = Field(
        default=None,
        description="Base URL of the knowledge source (required for web scraping)",
    )
    scraping_mode: Optional[ScrapingMode] = Field(
        default=None, description="Mode of scraping"
    )
    url_source: Optional[UrlSourceConfigCreate] = Field(
        default=None,
        description="URL source configuration for multiple_pages mode (will be stored separately)",
    )
    allowed_subdomains: Optional[List[str]] = Field(
        default=None,
        description="List of allowed subdomains for crawling (web scraping only)",
    )
    blocked_subdomains: Optional[List[str]] = Field(
        default=None,
        description="List of blocked subdomains for crawling (web scraping only)",
    )
    url_patterns: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="URL pattern filters (web scraping only)",
    )
    crawl_depth: Optional[int] = Field(
        default=None,
        description="Maximum depth for recursive crawling (web scraping only)",
        ge=0,
        le=5,
    )
    target_elements: Optional[List[str]] = Field(
        default=None,
        description="CSS selectors to target specific elements on the page (web scraping only)",
    )
    content_filter_threshold: Optional[float] = Field(
        default=None,
        description="Content filter relevance threshold (0-1) (web scraping only)",
        ge=0,
        le=1,
    )
    output_format: Optional[OutputFormat] = Field(
        default=None, description="Format of the output"
    )
    llm_content_filter_id: Optional[str] = Field(
        default=None,
        description="ID of the LLM content filter configuration to use (web scraping only)",
    )
    local_files: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of uploaded local files with metadata (local files only)",
    )
    file_types: Optional[List[str]] = Field(
        default=None,
        description="Supported file types: ['html', 'markdown'] (local files only)",
    )

    # Confluence Configuration
    confluence_credential_id: Optional[str] = Field(
        default=None,
        description="ID of the Confluence credential (confluence only)",
    )
    confluence_config: Optional[ConfluenceConfig] = Field(
        default=None,
        description="Confluence API configuration (confluence only)",
    )


class KnowledgeSourceConfigExpanded(KnowledgeSourceConfig):
    """Expanded knowledge source configuration model with related data."""

    # Related data (optional, populated based on query parameters)
    content_filter: Optional[Dict[str, Any]] = Field(
        default=None, description="Full LLM content filter configuration data"
    )
    model_provider: Optional[Dict[str, Any]] = Field(
        default=None, description="Full model provider configuration data"
    )
    url_source: Optional[Dict[str, Any]] = Field(
        default=None, description="Full URL source configuration data"
    )
