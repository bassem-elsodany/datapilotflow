# Pipeline Builder - Workflow & Component Architecture

## User Workflow

```
1. USER OPENS PIPELINE BUILDER
   ↓
2. DRAG NODE FROM TOOLBOX (or click to add)
   ├─ Node added to canvas at drop position
   ├─ Auto-connection logic triggered
   ├─ Validation rules checked
   └─ Node appears with pending status
   ↓
3. DOUBLE-CLICK NODE (or select + configure)
   ├─ NodeEditor opens at bottom
   ├─ Multi-step stepper form appears
   ├─ User fills in configuration
   └─ "Apply Changes" clicked
   ↓
4. NODE CONFIGURED
   ├─ Data persisted to node.data object
   ├─ Node status changes to "configured"
   ├─ Green checkmark appears on node
   └─ Validation runs again
   ↓
5. REPEAT FOR EACH NODE (typically 4-8 nodes)
   ↓
6. CLICK "SAVE" BUTTON
   ├─ Pipeline structure collected
   ├─ API call to /api/pipelines (NOT YET IMPLEMENTED)
   ├─ Backend persists to database
   └─ User feedback (success/error)
   ↓
7. CLICK "RUN" BUTTON (optional)
   ├─ Pipeline sent to backend
   ├─ Backend executes nodes sequentially
   ├─ Logs streamed back (WebSocket or polling)
   ├─ Real-time status updates
   └─ Final results shown
   ↓
8. REPEAT or RESET
```

---

## Component Hierarchy

```
PipelineBuilderPage (index.tsx)
│
├── PAGE HEADER & CONTROLS
│   └── Save | Run | Reset buttons
│
├── MAIN CONTENT (Container)
│   │
│   ├── CANVAS SECTION
│   │   ├── DraggableToolbox (floating)
│   │   │   └── Toolbox
│   │   │       ├── Category Groups (expandable)
│   │   │       │   └── Tool Items (draggable)
│   │   │       └── Search Filter
│   │   │
│   │   └── CanvasWrapper (React Flow)
│   │       ├── ReactFlow (core library)
│   │       ├── Controls (zoom, center)
│   │       ├── MiniMap (preview)
│   │       ├── Background (dots pattern)
│   │       ├── PipelineNode components (rendered)
│   │       └── ArrowEdge components (rendered)
│   │
│   ├── VALIDATION SECTION
│   │   └── PipelineValidator
│   │       ├── Errors (red)
│   │       ├── Warnings (yellow)
│   │       ├── Suggestions (blue)
│   │       └── Success message (green)
│   │
│   └── PIPELINE STATUS SECTION
│       └── PipelineRunner
│           ├── Statistics (progress, time, counts)
│           ├── Progress bar
│           └── Execution logs (scrollable)
│
└── BOTTOM PANEL (NodeEditor - when expanded)
    ├── Header (node name, type, status)
    ├── Expand/collapse toggle
    ├── Close button
    │
    ├── Stepper (multi-step form)
    │   ├── Step 1: Basic Info
    │   ├── Step 2: Type-specific Config
    │   ├── Step 3: Optional (domain filtering)
    │   └── Step 4: Review
    │
    ├── Form Fields (rendered conditionally)
    │   ├── TextInput
    │   ├── Textarea
    │   ├── NumberInput
    │   └── Dynamic arrays
    │
    └── Action Buttons
        ├── Previous
        ├── Next (or Apply if last step)
        └── Apply Changes
```

---

## State Management Flow

```
usePipelineBuilder Hook
│
├── NODES STATE (React Flow)
│   ├── setNodes(currentNodes)
│   ├── onNodesChange(changes)      <- from React Flow
│   └── selectedNode                <- currently selected node
│
├── EDGES STATE (React Flow)
│   ├── setEdges(currentEdges)
│   └── onEdgesChange(changes)      <- from React Flow
│
├── NODE OPERATIONS
│   ├── addNode(type, position)
│   │   ├─ Generate UUID
│   │   ├─ Create default config
│   │   ├─ Auto-connect to existing
│   │   └─ Update nodes array
│   │
│   ├── updateNode(id, data)
│   │   ├─ Find node by id
│   │   ├─ Merge new data
│   │   ├─ Update nodes array
│   │   └─ Update selectedNode
│   │
│   └── deleteNode(id)
│       ├─ Remove node
│       ├─ Remove connected edges
│       ├─ Clear selection
│       └─ Update arrays
│
├── SELECTION
│   ├── handleNodeSelect(node)      <- click on node
│   └── setSelectedNode(node)
│
├── PERSISTENCE
│   ├── savePipeline() -> Pipeline object
│   ├── loadPipeline(pipeline) -> restore state
│   └── clearCanvas()
│
└── VALIDATION
    └── validateCurrentPipeline() -> ValidationResult
```

