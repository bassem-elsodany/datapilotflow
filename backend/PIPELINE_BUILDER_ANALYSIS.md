# Pipeline Builder Frontend Implementation Analysis

## Overview
The Pipeline Builder is a visual, drag-and-drop React application for constructing RAG (Retrieval-Augmented Generation) data processing pipelines. It's built on React Flow and Mantine UI, accessible at `http://localhost:5173/dashboard/management/pipeline-builder`.

---

## 1. KEY FILE LOCATIONS

### Core Implementation Files
- **Main Page Component**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/pipeline-builder/index.tsx`
- **Canvas Component**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/pipeline-builder/components/Canvas.tsx`
- **Custom Hook**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/pipeline-builder/hooks/usePipelineBuilder.ts`

### UI Components
- **Node Editor (Config Form)**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/pipeline-builder/components/NodeEditor.tsx`
- **Toolbox (Draggable Tools)**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/pipeline-builder/components/Toolbox.tsx`
- **Node Component**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/pipeline-builder/components/PipelineNode.tsx`
- **Pipeline Validator**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/pipeline-builder/components/PipelineValidator.tsx`
- **Pipeline Runner**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/pipeline-builder/components/PipelineRunner.tsx`

### Edge Components
- **Arrow Edge**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/pipeline-builder/components/ArrowEdge.tsx`
- **Pipeline Edge**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/pipeline-builder/components/PipelineEdge.tsx`

