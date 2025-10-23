# Pipeline Builder - Implementation Status

## ✅ What's Been Completed

### Backend (Fully Implemented)
- ✅ Pipeline domain models with 14 node types
- ✅ Pipeline DAO for MongoDB operations
- ✅ Pipeline Service with execution logic
- ✅ Pipeline Router with 7 REST API endpoints
- ✅ Integration with existing services (sources, jobs, splitters, collections)
- ✅ All Python code compiles successfully

### Frontend (Partially Implemented)
- ✅ Pipeline API resource with React Query hooks
- ✅ API endpoints configured
- ✅ Save/Run button integration in main page
- ✅ NodeConfigModal wrapper component
- ✅ WebsiteSourceConfig (simple, 3-field version)

---

## 🚧 What Needs to Be Built

### New Modular Node Configs (Simple popover forms)

#### 1. **DomainFilterConfig.tsx** - NEW NODE TYPE
```typescript
// 2 sections, ~4-6 fields total
- Allowed subdomains (dynamic list)
- Blocked subdomains (dynamic list)
```

#### 2. **ContentFilterConfig.tsx** - NEW NODE TYPE
```typescript
// 1 section, 1-3 fields
- Target CSS selectors (dynamic list)
```

#### 3. **OutputFormatConfig.tsx** - NEW NODE TYPE
```typescript
// 1 field
- Format selection: HTML / Markdown / LLM Markdown
```

#### 4. **TextSplitterConfig.tsx**
```typescript
// 2-3 fields
- Chunk size (slider)
- Chunk overlap (auto-calculated or manual)
```

#### 5. **EmbeddingGeneratorConfig.tsx**
```typescript
// 2-3 fields
- Provider (dropdown)
- Model (dropdown, filtered by provider)
- Batch size (optional)
```

#### 6. **VectorDatabaseConfig.tsx**
```typescript
// 2-4 fields
- Collection name
- Use existing? (toggle)
- Clear before start? (checkbox)
- Check duplicates? (checkbox)
```

#### 7. **FileExportConfig.tsx**
```typescript
// 2-3 fields
- Output format (JSON/CSV/Markdown)
- Include metadata? (checkbox)
- Consolidated file? (checkbox)
```

---

## 🔧 Backend Updates Needed

### 1. Update Domain Models

**File**: `src/domain/knowledge/pipeline.py`

Add new node types to `NodeType` enum:
```python
class NodeType(str, Enum):
    # Data Sources
    WEBSITE = "website"
    MULTIPLE_PAGES = "multiple_pages"
    SINGLE_PAGE = "single_page"
    CONFLUENCE = "confluence"

    # NEW: Filter Nodes
    DOMAIN_FILTER = "domainFilter"
    CONTENT_FILTER = "contentFilter"
    OUTPUT_FORMAT = "outputFormat"

    # Processing
    TEXT_SPLITTER = "textSplitter"

    # AI Tools
    EMBEDDING_GENERATOR = "embeddingGenerator"
    # ... rest unchanged
```

Add new config schemas:
```python
class DomainFilterNodeConfig(BaseModel):
    """Configuration for domain filter node."""
    allowed_subdomains: List[str] = Field(default_factory=list)
    blocked_subdomains: List[str] = Field(default_factory=list)

class ContentFilterNodeConfig(BaseModel):
    """Configuration for content filter node."""
    target_elements: List[str] = Field(default_factory=list)

class OutputFormatNodeConfig(BaseModel):
    """Configuration for output format node."""
    output_format: str = Field(default="markdown")
    llm_content_filter_id: Optional[str] = None
```

### 2. Update Pipeline Service

**File**: `src/services/knowledge/pipeline_service.py`

Update `_extract_source_config()` to collect configs from multiple nodes:
```python
def _extract_source_config(self, pipeline: Pipeline, user_id: str) -> KnowledgeSourceConfigCreate:
    """Extract knowledge source configuration from pipeline nodes."""

    # Find website source node
    source_node = self._find_node_by_type(pipeline, [NodeType.WEBSITE, ...])

    # Find optional filter nodes
    domain_filter = self._find_node_by_type(pipeline, NodeType.DOMAIN_FILTER)
    content_filter = self._find_node_by_type(pipeline, NodeType.CONTENT_FILTER)
    output_format = self._find_node_by_type(pipeline, NodeType.OUTPUT_FORMAT)

    # Combine configs from all nodes
    return KnowledgeSourceConfigCreate(
        name=source_node.name,
        url=source_node.config.get("url"),
        crawl_depth=source_node.config.get("crawl_depth", 4),

        # From domain filter node (if present)
        allowed_subdomains=domain_filter.config.get("allowed_subdomains", []) if domain_filter else [],
        blocked_subdomains=domain_filter.config.get("blocked_subdomains", []) if domain_filter else [],

        # From content filter node (if present)
        target_elements=content_filter.config.get("target_elements", []) if content_filter else [],

        # From output format node (if present)
        output_format=OutputFormat(output_format.config.get("output_format", "markdown")) if output_format else OutputFormat.MARKDOWN,

        ...
    )
```

