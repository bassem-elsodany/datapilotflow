"""
Pipeline Service.

This service handles business logic for pipelines, which are visual templates
that orchestrate existing knowledge services (sources, jobs, splitters, collections).
"""

from datetime import datetime
from typing import Any, List, Optional

from loguru import logger

from src.domain.knowledge.document_splitter import DocumentSplitterCreate, SplitterType
from src.domain.knowledge.knowledge_job import KnowledgeJob, KnowledgeJobCreate
from src.domain.knowledge.knowledge_source_config import (
    ContentSourceType,
    KnowledgeSourceConfig,
    KnowledgeSourceConfigCreate,
    OutputFormat,
    ScrapingMode,
    UrlSourceConfigCreate,
)
from src.domain.knowledge.pipeline import (
    NodeType,
    Pipeline,
    PipelineCreate,
    PipelineEdge,
    PipelineExecutionRequest,
    PipelineExecutionStatus,
    PipelineNode,
    PipelineStatus,
    PipelineUpdate,
)
from src.domain.knowledge.vectordb_collection import VectorDBCollectionCreate
from src.services.knowledge.dao.pipeline_dao import PipelineDAO
from src.services.knowledge.document_splitter_service import DocumentSplitterService
from src.services.knowledge.knowledge_job_service import KnowledgeJobService
from src.services.knowledge.knowledge_source_service import KnowledgeSourceService
from src.services.knowledge.vectordb_collection_service import VectorDBCollectionService


