# Pipeline Builder Alignment Analysis

## Executive Summary

This document analyzes the **misalignments** between the current Pipeline Builder node configurations and the actual Knowledge Source Config used during job execution. It identifies gaps, missing features, and proposes a comprehensive alignment strategy.

---

## Current State vs. Desired State

### Knowledge Source Config Structure (Source of Truth)

The **KnowledgeSourceConfig** is the actual configuration used when jobs execute. It supports:

#### Content Source Types:
1. **WEB_SCRAPING** - Extract content from web pages
2. **LOCAL_FILES** - Process uploaded files

#### Scraping Modes (ScrapingMode enum):

**Web Scraping Modes:**
- `SINGLE_PAGE` - Process one specific URL
- `MULTIPLE_PAGES` - Process user-provided list of URLs (uses UrlSourceConfig)
- `WEBSITE` - Recursively crawl entire website

**Local Files Modes:**
- `HTML_FILES` - HTML files only
- `MARKDOWN_FILES` - Markdown files only
- `PDF_FILES` - PDF files only
- `DOCX_FILES` - DOCX files only
- `TXT_FILES` - TXT files only

#### Output Formats:
- `HTML` - Raw HTML content
- `MARKDOWN` - Structured markdown
- `LLM_MARKDOWN` - LLM-powered markdown with content filtering

#### All Configuration Fields:

**Common Fields:**
```python
id, user_id, name, description
content_source_type  # WEB_SCRAPING or LOCAL_FILES
created_at, updated_at, created_by, updated_by
```

**Web Scraping Fields:**
```python
url                      # Base URL
scraping_mode           # SINGLE_PAGE, MULTIPLE_PAGES, or WEBSITE
url_source_id           # For MULTIPLE_PAGES mode (links to UrlSourceConfig)
crawl_depth             # 0=exact URL only, 1+=recursive crawling
allowed_subdomains[]    # Subdomain whitelist
blocked_subdomains[]    # Subdomain blacklist
url_patterns[]          # URL pattern filters
target_elements[]       # CSS selectors for content extraction
content_filter_threshold  # 0.0-1.0 (default 0.6)
output_format           # HTML, MARKDOWN, or LLM_MARKDOWN
llm_content_filter_id   # ID of LLM filter config (for LLM_MARKDOWN)
```

**Local Files Fields:**
```python
local_files[]           # List of {file_path, original_filename, file_type, file_size, upload_date}
file_types[]            # Supported: html, markdown, pdf, docx, txt
scraping_mode           # HTML_FILES, MARKDOWN_FILES, PDF_FILES, DOCX_FILES, or TXT_FILES
```

---

## Pipeline Builder Current State

### Available Node Types (21 total):

**Data Source Nodes (3):**
1. `WEBSITE` - WebsiteNodeConfig
2. `MULTIPLE_PAGES` - MultiplePagesNodeConfig
3. `SINGLE_PAGE` - SinglePageNodeConfig

**Filter Nodes (2):**
4. `DOMAIN_FILTER` - DomainFilterNodeConfig
5. `CONTENT_FILTER` - ContentFilterNodeConfig

**Output Format Nodes (3):**
6. `HTML_EXTRACTOR` - HtmlExtractorNodeConfig
7. `MARKDOWN_GENERATOR` - MarkdownGeneratorNodeConfig
8. `LLM_MARKDOWN_GENERATOR` - LlmMarkdownGeneratorNodeConfig

**Processing Nodes (1):**
9. `TEXT_SPLITTER` - TextSplitterNodeConfig

**AI Nodes (1):**
10. `EMBEDDING_GENERATOR` - EmbeddingGeneratorNodeConfig

**Storage Nodes (2):**
11. `VECTOR_DATABASE` - VectorDatabaseNodeConfig
12. `FILE_EXPORT` - FileExportNodeConfig

