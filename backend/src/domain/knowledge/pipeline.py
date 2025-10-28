"""
Pipeline domain models.

This module defines the domain models for managing visual data processing pipelines,
including node configurations, edges, and execution state.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Types of nodes available in the pipeline."""

    # Data Sources
    WEBSITE = "website"
    MULTIPLE_PAGES = "multiple_pages"
    SINGLE_PAGE = "single_page"

    # Filters & Transforms
    DOMAIN_FILTER = "domainFilter"
    CONTENT_FILTER = "contentFilter"

    # Output Formats
    HTML_EXTRACTOR = "htmlExtractor"
    MARKDOWN_GENERATOR = "markdownGenerator"
    LLM_MARKDOWN_GENERATOR = "llmMarkdownGenerator"

    # Processing
    TEXT_SPLITTER = "textSplitter"

    # AI Tools
    EMBEDDING_GENERATOR = "embeddingGenerator"

    # Storage/Output
    VECTOR_DATABASE = "vectorDatabase"
    FILE_EXPORT = "fileExport"


class NodeStatus(str, Enum):
    """Status of a node in the pipeline."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStatus(str, Enum):
    """Overall status of the pipeline."""

    DRAFT = "draft"  # Pipeline is being built, not executed
    READY = "ready"  # Pipeline is configured and ready to execute
    RUNNING = "running"  # Pipeline is currently executing
    COMPLETED = "completed"  # Pipeline execution completed successfully
    FAILED = "failed"  # Pipeline execution failed
    CANCELLED = "cancelled"  # Pipeline execution was cancelled


# Node Configuration Models (matching frontend)


class WebsiteNodeConfig(BaseModel):
    """Configuration for website data source node - SIMPLIFIED.

    This node ONLY stores URL and crawl depth.
    Other options (filtering, output) are configured via separate filter nodes.
    """

    url: str = Field(description="Base URL of the website to crawl")
    crawl_depth: int = Field(
        default=4, ge=0, le=10, description="Maximum crawling depth"
    )


class MultiplePagesNodeConfig(BaseModel):
    """Configuration for multiple pages data source node - SIMPLIFIED.

    This node ONLY stores the list of URLs to process.
    Filtering and output options are configured via separate filter nodes.
    """

    base_url: str = Field(description="Base URL for the pages")
    urls: List[str] = Field(
        default_factory=list,
        description="List of specific URLs to process",
        max_items=50000,
    )
    file_name: Optional[str] = Field(
        default=None, description="Name of uploaded file with URLs"
    )


class SinglePageNodeConfig(BaseModel):
    """Configuration for single page data source node - SIMPLIFIED.

    This node ONLY stores the URL to process.
    Filtering and output options are configured via separate filter nodes.
    """

    url: str = Field(description="URL of the single page to process")


class DomainFilterNodeConfig(BaseModel):
    """Configuration for domain filter node."""

    allowed_subdomains: List[str] = Field(
        default_factory=list, description="List of allowed subdomains"
    )
    blocked_subdomains: List[str] = Field(
        default_factory=list, description="List of blocked subdomains"
    )


class ContentFilterNodeConfig(BaseModel):
    """Configuration for content filter node."""

    target_elements: List[str] = Field(
        default_factory=list, description="CSS selectors for content to include"
    )
    exclude_elements: List[str] = Field(
        default_factory=list, description="CSS selectors for content to exclude"
    )


class HtmlExtractorNodeConfig(BaseModel):
    """Configuration for HTML extractor node."""

    content_filter_threshold: float = Field(
        default=0.6, ge=0.0, le=1.0, description="Content filter threshold"
    )


class MarkdownGeneratorNodeConfig(BaseModel):
    """Configuration for markdown generator node."""

    content_filter_threshold: float = Field(
        default=0.6, ge=0.0, le=1.0, description="Content filter threshold"
    )


class LlmMarkdownGeneratorNodeConfig(BaseModel):
    """Configuration for LLM markdown generator node."""

    llm_content_filter_id: Optional[str] = Field(
        default=None, description="LLM content filter configuration ID"
    )


class TextSplitterNodeConfig(BaseModel):
    """Configuration for text splitter node."""

    splitter_id: Optional[str] = Field(
        default=None, description="Reference to existing splitter configuration"
    )
    splitter_type: str = Field(
        default="TEXT", description="Splitter type (TEXT or DOCUMENT)"
    )
    chunk_size: int = Field(
        default=512,
        ge=64,
        description="Size of text chunks (validated against embedding model's max tokens)",
    )
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        description="Overlap between chunks (validated against chunk_size and embedding model limits)",
    )
    separators: List[str] = Field(
        default_factory=lambda: ["\n\n", "\n", " ", ""], description="Text separators"
    )


class EmbeddingGeneratorNodeConfig(BaseModel):
    """Configuration for embedding generator node."""

    model_provider_id: str = Field(description="ID of the model provider")
    model_name: str = Field(description="Name of the embedding model")
    vector_dimension: int = Field(
        ge=1, le=4096, description="Dimension of embedding vectors"
    )
    batch_size: int = Field(
        default=100, ge=1, le=1000, description="Batch size for processing"
    )


class TextSummarizerNodeConfig(BaseModel):
    """Configuration for text summarizer node."""

    model_provider_id: str = Field(description="ID of the LLM provider")
    model_name: str = Field(description="Name of the LLM model")
    summary_type: str = Field(
        default="extractive", description="Type of summary (extractive, abstractive)"
    )
    max_length: int = Field(
        default=500, ge=50, le=2000, description="Maximum summary length"
    )
    temperature: float = Field(
        default=0.3, ge=0.0, le=2.0, description="Model temperature"
    )


class ContentClassifierNodeConfig(BaseModel):
    """Configuration for content classifier node."""

    model_provider_id: str = Field(description="ID of the LLM provider")
    model_name: str = Field(description="Name of the LLM model")
    categories: List[str] = Field(
        default_factory=list, description="Classification categories"
    )
    confidence_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )


class ContentEnricherNodeConfig(BaseModel):
    """Configuration for content enricher node."""

    model_provider_id: str = Field(description="ID of the LLM provider")
    model_name: str = Field(description="Name of the LLM model")
    enrichment_fields: List[str] = Field(
        default_factory=list,
        description="Fields to enrich (keywords, entities, topics)",
    )
    temperature: float = Field(
        default=0.3, ge=0.0, le=2.0, description="Model temperature"
    )


class TranslationNodeConfig(BaseModel):
    """Configuration for translation node."""

    model_provider_id: str = Field(description="ID of the LLM provider")
    model_name: str = Field(description="Name of the LLM model")
    target_language: str = Field(description="Target language code")
    preserve_formatting: bool = Field(
        default=True, description="Preserve original formatting"
    )


class VectorDatabaseNodeConfig(BaseModel):
    """Configuration for vector database storage node."""

    collection_id: Optional[str] = Field(
        default=None, description="ID of existing collection"
    )
    collection_name: Optional[str] = Field(
        default=None, description="Name for new collection"
    )
    collection_description: Optional[str] = Field(
        default=None, description="Collection description"
    )
    clear_collection_before_start: bool = Field(
        default=False, description="Clear collection before storing"
    )
    check_duplicates_before_insert: bool = Field(
        default=False, description="Check for duplicates"
    )


class FileExportNodeConfig(BaseModel):
    """Configuration for file export node."""

    output_path: str = Field(description="Path to save exported files")
    file_format: str = Field(
        default="json", description="Export format (json, csv, txt, markdown)"
    )
    consolidated_file: bool = Field(
        default=False, description="Save as single consolidated file"
    )
    include_metadata: bool = Field(
        default=True, description="Include metadata in export"
    )


class ReportGeneratorNodeConfig(BaseModel):
    """Configuration for report generator node."""

    report_type: str = Field(
        default="summary", description="Type of report (summary, detailed, custom)"
    )
    output_format: str = Field(
        default="pdf", description="Report format (pdf, html, markdown)"
    )
    include_charts: bool = Field(default=True, description="Include visualizations")
    sections: List[str] = Field(
        default_factory=list, description="Report sections to include"
    )


class AnalyticsNodeConfig(BaseModel):
    """Configuration for analytics node."""

    metrics: List[str] = Field(default_factory=list, description="Metrics to calculate")
    aggregation_level: str = Field(
        default="document", description="Aggregation level (document, batch, pipeline)"
    )
    save_results: bool = Field(default=True, description="Save analytics results")


class NotificationNodeConfig(BaseModel):
    """Configuration for notification node."""

    notification_type: str = Field(
        default="email", description="Notification type (email, webhook, slack)"
    )
    recipients: List[str] = Field(
        default_factory=list, description="Notification recipients"
    )
    trigger_on: str = Field(
        default="completion", description="When to trigger (completion, failure, both)"
    )
    include_summary: bool = Field(default=True, description="Include execution summary")


class PipelineNode(BaseModel):
    """A node in the pipeline graph."""

    id: str = Field(description="Unique identifier for the node")
    type: NodeType = Field(description="Type of the node")
    name: str = Field(description="Display name of the node")
    position: Dict[str, float] = Field(description="Position on the canvas (x, y)")
    status: NodeStatus = Field(
        default=NodeStatus.PENDING, description="Execution status of the node"
    )
    configured: bool = Field(
        default=False, description="Whether the node has been configured"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Node-specific configuration"
    )

    # Execution metadata
    started_at: Optional[datetime] = Field(
        default=None, description="When node execution started"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="When node execution completed"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PipelineEdge(BaseModel):
    """An edge (connection) between nodes in the pipeline."""

    id: str = Field(description="Unique identifier for the edge")
    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    type: str = Field(default="arrow", description="Visual type of the edge")


class Pipeline(BaseModel):
    """A complete data processing pipeline.

    This model represents a user-created visual pipeline with nodes and edges
    that defines a complete data processing workflow.
    """

    id: str = Field(description="Unique identifier for the pipeline")
    user_id: str = Field(description="ID of the user who owns this pipeline")
    name: str = Field(description="Name of the pipeline")
    description: Optional[str] = Field(
        default=None, description="Description of the pipeline"
    )

    # Pipeline graph structure
    nodes: List[PipelineNode] = Field(
        default_factory=list, description="Nodes in the pipeline"
    )
    edges: List[PipelineEdge] = Field(
        default_factory=list, description="Edges connecting nodes"
    )

    # Pipeline state
    status: PipelineStatus = Field(
        default=PipelineStatus.DRAFT, description="Overall pipeline status"
    )

    # Execution tracking
    last_executed_at: Optional[datetime] = Field(
        default=None, description="Last execution timestamp"
    )
    execution_count: int = Field(
        default=0, description="Number of times this pipeline has been executed"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the pipeline was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the pipeline was last updated",
    )
    created_by: str = Field(description="User ID who created this pipeline")
    updated_by: str = Field(description="User ID who last updated this pipeline")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PipelineCreate(BaseModel):
    """Model for creating a new pipeline."""

    name: str = Field(description="Name of the pipeline")
    description: Optional[str] = Field(
        default=None, description="Description of the pipeline"
    )
    nodes: List[PipelineNode] = Field(
        default_factory=list, description="Nodes in the pipeline"
    )
    edges: List[PipelineEdge] = Field(
        default_factory=list, description="Edges connecting nodes"
    )


class PipelineUpdate(BaseModel):
    """Model for updating an existing pipeline."""

    name: Optional[str] = Field(default=None, description="Name of the pipeline")
    description: Optional[str] = Field(
        default=None, description="Description of the pipeline"
    )
    nodes: Optional[List[PipelineNode]] = Field(
        default=None, description="Nodes in the pipeline"
    )
    edges: Optional[List[PipelineEdge]] = Field(
        default=None, description="Edges connecting nodes"
    )
    status: Optional[PipelineStatus] = Field(
        default=None, description="Pipeline status"
    )


class PipelineExecutionRequest(BaseModel):
    """Request model for executing a pipeline."""

    pipeline_id: str = Field(description="ID of the pipeline to execute")
    async_execution: bool = Field(
        default=True, description="Execute asynchronously via RabbitMQ"
    )


class PipelineExecutionStatus(BaseModel):
    """Status information for a pipeline execution."""

    pipeline_id: str = Field(description="ID of the pipeline")
    status: PipelineStatus = Field(description="Current pipeline status")
    current_node: Optional[str] = Field(
        default=None, description="Currently executing node ID"
    )
    progress: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Execution progress percentage"
    )
    nodes_status: List[PipelineNode] = Field(
        default_factory=list, description="Status of all nodes"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Execution start time"
    )
    estimated_completion: Optional[datetime] = Field(
        default=None, description="Estimated completion time"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