### Business Logic
- **Pipeline Rules**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/pipeline-builder/utils/pipelineRules.ts`

---

## 2. DRAG-AND-DROP LIBRARY

**Library Used**: **React Flow** (v11.11.4)
- Official site: https://reactflow.dev/
- Provides: Node-based editor, canvas management, automatic layouts
- Custom components: PipelineNode, ArrowEdge

**Interaction Methods**:
1. **Drag from Toolbox**: Items dragged to canvas trigger `onDrop` event
2. **Click to Add**: Clicking toolbox items adds nodes to canvas center
3. **Auto-connection**: Nodes automatically connect based on pipeline rules
4. **Manual Deletion**: Hover delete button on nodes, or select + Delete key

---

## 3. PIPELINE STRUCTURE & DATA MODEL

### Node Data Structure
```typescript
interface PipelineNodeData {
  id: string;                    // UUID
  name: string;                  // User-friendly name
  type: string;                  // Node type (see types below)
  status: 'pending' | 'running' | 'completed' | 'failed';
  description?: string;
  configured?: boolean;          // Indicates if node has been configured
  [key: string]: any;            // Type-specific config
}
```

### Edge Structure
```typescript
interface Edge {
  id: string;                    // e.g., "edge-source-id-target-id"
  source: string;                // Source node ID
  target: string;                // Target node ID
  type: 'arrow';                 // Edge type
  animated: boolean;             // Visual animation
  style: { stroke: string; strokeWidth: number };
}
```

### Pipeline Export Structure
```typescript
{
  nodes: [
    {
      id: string;
      type: 'pipelineNode';
      position: { x: number; y: number };
      data: PipelineNodeData;
    }
  ],
  edges: [
    {
      id: string;
      source: string;
      target: string;
      type: string;
    }
  ]
}
```

---

## 4. AVAILABLE NODE TYPES

### Category 1: DATA SOURCES (Max 1 per pipeline)
- **website**: Website Crawling
- **multiple_pages**: Links File (CSV/TXT with URLs)
- **single_page**: Single Page
- **confluence**: Confluence Space Crawler

### Category 2: PROCESSING TOOLS
- **textSplitter**: Document Splitter (chunks text into processable units)

### Category 3: AI TOOLS
- **embeddingGenerator**: Embedding Generator (converts text to vectors)
- **textSummarizer**: Text Summarizer
- **contentClassifier**: Content Classifier
- **contentEnricher**: Content Enricher
- **translation**: Translation

### Category 4: STORAGE & OUTPUT
- **vectorDatabase**: Vector Database (stores embeddings)
- **fileExport**: File Export
- **reportGenerator**: Report Generator
- **analytics**: Analytics
- **notification**: Notification

---

## 5. NODE-SPECIFIC CONFIGURATIONS

### Data Source Nodes (website, multiple_pages, single_page, confluence)
```typescript
{
  scraping_mode: 'website' | 'multiple_pages' | 'single_page' | 'confluence';
  url?: string;                          // Required except for multiple_pages
  allowed_subdomains: string[];          // Whitelist subdomains
  blocked_subdomains: string[];          // Blacklist subdomains
  url_patterns: string[];                // Regex patterns
  crawl_depth: number;                   // 1-10, default 4
  css_selector: string;                  // CSS selector for content
  css_selector_parts: {                  // Hierarchical selectors
    type: string;
    selector: string;
  }[];
  content_filter_threshold: number;      // 0-1, default 0.6
}
```

### Text Splitter Node
```typescript
{
  chunk_size: number;                    // Tokens, default 1000, range 64-4096
  chunk_overlap: number;                 // Tokens, default 200, range 0-512
  batch_size: number;                    // Documents per batch, default 100
}
```

---

## 6. PIPELINE VALIDATION RULES

### Connection Rules
The system validates connections between node types:
- Data Sources → Document Splitter (mandatory)
- Document Splitter → AI Tools
- AI Tools → Storage & Output
- AI Tools → AI Tools (chaining allowed)
- Storage & Output → Storage & Output

### Required Nodes
1. **At least one Data Source**: (website, multiple_pages, single_page, or confluence)
2. **Document Splitter**: Required after data source
3. **Embedding Generator**: Required for RAG functionality
4. **Vector Database**: Required to store embeddings

### Validation Result Structure
```typescript
interface PipelineValidationResult {
  isValid: boolean;
  errors: string[];              // Critical issues
  warnings: string[];            // Non-critical issues (orphaned nodes)
  suggestions: string[];         // Recommended additions
}
```

---

## 7. CONFIGURATION FORMS (NODE EDITOR)

### Structure: Multi-Step Stepper

**For Data Source Nodes** (4 steps):
1. **Basic Info**: Node name, description
2. **Scraping Config**: URL, crawl depth, content filter threshold
3. **Domain Filtering**: Allowed/blocked subdomains, URL patterns
4. **Review**: Summary of all settings

**For Text Splitter Node** (3 steps):
1. **Basic Info**: Node name, description
2. **Splitter Config**: Chunk size, overlap, batch size
3. **Review**: Summary of settings

### Form Validation
- Required fields: name, description
- Conditional validation: URL required except for multiple_pages mode
- Range validation: crawl_depth (1-10), threshold (0-1), etc.

### Configuration Persistence
Configuration is saved to node's data object when "Apply Changes" is clicked. The node status changes to "configured" with a green checkmark indicator.

---

## 8. AUTO-CONNECTION LOGIC

When a new node is added:
1. System checks `PIPELINE_CONNECTION_RULES` to find valid connections
2. For each existing node, checks if new node can connect:
   - **Forward connection**: new → existing
   - **Backward connection**: existing → new
3. Creates animated blue edges automatically
4. Multiple connections possible to support chaining

**Key Functions**:
- `getValidTargets(nodeType)`: Returns node types this can connect to
- `getValidSources(nodeType)`: Returns node types that can connect to this
- `validateConnection(fromType, toType)`: Boolean validation

---

## 9. API INTEGRATION STATUS

### CURRENT STATUS: NOT FULLY IMPLEMENTED

#### What's Ready:
1. **savePipeline() hook**: Collects nodes and edges into structured format
   ```typescript
   const pipeline = {
     nodes: nodes.map(node => ({ id, type, position, data })),
     edges: edges.map(edge => ({ id, source, target, type }))
   }
   ```
2. **loadPipeline() hook**: Can restore pipeline from saved structure
3. **Data structure**: Well-defined and ready to send

#### What's TODO:
1. **Save Button**: Currently logs to console, no API call
   - Location: `handleSavePipeline()` in index.tsx (line 140-143)
   - TODO comment: `// TODO: Implement save logic`
   