**Advanced Processing Nodes (4 - defined but not implemented):**
13. `TEXT_SUMMARIZER` - TextSummarizerNodeConfig
14. `CONTENT_CLASSIFIER` - ContentClassifierNodeConfig
15. `CONTENT_ENRICHER` - ContentEnricherNodeConfig
16. `TRANSLATION` - TranslationNodeConfig

**Output Nodes (3 - defined but not implemented):**
17. `REPORT_GENERATOR` - ReportGeneratorNodeConfig
18. `ANALYTICS` - AnalyticsNodeConfig
19. `NOTIFICATION` - NotificationNodeConfig

---

## Critical Misalignments Identified

### 1. **MISSING: Local Files Support** ❌

**Gap**: Pipeline Builder has NO nodes for local file processing!

**What's Missing**:
- No `LOCAL_FILES` data source node
- No way to specify file types (HTML, Markdown, PDF, DOCX, TXT)
- No file upload interface in pipeline builder
- No file selection/configuration

**Impact**: Users cannot use pipeline builder for local file processing scenarios, forcing them to use the separate "Knowledge Source Config" UI instead.

**Required New Nodes**:
```python
LOCAL_FILES_SOURCE (NodeType)
  ├─ LocalFilesNodeConfig:
  │    ├─ file_types[] = ["html", "markdown", "pdf", "docx", "txt"]
  │    ├─ local_files[] = [{file_path, original_filename, file_type, ...}]
  │    └─ scraping_mode = HTML_FILES | MARKDOWN_FILES | PDF_FILES | DOCX_FILES | TXT_FILES
```

---

### 2. **INCOMPLETE: Web Scraping Modes** ⚠️

**Current State**:
- ✅ WEBSITE node exists
- ✅ SINGLE_PAGE node exists
- ✅ MULTIPLE_PAGES node exists

**Gap**: MULTIPLE_PAGES node config doesn't fully match UrlSourceConfig requirements

**MultiplePagesNodeConfig (Current)**:
```python
base_url: str           # Base URL for relative URL resolution
urls: List[str]         # Direct list of URLs (max ???)
file_name: str          # File name if uploaded
```

**UrlSourceConfig (Actual)**:
```python
id: str                 # Unique ID (auto-generated)
file_name: str          # Original filename
urls: List[str]         # Max 50,000 URLs!
created_at: datetime
updated_at: datetime
```

**Issues**:
- Pipeline node has `base_url` field but UrlSourceConfig doesn't (should it?)
- Pipeline node doesn't specify max URL limit (should be 50,000)
- Pipeline node doesn't handle file upload workflow
- Unclear how user provides URLs in pipeline builder UI:
  - Paste directly? (limited to ~100 URLs)
  - Upload file? (supports 50,000 URLs)
  - Both options?

---

### 3. **INCOMPLETE: Output Format Handling** ⚠️

**Current State**:
- ✅ HTML_EXTRACTOR node exists
- ✅ MARKDOWN_GENERATOR node exists
- ✅ LLM_MARKDOWN_GENERATOR node exists

**Gap**: Node configurations don't capture all required fields

**Current Node Configs**:
```python
HtmlExtractorNodeConfig:
    content_filter_threshold: float = 0.6

MarkdownGeneratorNodeConfig:
    content_filter_threshold: float = 0.6

LlmMarkdownGeneratorNodeConfig:
    llm_content_filter_id: str  # References LLM filter config
```

**What Maps To**:
```python
KnowledgeSourceConfig:
    output_format: OutputFormat  # HTML, MARKDOWN, or LLM_MARKDOWN
    content_filter_threshold: float = 0.6
    llm_content_filter_id: Optional[str]
```

**Issues**:
- ✅ Mapping works but is implicit (node type → output format)
- ⚠️  `content_filter_threshold` is duplicated across HTML and MARKDOWN nodes (should be single source of truth)
- ⚠️  Service code references mysterious `NodeType.OUTPUT_FORMAT` that doesn't exist in enum (line 276 in pipeline_service.py)

**Question**: Should output format be:
- **Option A**: Separate nodes (current approach - HTML_EXTRACTOR, MARKDOWN_GENERATOR, etc.)
- **Option B**: A property/dropdown on data source nodes?
- **Option C**: A separate OUTPUT_FORMAT node that can connect to any data source?