class PipelineService:
    """Service for managing pipelines and orchestrating their execution."""

    def __init__(self):
        self.pipeline_dao = PipelineDAO()
        self.knowledge_source_service = KnowledgeSourceService()
        self.knowledge_job_service = KnowledgeJobService()
        self.document_splitter_service = DocumentSplitterService()
        self.vectordb_collection_service = VectorDBCollectionService()

    def create_pipeline(self, pipeline_data: PipelineCreate, user_id: str) -> Pipeline:
        """Create a new pipeline template."""
        pipeline_id = self.pipeline_dao.create_pipeline(pipeline_data, user_id)
        if not pipeline_id:
            raise ValueError("Failed to create pipeline")

        pipeline = self.pipeline_dao.get_pipeline(pipeline_id, user_id)
        if not pipeline:
            raise ValueError("Failed to retrieve created pipeline")

        return pipeline

    def get_pipeline(self, pipeline_id: str, user_id: str) -> Optional[Pipeline]:
        """Get a pipeline by ID."""
        return self.pipeline_dao.get_pipeline(pipeline_id, user_id)

    def list_pipelines(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[Pipeline]:
        """List pipelines for a user."""
        return self.pipeline_dao.list_pipelines(user_id, skip, limit)

    def update_pipeline(
        self, pipeline_id: str, user_id: str, update_data: PipelineUpdate
    ) -> Optional[Pipeline]:
        """Update a pipeline template."""
        return self.pipeline_dao.update_pipeline(pipeline_id, user_id, update_data)

    def delete_pipeline(self, pipeline_id: str, user_id: str) -> bool:
        """Delete a pipeline."""
        return self.pipeline_dao.delete_pipeline(pipeline_id, user_id)

    def execute_pipeline(self, request: PipelineExecutionRequest, user_id: str) -> dict:
        """
        Execute a pipeline by converting it into knowledge source + job execution.

        This method:
        1. Validates the pipeline structure
        2. Creates knowledge source config from data source nodes
        3. Creates document splitter config from splitter nodes
        4. Creates/uses vector DB collection from storage nodes
        5. Creates and executes a KnowledgeJob

        Returns execution details including job_id for tracking.
        """
        pipeline_id = request.pipeline_id

        # Get the pipeline
        pipeline = self.pipeline_dao.get_pipeline(pipeline_id, user_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        # Update pipeline status to running
        self.pipeline_dao.update_pipeline_status(pipeline_id, user_id, "running")

        try:
            # Extract configurations from pipeline nodes
            source_config = self._extract_source_config(pipeline, user_id)
            splitter_config = self._extract_splitter_config(pipeline, user_id)
            vectordb_config = self._extract_vectordb_config(pipeline, user_id)

            # Create knowledge source configuration
            logger.info(f"Creating knowledge source from pipeline {pipeline_id}")
            knowledge_source = (
                self.knowledge_source_service.create_knowledge_source_config(
                    source_config, user_id
                )
            )

            # Create or get document splitter
            splitter_id = None
            if splitter_config:
                logger.info(f"Creating document splitter from pipeline {pipeline_id}")
                splitter = self.document_splitter_service.create_splitter(
                    splitter_config, user_id
                )
                splitter_id = splitter.id

            # Create or get vector DB collection
            collection_id = None
            if vectordb_config:
                logger.info(
                    f"Creating vector DB collection from pipeline {pipeline_id}"
                )
                collection = self.vectordb_collection_service.create_collection(
                    vectordb_config, user_id
                )
                collection_id = collection.id

            # Create knowledge job
            job_config = KnowledgeJobCreate(
                name=f"{pipeline.name} - Execution",
                description=f"Automated execution from pipeline: {pipeline.name}",
                splitter_id=splitter_id,
                existing_collection_id=collection_id,
                batch_size=self._extract_batch_size(pipeline),
                save_to_file=self._should_save_to_file(pipeline),
                write_consolidated_file=False,
                clear_collection_before_start=self._should_clear_collection(pipeline),
                check_duplicates_before_insert=self._should_check_duplicates(pipeline),
            )

            logger.info(
                f"Creating and executing knowledge job from pipeline {pipeline_id}"
            )
            job = self.knowledge_job_service.create_knowledge_job(
                knowledge_source.id, job_config, user_id
            )

            # Execute the job
            self.knowledge_job_service.execute_job(job.id, user_id)

            # Update pipeline status
            self.pipeline_dao.update_pipeline_status(pipeline_id, user_id, "running")

            return {
                "pipeline_id": pipeline_id,
                "job_id": job.id,
                "knowledge_source_id": knowledge_source.id,
                "status": "running",
                "message": f"Pipeline execution started. Job ID: {job.id}",
            }

        except Exception as e:
            logger.error(f"Error executing pipeline {pipeline_id}: {e}")
            self.pipeline_dao.update_pipeline_status(pipeline_id, user_id, "failed")
            raise ValueError(f"Pipeline execution failed: {str(e)}")

    def get_execution_status(
        self, pipeline_id: str, user_id: str
    ) -> PipelineExecutionStatus:
        """Get the execution status of a pipeline."""
        pipeline = self.pipeline_dao.get_pipeline(pipeline_id, user_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        # Calculate progress based on node statuses
        total_nodes = len(pipeline.nodes)
        completed_nodes = sum(
            1 for node in pipeline.nodes if node.status == "completed"
        )
        progress = (completed_nodes / total_nodes * 100) if total_nodes > 0 else 0

        # Find current running node
        current_node = None
        for node in pipeline.nodes:
            if node.status == "running":
                current_node = node.id
                break

        return PipelineExecutionStatus(
            pipeline_id=pipeline_id,
            status=pipeline.status,
            current_node=current_node,
            progress=progress,
            nodes_status=pipeline.nodes,
            started_at=pipeline.last_executed_at,
            estimated_completion=None,  # TODO: Calculate based on historical data
            error_message=None,
        )

    def _get_connected_nodes(
        self, start_node_id: str, edges: List[Any], nodes: List[Any]
    ) -> set:
        """
        Get all node IDs that are reachable from the start node by following edges.

        This performs a breadth-first search through the pipeline graph to find
        all nodes that are downstream (directly or indirectly connected) from the start node.

        Args:
            start_node_id: The ID of the starting node
            edges: List of edges (connections) in the pipeline
            nodes: List of all nodes in the pipeline

        Returns:
            Set of node IDs that are reachable from the start node
        """
        visited = set()
        queue = [start_node_id]

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue

            visited.add(current_id)

            # Find all edges where current node is the source
            for edge in edges:
                if edge.source == current_id and edge.target not in visited:
                    queue.append(edge.target)

        return visited

    def _extract_source_config(
        self, pipeline: Pipeline, user_id: str
    ) -> KnowledgeSourceConfigCreate:
        """Extract knowledge source configuration from pipeline nodes.

        Combines configurations from multiple CONNECTED nodes:
        - Source node (website/multiple_pages/single_page) for URL and depth
        - Optional Domain Filter node for subdomain rules (if connected)
        - Optional Content Filter node for CSS selectors (if connected)
        - Optional Output Format node for format settings (if connected)

        Follows the node connections (edges) to determine which filters apply.
        """
        # Find the data source node (website, multiple_pages, single_page, local_files)
        source_node = None
        for node in pipeline.nodes:
            if node.type in [
                NodeType.WEBSITE,
                NodeType.MULTIPLE_PAGES,
                NodeType.SINGLE_PAGE,
                NodeType.LOCAL_FILES,
            ]:
                source_node = node
                break

        if not source_node:
            raise ValueError("Pipeline must have a data source node")

        config = source_node.config

        # Find CONNECTED filter nodes by following edges from source node
        # This ensures we only use filters that are actually in the pipeline flow
        connected_node_ids = self._get_connected_nodes(
            source_node.id, pipeline.edges, pipeline.nodes
        )

        domain_filter_node = next(
            (
                n
                for n in pipeline.nodes
                if n.type == NodeType.DOMAIN_FILTER and n.id in connected_node_ids
            ),
            None,
        )
        content_filter_node = next(
            (
                n
                for n in pipeline.nodes
                if n.type == NodeType.CONTENT_FILTER and n.id in connected_node_ids
            ),
            None,
        )
        url_pattern_filter_node = next(
            (
                n
                for n in pipeline.nodes
                if n.type == NodeType.URL_PATTERN_FILTER and n.id in connected_node_ids
            ),
            None,
        )
        # Note: OUTPUT_FORMAT is not a NodeType - format is configured in source node or content filter node
        # Removed phantom reference to NodeType.OUTPUT_FORMAT

        # Extract configurations from filter nodes
        allowed_subdomains = config.get("allowed_subdomains", [])
        blocked_subdomains = config.get("blocked_subdomains", [])
        target_elements = config.get("target_elements", [])
        exclude_elements = config.get("exclude_elements", [])
        url_patterns = config.get("url_patterns", [])
        output_format = config.get("output_format", "markdown")
        llm_content_filter_id = config.get("llm_content_filter_id")
        content_filter_threshold = config.get("content_filter_threshold", 0.6)

        # Override with filter node configs if present
        if domain_filter_node:
            allowed_subdomains = domain_filter_node.config.get(
                "allowed_subdomains", allowed_subdomains
            )
            blocked_subdomains = domain_filter_node.config.get(
                "blocked_subdomains", blocked_subdomains
            )

        if content_filter_node:
            target_elements = content_filter_node.config.get(
                "target_elements", target_elements
            )
            exclude_elements = content_filter_node.config.get(
                "exclude_elements", exclude_elements
            )
            # Output format can also be configured in content filter node
            output_format = content_filter_node.config.get(
                "output_format", output_format
            )
            llm_content_filter_id = content_filter_node.config.get(
                "llm_content_filter_id", llm_content_filter_id
            )
            content_filter_threshold = content_filter_node.config.get(
                "content_filter_threshold", content_filter_threshold
            )

        if url_pattern_filter_node:
            url_patterns = url_pattern_filter_node.config.get(
                "url_patterns", url_patterns
            )

        # Map node type to scraping mode
        scraping_mode_map = {
            NodeType.WEBSITE: ScrapingMode.WEBSITE,
            NodeType.MULTIPLE_PAGES: ScrapingMode.MULTIPLE_PAGES,
            NodeType.SINGLE_PAGE: ScrapingMode.SINGLE_PAGE,
        }

        # Handle different source types
        if source_node.type == NodeType.WEBSITE:
            return KnowledgeSourceConfigCreate(
                name=source_node.name,
                description=f"Source from pipeline: {pipeline.name}",
                url=config.get("url", ""),
                scraping_mode=ScrapingMode.WEBSITE,
                crawl_depth=config.get("crawl_depth", 2),
                allowed_subdomains=allowed_subdomains,
                blocked_subdomains=blocked_subdomains,
                url_patterns=url_patterns,
                target_elements=target_elements,
                exclude_elements=exclude_elements,
                content_filter_threshold=content_filter_threshold,
                output_format=OutputFormat(output_format),
                llm_content_filter_id=llm_content_filter_id,
            )
        elif source_node.type == NodeType.MULTIPLE_PAGES:
            url_source = None
            if config.get("urls"):
                url_source = UrlSourceConfigCreate(
                    file_name=config.get("file_name", "pipeline_urls.txt"),
                    urls=config.get("urls", []),
                )
            return KnowledgeSourceConfigCreate(
                name=source_node.name,
                description=f"Source from pipeline: {pipeline.name}",
                url=config.get("base_url", ""),
                scraping_mode=ScrapingMode.MULTIPLE_PAGES,
                url_source=url_source,
                target_elements=target_elements,
                exclude_elements=exclude_elements,
                content_filter_threshold=content_filter_threshold,
                output_format=OutputFormat(output_format),
                llm_content_filter_id=llm_content_filter_id,
            )
        elif source_node.type == NodeType.SINGLE_PAGE:
            return KnowledgeSourceConfigCreate(
                name=source_node.name,
                description=f"Source from pipeline: {pipeline.name}",
                url=config.get("url", ""),
                scraping_mode=ScrapingMode.SINGLE_PAGE,
                crawl_depth=0,
                target_elements=target_elements,
                exclude_elements=exclude_elements,
                content_filter_threshold=content_filter_threshold,
                output_format=OutputFormat(output_format),
                llm_content_filter_id=llm_content_filter_id,
            )
        elif source_node.type == NodeType.LOCAL_FILES:
            # Handle local files source
            scraping_mode = ScrapingMode(config.get("scraping_mode", "markdown_files"))
            return KnowledgeSourceConfigCreate(
                name=source_node.name,
                description=f"Source from pipeline: {pipeline.name}",
                scraping_mode=scraping_mode,
                local_files=config.get("local_files", []),
                output_format=OutputFormat(output_format),
            )
        else:
            raise ValueError(f"Unsupported source type: {source_node.type}")

    def _extract_splitter_config(
        self, pipeline: Pipeline, user_id: str
    ) -> Optional[DocumentSplitterCreate]:
        """Extract document splitter configuration from pipeline nodes."""
        # Find the text splitter node
        splitter_node = None
        for node in pipeline.nodes:
            if node.type == NodeType.TEXT_SPLITTER:
                splitter_node = node
                break

        if not splitter_node:
            return None

        config = splitter_node.config

        # Check if referencing existing splitter
        if config.get("splitter_id"):
            # Just return the ID, service will handle it
            return None

        return DocumentSplitterCreate(
            name=splitter_node.name,
            description=f"Splitter from pipeline: {pipeline.name}",
            splitter_type=SplitterType(config.get("splitter_type", "text")),
            chunk_size=config.get("chunk_size", 512),
            chunk_overlap=config.get("chunk_overlap", 50),
            separators=config.get("separators", ["\n\n", "\n", " ", ""]),
        )

    def _extract_vectordb_config(
        self, pipeline: Pipeline, user_id: str
    ) -> Optional[VectorDBCollectionCreate]:
        """Extract vector DB collection configuration from pipeline nodes."""
        # Find the vector database node
        vectordb_node = None
        embedding_node = None

        for node in pipeline.nodes:
            if node.type == NodeType.VECTOR_DATABASE:
                vectordb_node = node
            elif node.type == NodeType.EMBEDDING_GENERATOR:
                embedding_node = node

        if not vectordb_node:
            return None

        config = vectordb_node.config

        # Check if using existing collection
        if config.get("collection_id"):
            return None

        # Need embedding generator config for vector dimensions
        if not embedding_node:
            raise ValueError(
                "Pipeline must have an embedding generator node for vector database"
            )

        embedding_config = embedding_node.config

        return VectorDBCollectionCreate(
            name=config.get("collection_name", f"{pipeline.name}_collection"),
            description=config.get(
                "collection_description",
                f"Collection from pipeline: {pipeline.name}",
            ),
            model_provider_id=embedding_config.get("model_provider_id"),
            model_name=embedding_config.get("model_name"),
            vector_dimension=embedding_config.get("vector_dimension"),
        )

    def _extract_batch_size(self, pipeline: Pipeline) -> int:
        """Extract batch size from embedding generator node."""
        for node in pipeline.nodes:
            if node.type == NodeType.EMBEDDING_GENERATOR:
                return node.config.get("batch_size", 100)
        return 100

    def _should_save_to_file(self, pipeline: Pipeline) -> bool:
        """Check if pipeline has file export node."""
        for node in pipeline.nodes:
            if node.type == NodeType.FILE_EXPORT:
                return True
        return False

    def _should_clear_collection(self, pipeline: Pipeline) -> bool:
        """Check if vector database node specifies clearing collection."""
        for node in pipeline.nodes:
            if node.type == NodeType.VECTOR_DATABASE:
                return node.config.get("clear_collection_before_start", False)
        return False

    def _should_check_duplicates(self, pipeline: Pipeline) -> bool:
        """Check if vector database node specifies duplicate checking."""
        for node in pipeline.nodes:
            if node.type == NodeType.VECTOR_DATABASE:
                return node.config.get("check_duplicates_before_insert", False)
        return False

    def convert_job_to_pipeline(
        self, job: KnowledgeJob, source_config: KnowledgeSourceConfig, user_id: str
    ) -> Pipeline:
        """
        Convert a KnowledgeJob and its source configuration to a Pipeline visualization.

        This enables bidirectional conversion: jobs created via wizard can be visualized
        as pipelines, and users can edit them in the pipeline builder.

        Args:
            job: The knowledge job to convert
            source_config: The source configuration for the job
            user_id: The user ID

        Returns:
            Pipeline object with nodes and edges representing the job
        """
        nodes = []
        edges = []
        node_id_counter = 1

        # Track node positions for visual layout (left to right flow)
        x_position = 100
        y_position = 250
        x_spacing = 300

        def create_node_id():
            nonlocal node_id_counter
            node_id = f"node-{node_id_counter}"
            node_id_counter += 1
            return node_id

        def add_node(node_type: NodeType, name: str, config: dict) -> str:
            nonlocal x_position
            node_id = create_node_id()
            nodes.append(
                PipelineNode(
                    id=node_id,
                    type=node_type,
                    name=name,
                    position={"x": x_position, "y": y_position},
                    status="pending",
                    configured=True,
                    config=config,
                )
            )
            x_position += x_spacing
            return node_id

        def add_edge(source_id: str, target_id: str):
            edges.append(
                PipelineEdge(
                    id=f"edge-{source_id}-{target_id}",
                    source=source_id,
                    target=target_id,
                    type="arrow",
                )
            )

        # Step 1: Create data source node based on content_source_type and scraping_mode
        last_node_id = None

        if source_config.content_source_type == ContentSourceType.LOCAL_FILES:
            # LOCAL_FILES source
            source_node_id = add_node(
                NodeType.LOCAL_FILES,
                "Local Files",
                {
                    "local_files": source_config.local_files or [],
                    "scraping_mode": source_config.scraping_mode.value,
                    "output_format": source_config.output_format.value,
                },
            )
            last_node_id = source_node_id

        elif source_config.scraping_mode == ScrapingMode.WEBSITE:
            # WEBSITE source (with crawling)
            source_node_id = add_node(
                NodeType.WEBSITE,
                "Website Crawler",
                {
                    "url": source_config.url or "",
                    "crawl_depth": source_config.crawl_depth or 2,
                    "allowed_subdomains": source_config.allowed_subdomains or [],
                    "blocked_subdomains": source_config.blocked_subdomains or [],
                },
            )
            last_node_id = source_node_id

        elif source_config.scraping_mode == ScrapingMode.MULTIPLE_PAGES:
            # MULTIPLE_PAGES source
            urls = []
            file_name = "urls.txt"

            # Safely check if url_source exists
            if hasattr(source_config, "url_source") and source_config.url_source:
                urls = source_config.url_source.urls or []
                file_name = source_config.url_source.file_name or "urls.txt"

            source_node_id = add_node(
                NodeType.MULTIPLE_PAGES,
                "Multiple Pages",
                {
                    "base_url": source_config.url or "",
                    "urls": urls,
                    "file_name": file_name,
                },
            )
            last_node_id = source_node_id

        elif source_config.scraping_mode == ScrapingMode.SINGLE_PAGE:
            # SINGLE_PAGE source
            source_node_id = add_node(
                NodeType.SINGLE_PAGE,
                "Single Page",
                {
                    "url": source_config.url or "",
                },
            )
            last_node_id = source_node_id

        # Step 2: Add filter nodes if configured

        # Domain filter (for web sources only)
        if source_config.content_source_type == ContentSourceType.WEB_SCRAPING and (
            source_config.allowed_subdomains or source_config.blocked_subdomains
        ):
            domain_filter_id = add_node(
                NodeType.DOMAIN_FILTER,
                "Domain Filter",
                {
                    "allowed_subdomains": source_config.allowed_subdomains or [],
                    "blocked_subdomains": source_config.blocked_subdomains or [],
                },
            )
            if last_node_id:
                add_edge(last_node_id, domain_filter_id)
            last_node_id = domain_filter_id

        # URL pattern filter
        if source_config.url_patterns:
            url_filter_id = add_node(
                NodeType.URL_PATTERN_FILTER,
                "URL Pattern Filter",
                {
                    "url_patterns": source_config.url_patterns,
                },
            )
            if last_node_id:
                add_edge(last_node_id, url_filter_id)
            last_node_id = url_filter_id

        # Content filter (CSS selectors)
        if source_config.target_elements or source_config.exclude_elements:
            content_filter_id = add_node(
                NodeType.CONTENT_FILTER,
                "Content Filter",
                {
                    "target_elements": source_config.target_elements or [],
                    "exclude_elements": source_config.exclude_elements or [],
                    "output_format": source_config.output_format.value,
                },
            )
            if last_node_id:
                add_edge(last_node_id, content_filter_id)
            last_node_id = content_filter_id

        # LLM content filter
        if source_config.llm_content_filter_id:
            llm_filter_id = add_node(
                NodeType.LLM_CONTENT_FILTER,
                "LLM Content Filter",
                {
                    "llm_content_filter_id": source_config.llm_content_filter_id,
                    "content_filter_threshold": source_config.content_filter_threshold
                    or 0.6,
                },
            )
            if last_node_id:
                add_edge(last_node_id, llm_filter_id)
            last_node_id = llm_filter_id

        # Step 3: Add document splitter node if configured
        if job.splitter_id:
            # Fetch splitter details
            splitter = self.document_splitter_service.get_splitter_by_id(
                job.splitter_id
            )
            if splitter:
                splitter_id = add_node(
                    NodeType.TEXT_SPLITTER,
                    "Text Splitter",
                    {
                        "splitter_id": splitter.id,
                        "splitter_type": splitter.splitter_type.value,
                        "chunk_size": splitter.chunk_size,
                        "chunk_overlap": splitter.chunk_overlap,
                        "separators": ["\n\n", "\n", " ", ""],  # Default separators
                    },
                )
                if last_node_id:
                    add_edge(last_node_id, splitter_id)
                last_node_id = splitter_id

        # Step 4: Add embedding generator node
        # Fetch collection details to get embedding model info
        if job.vectordb_collection_id:
            collection = self.vectordb_collection_service.get_collection(
                job.vectordb_collection_id, user_id
            )
            if collection:
                embedding_id = add_node(
                    NodeType.EMBEDDING_GENERATOR,
                    "Embedding Generator",
                    {
                        "model_provider_id": collection.embedding_model_provider_id,
                        "model_name": collection.embedding_model_name,
                        "vector_dimension": collection.vector_dimension,
                        "batch_size": job.batch_size or 100,
                    },
                )
                if last_node_id:
                    add_edge(last_node_id, embedding_id)
                last_node_id = embedding_id

                # Step 5: Add vector database node
                vectordb_id = add_node(
                    NodeType.VECTOR_DATABASE,
                    "Vector Database",
                    {
                        "collection_id": collection.id,
                        "collection_name": collection.collection_name,
                        "clear_collection_before_start": job.clear_collection_before_start
                        or False,
                        "check_duplicates_before_insert": job.check_duplicates_before_insert
                        or False,
                    },
                )
                if last_node_id:
                    add_edge(last_node_id, vectordb_id)
                last_node_id = vectordb_id

        # Step 6: Add file export node if configured
        if job.save_to_file:
            file_export_id = add_node(
                NodeType.FILE_EXPORT,
                "File Export",
                {
                    "save_to_file": True,
                    "write_consolidated_file": job.write_consolidated_file or False,
                },
            )
            if last_node_id:
                add_edge(last_node_id, file_export_id)
            last_node_id = file_export_id

        # Create and return pipeline
        return Pipeline(
            id=f"job-{job.id}",
            user_id=user_id,
            name=f"Job: {source_config.name}",
            description=f"Pipeline visualization of job {job.id}",
            nodes=nodes,
            edges=edges,
            status=PipelineStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=user_id,
            updated_by=user_id,
        )


# Global instance for dependency injection
_pipeline_service: Optional[PipelineService] = None


def get_pipeline_service() -> PipelineService:
    """Get or create the global pipeline service instance."""
    global _pipeline_service
    if _pipeline_service is None:
        _pipeline_service = PipelineService()
    return _pipeline_service
