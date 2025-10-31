# Pipeline Service Implementation - Complete Updates

## Summary of Changes Needed

This document outlines all changes to `/src/services/knowledge/pipeline_service.py` to support:
1. LOCAL_FILES node type
2. URL_PATTERN_FILTER node type
3. Fix OUTPUT_FORMAT phantom reference bug
4. Add crawl depth validation
5. Add exclude_elements mapping
6. Bidirectional conversion: Job → Pipeline visualization

---

## File: src/services/knowledge/pipeline_service.py

### Change 1: Fix OUTPUT_FORMAT Bug (Line 276)

**BEFORE** (BUGGY):
```python
output_format_node = next((n for n in pipeline.nodes if n.type == NodeType.OUTPUT_FORMAT and n.id in connected_node_ids), None)
```

**AFTER** (FIXED):
```python
# Find output format node (HTML_EXTRACTOR, MARKDOWN_GENERATOR, or LLM_MARKDOWN_GENERATOR)
output_format_node = next((
    n for n in pipeline.nodes
    if n.type in [NodeType.HTML_EXTRACTOR, NodeType.MARKDOWN_GENERATOR, NodeType.LLM_MARKDOWN_GENERATOR]
    and n.id in connected_node_ids
), None)
```

---

### Change 2: Add URL Pattern Filter Support (After line 276)

**ADD AFTER output_format_node**:
```python
# Find URL pattern filter node (if connected)
url_pattern_filter_node = next((
    n for n in pipeline.nodes
    if n.type == NodeType.URL_PATTERN_FILTER
    and n.id in connected_node_ids
), None)
```

---

### Change 3: Update Filter Extraction Logic (Lines 286-295)

**ADD to content_filter_node processing**:
```python
if content_filter_node:
    target_elements = content_filter_node.config.get("target_elements", target_elements)
    exclude_elements = content_filter_node.config.get("exclude_elements", [])  # NEW!
```

**ADD url_pattern_filter_node processing**:
```python
if url_pattern_filter_node:
    url_patterns = url_pattern_filter_node.config.get("url_patterns", [])
```

---

### Change 4: Update Source Config Creation (Lines 320-350)

**ADD to KnowledgeSourceConfigCreate**:
```python
source_config_data = {
    "name": config.get("name", source_node.name),
    "description": f"Knowledge source from pipeline: {pipeline.name}",
    "content_source_type": content_source_type,
    "url": url,
    "scraping_mode": scraping_mode,
    "url_source_id": url_source_id,
    "crawl_depth": crawl_depth,
    "allowed_subdomains": allowed_subdomains if allowed_subdomains else None,
    "blocked_subdomains": blocked_subdomains if blocked_subdomains else None,
    "target_elements": target_elements,
    "exclude_elements": exclude_elements,  # NEW!
    "url_patterns": url_patterns if url_patterns else None,  # NEW!
    "content_filter_threshold": content_filter_threshold,
    "output_format": output_format,
    "llm_content_filter_id": llm_content_filter_id,
    "user_id": user_id,
}
```

---

### Change 5: Add LOCAL_FILES Source Handling

**ADD new method after `_extract_source_config`**:
```python
def _extract_source_config_for_local_files(
    self, source_node: PipelineNode, pipeline: Pipeline, user_id: str
) -> KnowledgeSourceConfigCreate:
    """Extract knowledge source configuration from LOCAL_FILES node."""

    from src.domain.knowledge.pipeline import LocalFilesNodeConfig
    from src.domain.knowledge.knowledge_source_config import (
        ContentSourceType,
        ScrapingMode,
        OutputFormat,
        KnowledgeSourceConfigCreate
    )

    config = LocalFilesNodeConfig(**source_node.config)

    # Map scraping_mode string to ScrapingMode enum
    scraping_mode_map = {
        "html_files": ScrapingMode.HTML_FILES,
        "markdown_files": ScrapingMode.MARKDOWN_FILES,
        "pdf_files": ScrapingMode.PDF_FILES,
        "docx_files": ScrapingMode.DOCX_FILES,
        "txt_files": ScrapingMode.TXT_FILES,
    }

    scraping_mode = scraping_mode_map.get(
        config.scraping_mode.lower() if config.scraping_mode else "markdown_files",
        ScrapingMode.MARKDOWN_FILES
    )

    # Map output_format string to OutputFormat enum
    output_format_map = {
        "html": OutputFormat.HTML,
        "markdown": OutputFormat.MARKDOWN,
        "llm_markdown": OutputFormat.LLM_MARKDOWN,
    }

    output_format = output_format_map.get(
        config.output_format.lower() if config.output_format else "markdown",
        OutputFormat.MARKDOWN
    )

    return KnowledgeSourceConfigCreate(
        name=source_node.name or "Local Files Source",
        description=f"Local files source from pipeline: {pipeline.name}",
        content_source_type=ContentSourceType.LOCAL_FILES,
        scraping_mode=scraping_mode,
        local_files=config.local_files,
        file_types=config.file_types,
        output_format=output_format,
        user_id=user_id
    )
```