### 3. Update Connection Rules

**File**: `src/services/knowledge/pipeline_service.py`

Add validation for new node connections:
```python
VALID_CONNECTIONS = {
    NodeType.WEBSITE: [NodeType.DOMAIN_FILTER, NodeType.CONTENT_FILTER, NodeType.OUTPUT_FORMAT, NodeType.TEXT_SPLITTER],
    NodeType.DOMAIN_FILTER: [NodeType.CONTENT_FILTER, NodeType.OUTPUT_FORMAT, NodeType.TEXT_SPLITTER],
    NodeType.CONTENT_FILTER: [NodeType.OUTPUT_FORMAT, NodeType.TEXT_SPLITTER],
    NodeType.OUTPUT_FORMAT: [NodeType.TEXT_SPLITTER],
    NodeType.TEXT_SPLITTER: [NodeType.EMBEDDING_GENERATOR],
    NodeType.EMBEDDING_GENERATOR: [NodeType.VECTOR_DATABASE, NodeType.FILE_EXPORT],
    NodeType.VECTOR_DATABASE: [NodeType.FILE_EXPORT, NodeType.REPORT_GENERATOR],
}
```

---

## 🎨 Frontend Updates Needed

### 1. Update Pipeline Types

**File**: `dashboard/src/api/resources/pipelines.ts`

Add new node types to schema:
```typescript
export const NodeTypeSchema = z.enum([
  // Data Sources
  'website',
  'multiple_pages',
  'single_page',
  'confluence',

  // NEW: Filter Nodes
  'domainFilter',
  'contentFilter',
  'outputFormat',

  // Processing
  'textSplitter',

  // AI Tools
  'embeddingGenerator',
  // ... rest
]);
```

### 2. Update Toolbox

**File**: `dashboard/src/pages/dashboard/management/pipeline-builder/components/Toolbox.tsx`

Add new node types to toolbox:
```typescript
const nodeTypes = [
  {
    category: 'Data Sources',
    nodes: [
      { type: 'website', label: 'Website', icon: '📄' },
      { type: 'multiple_pages', label: 'Multiple Pages', icon: '📚' },
      { type: 'single_page', label: 'Single Page', icon: '📝' },
    ],
  },
  {
    category: 'Filters & Transforms',  // NEW CATEGORY
    nodes: [
      { type: 'domainFilter', label: 'Domain Filter', icon: '🔍' },
      { type: 'contentFilter', label: 'Content Filter', icon: '📋' },
      { type: 'outputFormat', label: 'Output Format', icon: '⚙️' },
    ],
  },
  {
    category: 'Processing',
    nodes: [
      { type: 'textSplitter', label: 'Text Splitter', icon: '✂️' },
    ],
  },
  // ... rest
];
```

### 3. Update NodeConfigModal

**File**: `dashboard/src/pages/dashboard/management/pipeline-builder/components/NodeConfigModal.tsx`

Add cases for new node types:
```typescript
const renderNodeConfig = () => {
  switch (node.type) {
    case 'website':
    case 'multiple_pages':
    case 'single_page':
      return <WebsiteSourceConfig node={node} onSave={onSave} onClose={onClose} />;

    // NEW NODE TYPES
    case 'domainFilter':
      return <DomainFilterConfig node={node} onSave={onSave} onClose={onClose} />;

    case 'contentFilter':
      return <ContentFilterConfig node={node} onSave={onSave} onClose={onClose} />;

    case 'outputFormat':
      return <OutputFormatConfig node={node} onSave={onSave} onClose={onClose} />;

    case 'textSplitter':
      return <TextSplitterConfig node={node} onSave={onSave} onClose={onClose} />;

    // ... rest
  }
};
```

### 4. Update Connection Validation

**File**: `dashboard/src/pages/dashboard/management/pipeline-builder/utils/pipelineRules.ts`