---

## Data Flow: Drag & Drop

```
1. TOOLBOX DRAG START (Toolbox.tsx)
   │
   ├─ onDragStart event fired
   ├─ event.dataTransfer.setData('application/reactflow', nodeType)
   └─ cursor becomes 'grab'
   
2. CANVAS DRAG OVER (Canvas.tsx)
   │
   ├─ onDragOver event prevents default
   ├─ event.dataTransfer.dropEffect = 'move'
   ├─ Canvas background changes to light blue
   └─ cursor becomes 'move'
   
3. CANVAS DROP (Canvas.tsx)
   │
   ├─ onDrop event fired
   ├─ Extract nodeType from dataTransfer
   ├─ Calculate drop position relative to canvas
   ├─ Call onNodesChange([{ type: 'add', item: newNode }])
   │
   └─ IN COMPONENT (through props)
       │
       ├─ addNode(type, position) from usePipelineBuilder
       │
       ├─ setNodes(currentNodes => {
       │   ├─ Check for duplicate data sources
       │   ├─ Create nodeId (UUID)
       │   ├─ Smart positioning logic
       │   ├─ Set default configuration
       │   ├─ Create newNode object
       │   ├─ autoConnectNode(newNode, allNodes)
       │   └─ return [...currentNodes, newNode]
       │ })
       │
       └─ autoConnectNode(newNode, allNodes)
           ├─ getValidTargets(newNode.type)
           ├─ getValidSources(newNode.type)
           ├─ For each existing node:
           │   ├─ Check forward connection (new -> existing)
           │   ├─ Check backward connection (existing -> new)
           │   └─ Create edge if valid
           └─ setEdges(eds => [...eds, ...newEdges])

4. CANVAS UPDATED
   │
   ├─ React Flow re-renders
   ├─ New node appears at drop position
   ├─ New edges appear animated
   ├─ Validation re-runs
   └─ UI updates with new status
```

---

## Data Flow: Configuration Save

```
1. USER DOUBLE-CLICKS NODE
   │
   ├─ PipelineNode.tsx detects double-click
   ├─ onNodeDoubleClick fired in Canvas
   ├─ handleNodeConfigure called
   ├─ handleNodeSelect(node) called
   ├─ setNodeEditorOpened(true)
   └─ NodeEditor mounts at bottom
   
2. NODE EDITOR OPENS
   │
   ├─ useForm initializes with node.data values
   ├─ Multi-step stepper displayed
   ├─ User fills in form fields
   └─ Form state tracked in React state
   
3. USER CLICKS "APPLY CHANGES"
   │
   ├─ form.values contains all user input
   ├─ handleSubmit callback triggered
   │
   └─ updateNode(node.id, {
       ├─ ...formData          (all form values)
       ├─ status: 'completed'  (mark as done)
       ├─ configured: true     (set flag)
       └─ })
   
4. UPDATE APPLIED
   │
   ├─ setNodes updates node in array
   ├─ node.data now contains new config
   ├─ selectedNode updated
   ├─ UI re-renders
   │
   └─ NODE EDITOR CLOSES
       ├─ onClose() called
       ├─ setNodeEditorOpened(false)
       └─ Bottom panel disappears
   
5. VALIDATION RUNS
   │
   ├─ validateCurrentPipeline() called
   ├─ Checks all nodes against rules
   ├─ Updates validation UI
   └─ Shows errors/warnings/suggestions
```

---

## Connection Rules Engine

```
validatePipeline(nodes, edges)
│
├─ CHECK REQUIRED NODES
│  ├─ At least 1 data source?
│  │  └─ Filter: website|multiple_pages|single_page|confluence
│  │     ├─ YES → continue
│  │     └─ NO → error: "Must have data source"
│  │
│  ├─ Text splitter exists?
│  │  └─ Filter: textSplitter
│  │     ├─ YES → continue
│  │     └─ NO → error: "Must have splitter"
│  │
│  ├─ Embedding generator exists?
│  │  └─ Filter: embeddingGenerator
│  │     ├─ YES → continue
│  │     └─ NO → error: "Must have embeddings"
│  │
│  └─ Vector database exists?
│     └─ Filter: vectorDatabase
│        ├─ YES → continue
│        └─ NO → error: "Must have vector DB"
│
├─ VALIDATE CONNECTIONS
│  └─ For each edge:
│     ├─ Get source node type
│     ├─ Get target node type
│     ├─ validateConnection(source, target)
│     │  └─ Check PIPELINE_CONNECTION_RULES
│     ├─ YES → continue
│     └─ NO → error: "Invalid connection"
│
├─ CHECK ORPHANED NODES
│  ├─ Collect all connected node IDs from edges
│  ├─ Find nodes not in connected set
│  ├─ If found → warning: "N disconnected nodes"
│  └─ Continue anyway (allow intentional)
│
└─ RETURN ValidationResult
   ├─ isValid: boolean
   ├─ errors: string[]
   ├─ warnings: string[]
   └─ suggestions: string[]
```