2. **Run Button**: Currently toggles state, no backend execution
   - Location: `handleRunPipeline()` in index.tsx (line 145-149)
   - TODO comment: `// TODO: Implement run logic`

3. **No API Endpoint Defined**: Backend has no pipeline save/run endpoints yet
4. **No axios Integration**: No API resource created for pipeline operations
5. **Mock Data**: PipelineRunner uses mock logs and statistics

---

## 10. DATA BEING SENT (READY TO SEND)

### Pipeline Save Payload
```typescript
{
  nodes: [
    {
      id: "uuid-1",
      type: "pipelineNode",
      position: { x: 100, y: 200 },
      data: {
        id: "uuid-1",
        name: "Website Crawling",
        type: "website",
        status: "completed",
        description: "Crawl and scrape content from websites",
        configured: true,
        scraping_mode: "website",
        url: "https://example.com",
        allowed_subdomains: [],
        blocked_subdomains: [],
        url_patterns: [],
        crawl_depth: 4,
        css_selector: "main > article",
        css_selector_parts: [
          { type: "main", selector: "" },
          { type: "article", selector: "" }
        ],
        content_filter_threshold: 0.6
      }
    },
    {
      id: "uuid-2",
      type: "pipelineNode",
      position: { x: 300, y: 200 },
      data: {
        id: "uuid-2",
        name: "Document Splitter",
        type: "textSplitter",
        status: "pending",
        description: "Split documents into chunks for processing",
        configured: false,
        chunk_size: 1000,
        chunk_overlap: 200,
        batch_size: 100
      }
    }
  ],
  edges: [
    {
      id: "edge-uuid-1-uuid-2",
      source: "uuid-1",
      target: "uuid-2",
      type: "arrow",
      animated: true,
      style: { stroke: "#228be6", strokeWidth: 2 }
    }
  ]
}
```

---

## 11. COMPONENT INTERACTION FLOW

```
PipelineBuilderPage (Main Container)
├── DraggableToolbox (Floating)
│   └── Toolbox (Tool Categories)
│       └── onDragStart (sets data transfer)
│
├── Canvas (React Flow)
│   ├── onDrop (from Toolbox)
│   ├── onNodeClick (select node)
│   ├── onNodeDoubleClick (open editor)
│   ├── PipelineNode (custom node render)
│   └── ArrowEdge (custom edge render)
│
├── PipelineValidator
│   └── validatePipeline() [from utils]
│
├── PipelineRunner (Status & Logs)
│
└── NodeEditor (Bottom Panel - Fixed Position)
    ├── Stepper (Multi-step form)
    ├── useForm (Mantine form hooks)
    └── updateNode (persist config)

usePipelineBuilder Hook
├── useNodesState (React Flow)
├── useEdgesState (React Flow)
├── addNode (auto-connect logic)
├── updateNode (config persistence)
├── deleteNode (cleanup edges)
├── savePipeline (export to structure)
├── loadPipeline (import from structure)
└── validateCurrentPipeline (validate rules)
```

---

## 12. IMPLEMENTATION GAPS & NEXT STEPS

### Missing Features (Frontend)
1. [ ] API endpoint integration for saving pipeline
2. [ ] API endpoint integration for running pipeline
3. [ ] Persisting pipelines to backend database
4. [ ] Loading saved pipelines from backend
5. [ ] Real-time execution status updates (WebSocket?)
6. [ ] Real log streaming from backend
7. [ ] Error handling and retry logic
8. [ ] Pipeline versioning/history
9. [ ] Pipeline templates/presets
10. [ ] Undo/Redo functionality