Add validation rules for new nodes:
```typescript
export const connectionRules = [
  // Website Source can connect to filters or directly to splitter
  { source: 'website', target: 'domainFilter', valid: true },
  { source: 'website', target: 'contentFilter', valid: true },
  { source: 'website', target: 'outputFormat', valid: true },
  { source: 'website', target: 'textSplitter', valid: true },

  // Domain Filter can connect to content filter or output format
  { source: 'domainFilter', target: 'contentFilter', valid: true },
  { source: 'domainFilter', target: 'outputFormat', valid: true },
  { source: 'domainFilter', target: 'textSplitter', valid: true },

  // Content Filter can connect to output format or splitter
  { source: 'contentFilter', target: 'outputFormat', valid: true },
  { source: 'contentFilter', target: 'textSplitter', valid: true },

  // Output Format connects to splitter
  { source: 'outputFormat', target: 'textSplitter', valid: true },

  // Rest of the rules remain the same...
];
```

---

## 📋 Implementation Checklist

### Week 1: Core Modular Nodes
- [x] Website Source Config (simple version) ✅
- [ ] Domain Filter Config
- [ ] Content Filter Config
- [ ] Output Format Config
- [ ] Update backend domain models
- [ ] Update backend service to handle multiple nodes

### Week 2: Processing Nodes
- [ ] Text Splitter Config
- [ ] Embedding Generator Config
- [ ] Vector Database Config
- [ ] File Export Config
- [ ] Update connection validation (backend)
- [ ] Update connection validation (frontend)

### Week 3: Integration & Polish
- [ ] Test full pipeline flow
- [ ] Add visual feedback for connections
- [ ] Add pipeline templates
- [ ] Error handling & recovery
- [ ] Documentation

---

## 🎯 Example Pipeline Flow

### User creates this pipeline:
```
[Website Source] → [Domain Filter] → [Content Filter] → [Output Format]
                                                              ↓
                                                       [Text Splitter]
                                                              ↓
                                                    [Embedding Generator]
                                                              ↓
                                                      [Vector Database]
```

### Backend combines configs and creates:
1. **KnowledgeSource** with:
   - URL from Website Source
   - Allowed/blocked subdomains from Domain Filter
   - Target elements from Content Filter
   - Output format from Output Format node

2. **DocumentSplitter** from Text Splitter node

3. **VectorDBCollection** from Vector Database node

4. **KnowledgeJob** linking everything

5. **Execute job** via RabbitMQ

---

## 🚀 Quick Start (Next Steps)

### Option A: Build remaining node configs first (Frontend-focused)
1. Create DomainFilterConfig.tsx
2. Create ContentFilterConfig.tsx
3. Create OutputFormatConfig.tsx
4. Create TextSplitterConfig.tsx
5. Create EmbeddingGeneratorConfig.tsx
6. Create VectorDatabaseConfig.tsx
7. Update toolbox with new node types
8. Update NodeConfigModal to handle new types

### Option B: Update backend first (Backend-focused)
1. Update NodeType enum with new types
2. Add new config schemas
3. Update pipeline service extraction logic
4. Add connection validation
5. Test backend with mock data
6. Then build frontend configs

### Recommended: Hybrid Approach
1. **Day 1**: Update backend models + Add 1 new node config (DomainFilter)
2. **Day 2**: Test end-to-end with DomainFilter node
3. **Day 3-4**: Add remaining filter nodes (Content, Output)
4. **Day 5**: Add processing nodes (Splitter, Embedding, VectorDB)
5. **Week 2**: Polish, templates, validation

---

## 📊 Progress Summary

| Component | Status | Progress |
|-----------|--------|----------|
| Backend Models | 🟡 Partial | 70% (needs new node types) |
| Backend Service | 🟡 Partial | 60% (needs multi-node extraction) |
| Backend API | ✅ Complete | 100% |
| Frontend API | ✅ Complete | 100% |
| Node Configs | 🟡 Partial | 14% (1/7 done) |
| Toolbox | 🔴 Needs Update | 0% |
| Validation | 🔴 Needs Update | 0% |
| Testing | 🔴 Not Started | 0% |

**Overall Progress**: ~40%

---

## 💡 Key Decisions Made

1. ✅ **Modular nodes** instead of one big wizard
2. ✅ **Simple configs** (2-4 fields per node)
3. ✅ **Separate filter nodes** (Domain, Content, Output)
4. ✅ **Modal popovers** instead of full-page wizards
5. ✅ **Backend combines** configs from multiple nodes

---

## 🎉 What This Achieves

### User Benefits
- **Faster**: 30 seconds vs 10 minutes
- **Simpler**: 2-3 fields per node vs 20+ fields
- **Visual**: See data flow at a glance
- **Flexible**: Skip nodes you don't need
- **Modular**: Reuse components across pipelines

### Developer Benefits
- **Maintainable**: Each node = one file, one concern
- **Testable**: Test nodes independently
- **Extensible**: Easy to add new node types
- **Consistent**: Same patterns everywhere

---

**Ready to continue building? Let's tackle the remaining node configs!** 🚀

Next file to create: `DomainFilterConfig.tsx`