**Recommendation**: Keep current approach (Option A) but clarify the service code reference.

---

### 4. **INCOMPLETE: Domain & Content Filters** ⚠️

**Current State**:
- ✅ DOMAIN_FILTER node exists
- ✅ CONTENT_FILTER node exists

**DomainFilterNodeConfig (Current)**:
```python
allowed_subdomains: List[str] = []
blocked_subdomains: List[str] = []
```

**ContentFilterNodeConfig (Current)**:
```python
target_elements: List[str] = []      # CSS selectors to extract
exclude_elements: List[str] = []     # CSS selectors to exclude
```

**KnowledgeSourceConfig (Actual)**:
```python
allowed_subdomains: Optional[List[str]]
blocked_subdomains: Optional[List[str]]
target_elements: List[str] = []
url_patterns: Optional[List[Dict[str, Any]]]  # ⚠️ MISSING in pipeline!
```

**Gaps**:
1. ❌ **Missing `url_patterns` support** in pipeline builder
   - KnowledgeSourceConfig has `url_patterns[]` field
   - No corresponding pipeline node configuration
   - Users cannot specify URL pattern filters in pipeline builder

2. ⚠️  **Missing `exclude_elements` mapping**
   - ContentFilterNodeConfig has `exclude_elements[]`
   - KnowledgeSourceConfig doesn't have this field
   - Either add to KnowledgeSourceConfig OR remove from node config

**url_patterns Structure**:
```python
url_patterns: List[Dict[str, Any]] = [
    {
        "pattern": "https://docs.example.com/api/*",
        "match_type": "glob",  # or "regex"
        "include": True  # or False for exclusion
    }
]
```

**Required**:
- Add URL_PATTERN_FILTER node OR
- Extend DOMAIN_FILTER node to include url_patterns field

---

### 5. **INCOMPLETE: Crawl Depth Configuration** ⚠️

**WebsiteNodeConfig (Current)**:
```python
url: str
crawl_depth: int = 2  # Default: 2 levels
```

**KnowledgeSourceConfig (Actual)**:
```python
crawl_depth: Optional[int]
# 0 = exact URL only (no link following)
# 1 = URL + 1 level of links
# 2+ = deeper recursive crawling
# For single_page/multiple_pages: use 0
# For website mode: use 2+ for recursive discovery
```

**Gap**:
- ✅ Field exists in both
- ⚠️  But validation rules differ:
  - SinglePageNodeConfig should enforce `crawl_depth = 0`
  - MultiplePagesNodeConfig should enforce `crawl_depth = 0`
  - WebsiteNodeConfig allows configurable depth (1+)

**Current**: All three node types allow any crawl_depth
**Should Be**: Validation at service layer to enforce rules based on scraping mode

---

### 6. **MISSING: File Types Configuration** ❌

**Gap**: No way to specify supported file types in pipeline builder for local files mode

**Required**:
```python
LocalFilesNodeConfig:
    file_types: List[str] = ["html", "markdown", "pdf", "docx", "txt"]
    # Or specific mode selection:
    scraping_mode: ScrapingMode  # HTML_FILES, MARKDOWN_FILES, PDF_FILES, etc.
```

---

### 7. **ARCHITECTURE: Node Connection Requirements** 📋

**Current Behavior**:
- Service traverses pipeline graph to find connected nodes
- Filters only apply if connected via edges

**Example**:
```
[WEBSITE] → [DOMAIN_FILTER] → [MARKDOWN_GENERATOR] → [TEXT_SPLITTER] → [VECTOR_DATABASE]
            ↑ Connected!            ↑ Connected!

Domain filter IS applied because edge connects WEBSITE to DOMAIN_FILTER
```

vs.

```
[WEBSITE] → [MARKDOWN_GENERATOR] → [TEXT_SPLITTER] → [VECTOR_DATABASE]

[DOMAIN_FILTER]  ← Isolated node, NOT connected
                ↑ Filter NOT applied
```