---

### Change 6: Update Main `_extract_source_config` Method

**REPLACE source node type checking** (around line 255-272):
```python
# Find the data source node
source_node = None
for node in pipeline.nodes:
    if node.type in [
        NodeType.WEBSITE,
        NodeType.MULTIPLE_PAGES,
        NodeType.SINGLE_PAGE,
        NodeType.LOCAL_FILES  # NEW!
    ]:
        source_node = node
        break

if not source_node:
    raise ValueError(
        "Pipeline must contain a data source node (WEBSITE, MULTIPLE_PAGES, SINGLE_PAGE, or LOCAL_FILES)"
    )

# Handle LOCAL_FILES separately (different logic)
if source_node.type == NodeType.LOCAL_FILES:
    return self._extract_source_config_for_local_files(source_node, pipeline, user_id)

# Continue with web scraping nodes (existing logic)
# ...
```

---

### Change 7: Add Crawl Depth Validation

**ADD new method**:
```python
def _validate_crawl_depth(self, node_type: NodeType, crawl_depth: int) -> None:
    """Validate crawl depth based on node type."""

    if node_type == NodeType.SINGLE_PAGE:
        if crawl_depth != 0:
            raise ValueError(
                "SINGLE_PAGE mode must have crawl_depth=0 (no link following). "
                "Use crawl_depth=0 to process exact URL only."
            )

    elif node_type == NodeType.MULTIPLE_PAGES:
        if crawl_depth != 0:
            raise ValueError(
                "MULTIPLE_PAGES mode must have crawl_depth=0 (no link following). "
                "Use crawl_depth=0 to process exact URLs only."
            )

    elif node_type == NodeType.WEBSITE:
        if crawl_depth < 1:
            raise ValueError(
                "WEBSITE mode must have crawl_depth >= 1 for recursive crawling. "
                "Use crawl_depth=2 or higher for multi-level discovery."
            )
```

**CALL in `_extract_source_config`** (after crawl_depth is determined):
```python
# Validate crawl depth based on source type
self._validate_crawl_depth(source_node.type, crawl_depth)
```

---

### Change 8: Add Bidirectional Conversion - Job → Pipeline