---

## Connection Rules Matrix

```
FROM / TO          website  mult-pg  single_pg  confluence  textSplitter  
─────────────────────────────────────────────────────────────────────────
website              ✗        ✗        ✗         ✗           ✓
multiple_pages       ✗        ✗        ✗         ✗           ✓
single_page          ✗        ✗        ✗         ✗           ✓
confluence           ✗        ✗        ✗         ✗           ✓


FROM / TO          embed   summarizer  classifier  enricher  translation
─────────────────────────────────────────────────────────────────────────
textSplitter        ✓         ✓           ✓          ✓          ✓


FROM / TO          vectorDB  fileExport  report  analytics  notification
────────────────────────────────────────────────────────────────────────
embeddingGen        ✓         ✗           ✗       ✗          ✗
summarizer          ✗         ✓           ✗       ✗          ✗
classifier          ✗         ✓           ✗       ✗          ✗
enricher            ✗         ✓           ✗       ✗          ✗
translation         ✗         ✓           ✗       ✗          ✗


AI TOOLS (chaining)
── All AI tools can connect to ALL other AI tools ──
✓ = allowed, ✗ = not allowed
```

---

## Node Configuration Schemas

### Website Crawler
```
Step 1: Basic Info
├─ name (required, string)
└─ description (required, string)

Step 2: Scraping Config
├─ url (required, URL format)
├─ crawl_depth (1-10, default 4)
└─ content_filter_threshold (0-1, default 0.6)

Step 3: Domain Filtering
├─ allowed_subdomains (array of strings)
├─ blocked_subdomains (array of strings)
└─ url_patterns (array of regex strings)

Step 4: Review
└─ Display all settings
```

### Text Splitter
```
Step 1: Basic Info
├─ name (required)
└─ description (required)

Step 2: Splitter Config
├─ chunk_size (64-4096, default 1000)
├─ chunk_overlap (0-512, default 200)
└─ batch_size (1-1000, default 100)

Step 3: Review
└─ Display all settings
```

---

## API Integration Points (TODO)

### 1. Save Pipeline
```
Location: index.tsx:140-143
Current: console.log()
Needed: 
  const pipeline = savePipeline();
  const response = await api.post('/api/pipelines', {
    name: 'Pipeline Name',
    description: 'Description',
    nodes: pipeline.nodes,
    edges: pipeline.edges
  });
```

### 2. Run Pipeline
```
Location: index.tsx:145-149
Current: toggle boolean
Needed:
  const pipeline = savePipeline();
  const response = await api.post(`/api/pipelines/${id}/run`, {
    nodes: pipeline.nodes,
    edges: pipeline.edges
  });
  // Then stream logs via WebSocket
  wsConnect(`/ws/pipelines/${response.id}/logs`);
```

### 3. API Resource File
```
Location: /src/api/resources/pipelines.ts (DOESN'T EXIST)
Needed:
  export async function createPipeline(data) { ... }
  export async function getPipelines() { ... }
  export async function getPipeline(id) { ... }
  export async function runPipeline(id, data) { ... }
  export async function getPipelineStatus(id) { ... }
```

---

## Error Handling Flow

```
TRY SAVE
├─ Validate locally (frontend)
├─ All nodes configured?
├─ Pipeline valid?
│
├─ YES
│  ├─ API call POST /api/pipelines
│  │
│  ├─ SUCCESS (200)
│  │  ├─ Show success notification
│  │  ├─ Save pipeline ID
│  │  └─ Optionally redirect to view
│  │
│  └─ ERROR (4xx/5xx)
│     ├─ Show error notification
│     ├─ Log error details
│     └─ Suggest retry
│
└─ NO
   ├─ Show validation errors
   ├─ Highlight problematic nodes
   └─ Prevent API call
```

---

## Performance Considerations

```
Operation              Complexity    Max Nodes    Impact
─────────────────────────────────────────────────────────
Add Node              O(n)          100s         OK
Auto-connect          O(n²)         20           Good
Validate Pipeline     O(n + e)      1000s        OK
Render Canvas         O(n)          1000s        Good
Form Validation       O(1)          ∞           OK
Search Toolbox        O(n)          14          Instant
```

Recommendations:
- Keep canvas to <50 nodes for smooth dragging
- Auto-connection optimization: batch edge updates
- Memoize components to prevent re-renders
- Use React.memo on PipelineNode