**This is GOOD** but needs documentation:
- Which nodes MUST connect to which?
- What happens if required nodes are missing?
- What's the minimum viable pipeline?

**Minimum Viable Pipeline**:
```
Source Node → Output Format Node → Text Splitter → Embedding Generator → Vector Database
(required)    (required)            (required)      (required)             (required)
```

**Optional Filters** (connect between Source and Output Format):
```
Source → Domain Filter → Content Filter → URL Pattern Filter → Output Format
         (optional)       (optional)       (optional)
```

---

## Complete Alignment Proposal

### Phase 1: Add Missing Local Files Support

#### New Node Type: LOCAL_FILES

**Node Configuration**:
```python
class LocalFilesNodeConfig(NodeConfigBase):
    """Configuration for local files data source."""

    node_type: NodeType = Field(
        default=NodeType.LOCAL_FILES,
        description="Node type: local_files"
    )

    # File selection
    local_files: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of uploaded files with metadata: [{file_path, original_filename, file_type, file_size, upload_date}]"
    )

    # File type filter
    file_types: List[str] = Field(
        default_factory=lambda: ["html", "markdown", "pdf", "docx", "txt"],
        description="Supported file types to process"
    )

    # Scraping mode (which file types to prioritize)
    scraping_mode: ScrapingMode = Field(
        default=ScrapingMode.MARKDOWN_FILES,
        description="Primary file type to process: HTML_FILES, MARKDOWN_FILES, PDF_FILES, DOCX_FILES, or TXT_FILES"
    )

    # Output format for non-text files (PDF, DOCX)
    output_format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN,
        description="Convert non-text files to this format"
    )

    class Config:
        use_enum_values = True
```

**Pipeline Service Mapping**:
```python
def _extract_source_config_for_local_files(self, node: PipelineNode) -> KnowledgeSourceConfigCreate:
    """Extract source config from LOCAL_FILES node."""

    config = LocalFilesNodeConfig(**node.config)

    return KnowledgeSourceConfigCreate(
        name=node.name or "Local Files Source",
        description=f"Local files source from pipeline: {self.pipeline.name}",
        content_source_type=ContentSourceType.LOCAL_FILES,
        scraping_mode=config.scraping_mode,
        local_files=config.local_files,
        file_types=config.file_types,
        output_format=config.output_format,
        user_id=self.user_id
    )
```

**UI Requirements**:
- File upload interface in pipeline builder
- Drag & drop or file browser
- Show uploaded files list with metadata
- File type filter checkboxes
- Preview/remove files

---

### Phase 2: Add URL Pattern Filter Node

#### New Node Type: URL_PATTERN_FILTER

**Node Configuration**:
```python
class UrlPatternFilterNodeConfig(NodeConfigBase):
    """Configuration for URL pattern filtering."""

    node_type: NodeType = Field(
        default=NodeType.URL_PATTERN_FILTER,
        description="Node type: urlPatternFilter"
    )

    url_patterns: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of URL patterns to include/exclude"
    )

    # Example pattern structure:
    # {
    #   "pattern": "https://docs.example.com/api/*",
    #   "match_type": "glob",  # or "regex"
    #   "include": True  # True=whitelist, False=blacklist
    # }

    class Config:
        use_enum_values = True
```

**Pipeline Service Integration**:
```python
# In _extract_source_config():
url_pattern_filter_node = self._find_connected_node(source_node, NodeType.URL_PATTERN_FILTER)
if url_pattern_filter_node:
    url_pattern_config = UrlPatternFilterNodeConfig(**url_pattern_filter_node.config)
    source_config_data["url_patterns"] = url_pattern_config.url_patterns
```

**UI Requirements**:
- Pattern builder interface
- Pattern type selector (glob/regex)
- Include/exclude toggle
- Pattern tester (validate against sample URLs)
- Add/remove patterns

---

### Phase 3: Fix Output Format Node Issues