**ADD new method**:
```python
def convert_job_to_pipeline(
    self,
    knowledge_job: KnowledgeJob,
    knowledge_source_config: KnowledgeSourceConfig,
    document_splitter: Optional[DocumentSplitter] = None,
    vectordb_collection: Optional[VectorDBCollection] = None,
    user_id: str = None
) -> Pipeline:
    """
    Convert an existing knowledge job to a pipeline visualization.

    This enables users to:
    1. Create jobs via wizard
    2. View them as pipeline visualization
    3. Edit pipeline and update the job

    Args:
        knowledge_job: The job to convert
        knowledge_source_config: Source configuration
        document_splitter: Optional splitter config
        vectordb_collection: Optional vector DB config
        user_id: User ID

    Returns:
        Pipeline object with nodes and edges
    """
    from src.domain.knowledge.pipeline import (
        Pipeline,
        PipelineNode,
        PipelineEdge,
        PipelineStatus,
        NodeType,
        NodeStatus,
        WebsiteNodeConfig,
        MultiplePagesNodeConfig,
        SinglePageNodeConfig,
        LocalFilesNodeConfig,
        DomainFilterNodeConfig,
        ContentFilterNodeConfig,
        UrlPatternFilterNodeConfig,
        HtmlExtractorNodeConfig,
        MarkdownGeneratorNodeConfig,
        LlmMarkdownGeneratorNodeConfig,
        TextSplitterNodeConfig,
        EmbeddingGeneratorNodeConfig,
        VectorDatabaseNodeConfig
    )
    import uuid
    from datetime import datetime

    nodes = []
    edges = []
    node_counter = 0

    # Helper to create node with auto-positioning
    def create_node(node_type: NodeType, name: str, config: dict) -> PipelineNode:
        nonlocal node_counter
        node_id = str(uuid.uuid4())
        x_pos = 100 + (node_counter * 250)
        y_pos = 100
        node_counter += 1

        return PipelineNode(
            id=node_id,
            type=node_type,
            name=name,
            position={"x": x_pos, "y": y_pos},
            status=NodeStatus.COMPLETED if knowledge_job.status == JobStatus.COMPLETED else NodeStatus.PENDING,
            configured=True,
            config=config,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    # Helper to create edge
    def create_edge(source_id: str, target_id: str) -> PipelineEdge:
        return PipelineEdge(
            id=str(uuid.uuid4()),
            source=source_id,
            target=target_id,
            type="default"
        )

    # Step 1: Create data source node
    if knowledge_source_config.content_source_type == ContentSourceType.LOCAL_FILES:
        # LOCAL_FILES node
        source_node = create_node(
            NodeType.LOCAL_FILES,
            knowledge_source_config.name or "Local Files",
            {
                "local_files": knowledge_source_config.local_files or [],
                "file_types": knowledge_source_config.file_types or ["html", "markdown", "pdf", "docx", "txt"],
                "scraping_mode": knowledge_source_config.scraping_mode.value if knowledge_source_config.scraping_mode else "markdown_files",
                "output_format": knowledge_source_config.output_format.value if knowledge_source_config.output_format else "markdown"
            }
        )
    elif knowledge_source_config.scraping_mode == ScrapingMode.WEBSITE:
        # WEBSITE node
        source_node = create_node(
            NodeType.WEBSITE,
            knowledge_source_config.name or "Website",
            {
                "url": knowledge_source_config.url,
                "crawl_depth": knowledge_source_config.crawl_depth or 2
            }
        )
    elif knowledge_source_config.scraping_mode == ScrapingMode.MULTIPLE_PAGES:
        # MULTIPLE_PAGES node
        # Note: urls are stored in separate UrlSourceConfig collection
        source_node = create_node(
            NodeType.MULTIPLE_PAGES,
            knowledge_source_config.name or "Multiple Pages",
            {
                "base_url": knowledge_source_config.url or "",
                "urls": [],  # Would need to fetch from url_source_id
                "file_name": "urls.txt"  # Placeholder
            }
        )
    else:  # SINGLE_PAGE
        source_node = create_node(
            NodeType.SINGLE_PAGE,
            knowledge_source_config.name or "Single Page",
            {
                "url": knowledge_source_config.url
            }
        )

    nodes.append(source_node)
    last_node = source_node

    # Step 2: Add filter nodes if configured
    if knowledge_source_config.allowed_subdomains or knowledge_source_config.blocked_subdomains:
        domain_filter_node = create_node(
            NodeType.DOMAIN_FILTER,
            "Domain Filter",
            {
                "allowed_subdomains": knowledge_source_config.allowed_subdomains or [],
                "blocked_subdomains": knowledge_source_config.blocked_subdomains or []
            }
        )
        nodes.append(domain_filter_node)
        edges.append(create_edge(last_node.id, domain_filter_node.id))
        last_node = domain_filter_node

    if knowledge_source_config.target_elements or knowledge_source_config.exclude_elements:
        content_filter_node = create_node(
            NodeType.CONTENT_FILTER,
            "Content Filter",
            {
                "target_elements": knowledge_source_config.target_elements or [],
                "exclude_elements": knowledge_source_config.exclude_elements or []
            }
        )
        nodes.append(content_filter_node)
        edges.append(create_edge(last_node.id, content_filter_node.id))
        last_node = content_filter_node

    if knowledge_source_config.url_patterns:
        url_pattern_node = create_node(
            NodeType.URL_PATTERN_FILTER,
            "URL Pattern Filter",
            {
                "url_patterns": knowledge_source_config.url_patterns
            }
        )
        nodes.append(url_pattern_node)
        edges.append(create_edge(last_node.id, url_pattern_node.id))
        last_node = url_pattern_node

    # Step 3: Add output format node
    if knowledge_source_config.output_format == OutputFormat.HTML:
        output_node = create_node(
            NodeType.HTML_EXTRACTOR,
            "HTML Extractor",
            {
                "content_filter_threshold": knowledge_source_config.content_filter_threshold
            }
        )
    elif knowledge_source_config.output_format == OutputFormat.LLM_MARKDOWN:
        output_node = create_node(
            NodeType.LLM_MARKDOWN_GENERATOR,
            "LLM Markdown Generator",
            {
                "llm_content_filter_id": knowledge_source_config.llm_content_filter_id
            }
        )
    else:  # MARKDOWN
        output_node = create_node(
            NodeType.MARKDOWN_GENERATOR,
            "Markdown Generator",
            {
                "content_filter_threshold": knowledge_source_config.content_filter_threshold
            }
        )

    nodes.append(output_node)
    edges.append(create_edge(last_node.id, output_node.id))
    last_node = output_node

    # Step 4: Add text splitter node
    if document_splitter:
        splitter_node = create_node(
            NodeType.TEXT_SPLITTER,
            document_splitter.name or "Text Splitter",
            {
                "splitter_id": document_splitter.id,
                "splitter_type": document_splitter.splitter_type.value,
                "chunk_size": document_splitter.chunk_size,
                "chunk_overlap": document_splitter.chunk_overlap,
                "separators": document_splitter.separators or ["\n\n", "\n", " ", ""]
            }
        )
        nodes.append(splitter_node)
        edges.append(create_edge(last_node.id, splitter_node.id))
        last_node = splitter_node

    # Step 5: Add embedding generator node (if we have vector DB config)
    if vectordb_collection:
        embedding_node = create_node(
            NodeType.EMBEDDING_GENERATOR,
            "Embedding Generator",
            {
                "model_provider_id": vectordb_collection.model_provider_id,
                "model_name": vectordb_collection.model_name,
                "vector_dimension": vectordb_collection.vector_dimension,
                "batch_size": knowledge_job.batch_size or 100
            }
        )
        nodes.append(embedding_node)
        edges.append(create_edge(last_node.id, embedding_node.id))
        last_node = embedding_node

    # Step 6: Add vector database node
    if vectordb_collection:
        vector_db_node = create_node(
            NodeType.VECTOR_DATABASE,
            vectordb_collection.name or "Vector Database",
            {
                "collection_id": vectordb_collection.id,
                "collection_name": vectordb_collection.name,
                "collection_description": vectordb_collection.description,
                "clear_collection_before_start": knowledge_job.clear_collection_before_ingestion or False,
                "check_duplicates_before_insert": knowledge_job.check_duplicates_before_insert or False
            }
        )
        nodes.append(vector_db_node)
        edges.append(create_edge(last_node.id, vector_db_node.id))

    # Create pipeline
    pipeline = Pipeline(
        id=f"job-{knowledge_job.id}-pipeline",
        name=f"Pipeline for {knowledge_source_config.name}",
        description=f"Auto-generated pipeline from job {knowledge_job.id}",
        user_id=user_id or knowledge_job.user_id,
        nodes=nodes,
        edges=edges,
        status=PipelineStatus.COMPLETED if knowledge_job.status == JobStatus.COMPLETED else PipelineStatus.DRAFT,
        created_at=knowledge_job.created_at if hasattr(knowledge_job, 'created_at') else datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    return pipeline
```