### Missing Components (Backend)
1. [ ] Pipeline model/schema in database
2. [ ] POST /api/pipelines (create/save)
3. [ ] GET /api/pipelines (list)
4. [ ] GET /api/pipelines/:id (load)
5. [ ] PUT /api/pipelines/:id (update)
6. [ ] DELETE /api/pipelines/:id (delete)
7. [ ] POST /api/pipelines/:id/run (execute)
8. [ ] WebSocket endpoint for execution logs
9. [ ] Validation of pipeline structure
10. [ ] Actual node execution logic

---

## 13. TECHNICAL STACK

### Frontend
- **React**: 19.0.0
- **React Flow**: 11.11.4 (node editor)
- **Mantine UI**: 7.17.8 (component library)
- **React Router**: 7.3.0 (navigation)
- **React Query**: 5.90.2 (data fetching)
- **Axios**: 1.8.2 (HTTP client)
- **Zod**: 3.24.2 (schema validation)
- **TypeScript**: 5.8.2

### Key Libraries
- `@mantine/form`: Form state management
- `@mantine/hooks`: useForm, useDisclosure, etc.
- `@tabler/icons-react`: Icons
- `react-icons`: Additional icon libraries
- `cuid2`: ID generation (if needed)

---

## 14. UI/UX FEATURES

### Canvas
- 600px height, full width
- MiniMap (bottom-left) for navigation
- Controls (zoom, center, fit)
- Dot background pattern
- Floating toolbox (draggable)

### Nodes
- 32px circular nodes with icons
- Status indicator (colored dot, top-right)
- Node label + type below
- Hover delete button
- Selection highlight (blue border)
- Color-coded status: pending (gray), running (blue), completed (green), failed (red)

### Edges
- Blue curved edges with arrows
- Animated when active
- Smooth step paths

### Forms
- Teal/green color scheme (#45c9bb primary)
- Multi-step stepper with horizontal layout
- Responsive grid layout for inputs
- Dynamic field visibility based on node type

### Validation Display
- Alert boxes for errors (red), warnings (yellow), suggestions (blue), success (green)
- Real-time validation as nodes are added
- Pipeline flow guidance

---

## 15. ENTRY POINTS FOR IMPLEMENTATION

### 1. Save Pipeline
**File**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/pipeline-builder/index.tsx:140-143`

Replace:
```typescript
const handleSavePipeline = useCallback(() => {
  console.log('Saving pipeline:', { nodes, edges });
  // TODO: Implement save logic
}, [nodes, edges]);
```

With API call using `usePipelineBuilder()` hook's `savePipeline()` function.

### 2. Run Pipeline
**File**: Same file, line 145-149

Implement WebSocket connection or polling for real-time execution status.

### 3. Create API Resource
**File**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/api/resources/`

Create `pipelines.ts` with methods:
- `createPipeline(data)`
- `getPipelines()`
- `getPipeline(id)`
- `updatePipeline(id, data)`
- `deletePipeline(id)`
- `runPipeline(id)`

---

## 16. TESTING RECOMMENDATIONS

1. **Unit Tests**: Pipeline validation rules
2. **Integration Tests**: Node add/remove/configure flow
3. **E2E Tests**: Full pipeline creation and save
4. **Validation Tests**: Invalid connections are prevented
5. **Performance**: Canvas performance with 20+ nodes

---

## Summary

The Pipeline Builder is a well-structured, feature-rich visual editor for RAG pipeline construction with:
- **Strong Frontend**: Complete UI/UX with validation and multi-step configuration
- **Auto-Connection Logic**: Intelligent node connection based on pipeline rules
- **Data Structure Ready**: Nodes and edges ready to send to backend
- **Missing Backend**: No persistence or execution endpoints implemented

The system is ready for backend API integration. The data structures are well-defined and the frontend can immediately accept API endpoints for save/load/run operations.