#### Option 1: Keep Current Approach (Recommended)

**Keep separate nodes**:
- HTML_EXTRACTOR
- MARKDOWN_GENERATOR
- LLM_MARKDOWN_GENERATOR

**But standardize configuration**:
```python
class OutputFormatNodeConfigBase(NodeConfigBase):
    """Base class for output format node configurations."""

    content_filter_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Threshold for content filtering (0.0-1.0)"
    )

class HtmlExtractorNodeConfig(OutputFormatNodeConfigBase):
    node_type: NodeType = Field(default=NodeType.HTML_EXTRACTOR)
    # Inherits content_filter_threshold

class MarkdownGeneratorNodeConfig(OutputFormatNodeConfigBase):
    node_type: NodeType = Field(default=NodeType.MARKDOWN_GENERATOR)
    # Inherits content_filter_threshold

class LlmMarkdownGeneratorNodeConfig(OutputFormatNodeConfigBase):
    node_type: NodeType = Field(default=NodeType.LLM_MARKDOWN_GENERATOR)

    llm_content_filter_id: str = Field(
        description="ID of LLM content filter configuration"
    )
    # Inherits content_filter_threshold
```

**Remove mysterious `NodeType.OUTPUT_FORMAT`** from service code (line 276) and replace with explicit checks:
```python
# BEFORE (WRONG - OUTPUT_FORMAT doesn't exist):
output_format_node = self._find_connected_node(source_node, NodeType.OUTPUT_FORMAT)

# AFTER (CORRECT - check for any output format node type):
output_format_node = self._find_connected_node_by_types(
    source_node,
    [NodeType.HTML_EXTRACTOR, NodeType.MARKDOWN_GENERATOR, NodeType.LLM_MARKDOWN_GENERATOR]
)
```

---

### Phase 4: Validate Crawl Depth by Scraping Mode

**Add validation in PipelineService**:
```python
def _validate_source_node_config(self, node: PipelineNode) -> None:
    """Validate source node configuration based on node type."""

    if node.type == NodeType.SINGLE_PAGE:
        config = SinglePageNodeConfig(**node.config)
        # Single page should not crawl links
        if hasattr(config, 'crawl_depth') and config.crawl_depth != 0:
            raise ValueError("SINGLE_PAGE mode must have crawl_depth=0 (no link following)")

    elif node.type == NodeType.MULTIPLE_PAGES:
        config = MultiplePagesNodeConfig(**node.config)
        # Multiple pages should not crawl links
        if hasattr(config, 'crawl_depth') and config.crawl_depth != 0:
            raise ValueError("MULTIPLE_PAGES mode must have crawl_depth=0 (process exact URLs only)")

    elif node.type == NodeType.WEBSITE:
        config = WebsiteNodeConfig(**node.config)
        # Website mode needs crawl depth >= 1 for recursive discovery
        if config.crawl_depth < 1:
            raise ValueError("WEBSITE mode must have crawl_depth >= 1 for recursive crawling")
```

---

### Phase 5: Fix ContentFilter exclude_elements

**Option A: Add to KnowledgeSourceConfig** (Recommended)
```python
# In knowledge_source_config.py:
class KnowledgeSourceConfig(BaseModel):
    # ... existing fields ...

    target_elements: List[str] = Field(
        default_factory=list,
        description="List of CSS selectors to extract (include)"
    )

    exclude_elements: List[str] = Field(  # ← NEW!
        default_factory=list,
        description="List of CSS selectors to exclude (remove from extraction)"
    )
```

**Option B: Remove from Pipeline Node** (If not needed)
```python
# In pipeline.py:
class ContentFilterNodeConfig(NodeConfigBase):
    target_elements: List[str] = Field(default_factory=list)
    # Remove exclude_elements if not supported
```

**Recommendation**: Add to KnowledgeSourceConfig for more flexible content filtering.

---

### Phase 6: Improve MULTIPLE_PAGES Node