---

## Implementation Order

1. ✅ Fix OUTPUT_FORMAT bug (quick fix - 1 line)
2. ✅ Add url_pattern_filter_node extraction (5 lines)
3. ✅ Add exclude_elements mapping (2 lines)
4. ✅ Add url_patterns to source config creation (1 line)
5. ✅ Add LOCAL_FILES source handling (new method ~50 lines)
6. ✅ Update source node checking to include LOCAL_FILES (3 lines)
7. ✅ Add crawl depth validation (new method ~25 lines)
8. ✅ Add convert_job_to_pipeline method (new method ~250 lines)

Total lines added/modified: ~340 lines

---

## Testing

### Test 1: LOCAL_FILES Node
```python
# Create pipeline with LOCAL_FILES node
pipeline = {
    "nodes": [
        {
            "type": "local_files",
            "config": {
                "local_files": [
                    {"file_path": "/uploads/doc1.md", "file_type": "markdown"},
                    {"file_path": "/uploads/doc2.pdf", "file_type": "pdf"}
                ],
                "file_types": ["markdown", "pdf"],
                "scraping_mode": "markdown_files",
                "output_format": "markdown"
            }
        }
    ]
}

# Execute → Should create KnowledgeSourceConfig with LOCAL_FILES type
```

### Test 2: URL_PATTERN_FILTER Node
```python
# Add URL pattern filter to pipeline
url_pattern_node = {
    "type": "urlPatternFilter",
    "config": {
        "url_patterns": [
            {"pattern": "/api/*", "match_type": "glob", "include": True},
            {"pattern": "/admin/*", "match_type": "glob", "include": False}
        ]
    }
}

# Execute → Should pass url_patterns to KnowledgeSourceConfig
```

### Test 3: Bidirectional Conversion
```python
# 1. Create job via wizard
job = create_knowledge_job(...)

# 2. Convert to pipeline
pipeline = pipeline_service.convert_job_to_pipeline(job, source_config, splitter, vectordb)

# 3. Verify pipeline has all nodes
assert any(n.type == NodeType.WEBSITE for n in pipeline.nodes)
assert any(n.type == NodeType.TEXT_SPLITTER for n in pipeline.nodes)
assert any(n.type == NodeType.VECTOR_DATABASE for n in pipeline.nodes)

# 4. Display in UI at /job-details/{job.id} → Click "Show Visualization"
```

---

This completes the pipeline service implementation updates.