**Enhanced Configuration**:
```python
class MultiplePagesNodeConfig(NodeConfigBase):
    """Configuration for multiple pages data source."""

    node_type: NodeType = Field(default=NodeType.MULTIPLE_PAGES)

    # Option 1: Direct URL input (for small lists)
    urls: List[str] = Field(
        default_factory=list,
        max_items=100,  # Limit for direct input
        description="Direct URL list (max 100 URLs)"
    )

    # Option 2: File upload (for large lists)
    file_name: Optional[str] = Field(
        default=None,
        description="Uploaded file name containing URLs"
    )

    url_source_id: Optional[str] = Field(
        default=None,
        description="ID of UrlSourceConfig (auto-created from file upload)"
    )

    # Base URL for resolving relative URLs (optional)
    base_url: Optional[str] = Field(
        default=None,
        description="Base URL for resolving relative URLs in the list"
    )

    # Validation: Either urls OR (file_name + url_source_id) must be provided
    @validator('url_source_id', always=True)
    def validate_url_source(cls, v, values):
        urls = values.get('urls', [])
        file_name = values.get('file_name')

        if not urls and not (file_name and v):
            raise ValueError("Either 'urls' or 'file_name + url_source_id' must be provided")

        if urls and file_name:
            raise ValueError("Provide either 'urls' OR 'file_name', not both")

        return v
```

---

## Summary of Required Changes

### New Node Types to Add:

1. ✅ **LOCAL_FILES** - For local file processing
2. ✅ **URL_PATTERN_FILTER** - For URL pattern filtering

### Node Configurations to Update:

3. ✅ **MultiplePagesNodeConfig** - Better file upload handling, validation
4. ✅ **ContentFilterNodeConfig** - Map exclude_elements properly
5. ✅ **Output Format Nodes** - Standardize base class, remove phantom OUTPUT_FORMAT reference

### Service Layer Updates:

6. ✅ **PipelineService._extract_source_config()** - Add LOCAL_FILES handling
7. ✅ **PipelineService._find_output_format_node()** - Fix to check multiple node types
8. ✅ **PipelineService._validate_source_node_config()** - Add crawl_depth validation
9. ✅ **PipelineService mapping** - Add url_patterns and exclude_elements support

### Domain Model Updates:

10. ✅ **KnowledgeSourceConfig** - Add exclude_elements field (optional)
11. ✅ **NodeType enum** - Add LOCAL_FILES and URL_PATTERN_FILTER
12. ✅ **Pipeline validation** - Enforce minimum viable pipeline structure

---

## Implementation Priority

### Priority 1 (Critical - Blocking Features):
1. Add LOCAL_FILES node type (enables file processing via pipeline builder)
2. Fix OUTPUT_FORMAT reference bug in service
3. Add url_patterns support (via URL_PATTERN_FILTER node or extend DOMAIN_FILTER)

### Priority 2 (Important - UX Improvements):
4. Enhance MULTIPLE_PAGES file upload handling
5. Add crawl_depth validation
6. Add exclude_elements to KnowledgeSourceConfig

### Priority 3 (Nice to Have):
7. Pipeline validation rules (minimum viable pipeline)
8. Node connection requirements documentation
9. Better error messages for invalid pipelines

---

## Testing Strategy

### Unit Tests:
- Test each new node configuration model
- Test validation logic (crawl_depth, url_source_id, etc.)
- Test pipeline service extraction for all node types

### Integration Tests:
- Create pipeline with LOCAL_FILES → verify job creation
- Create pipeline with URL_PATTERN_FILTER → verify filtering works
- Create pipeline with MULTIPLE_PAGES file upload → verify 50,000 URL limit

### E2E Tests:
- Build complete pipeline in UI → Execute → Verify results in vector DB
- Test all scraping modes: SINGLE_PAGE, MULTIPLE_PAGES, WEBSITE
- Test all local file types: HTML, MARKDOWN, PDF, DOCX, TXT

---

🎯 **Goal**: Complete alignment between Pipeline Builder and Knowledge Source Config to provide a unified, intuitive UX for all knowledge processing scenarios.
