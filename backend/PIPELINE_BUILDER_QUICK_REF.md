# Pipeline Builder - Quick Reference Guide

## Frontend Location
- **URL**: `http://localhost:5173/dashboard/management/pipeline-builder`
- **Folder**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/pipeline-builder/`

---

## What's Implemented

### UI Components
- [x] Visual canvas with React Flow
- [x] Draggable toolbox with 14 node types
- [x] Multi-step configuration forms for each node
- [x] Pipeline validator with rules
- [x] Node auto-connection logic
- [x] Status indicators and visual feedback
- [x] Pipeline execution monitor (mock data)

### Business Logic
- [x] Node type definitions (4 categories)
- [x] Connection validation rules
- [x] Auto-connection algorithm
- [x] Form validation and persistence
- [x] Pipeline export to JSON structure
- [x] Pipeline import from JSON structure

---

## What's NOT Implemented

### Frontend
- [ ] **Save Button**: No API call (see line 140-143 in index.tsx)
- [ ] **Run Button**: No backend execution (see line 145-149 in index.tsx)
- [ ] Real log streaming
- [ ] WebSocket connection
- [ ] Pipeline history/versioning
- [ ] Undo/Redo

### Backend
- [ ] No pipeline models
- [ ] No API endpoints
- [ ] No database persistence
- [ ] No execution engine

---

## Key Files to Understand

```
pipeline-builder/
├── index.tsx                    # Main page, Save/Run buttons
├── hooks/usePipelineBuilder.ts  # State management & logic
├── components/
│   ├── Canvas.tsx              # React Flow container
│   ├── PipelineNode.tsx         # Node rendering
│   ├── NodeEditor.tsx           # Configuration form
│   ├── Toolbox.tsx              # Tool categories
│   ├── PipelineValidator.tsx    # Validation UI
│   ├── PipelineRunner.tsx       # Execution status
│   ├── ArrowEdge.tsx            # Edge rendering
│   └── PipelineEdge.tsx         # Alternative edge
└── utils/pipelineRules.ts       # Connection rules & validation
```

---

## Data Structure

### Complete Pipeline Object
```json
{
  "nodes": [
    {
      "id": "uuid",
      "type": "pipelineNode",
      "position": { "x": 100, "y": 200 },
      "data": {
        "id": "uuid",
        "name": "Node Name",
        "type": "website|textSplitter|embeddingGenerator|etc",
        "status": "pending|running|completed|failed",
        "description": "...",
        "configured": true,
        ...nodeSpecificConfig
      }
    }
  ],
  "edges": [
    {
      "id": "edge-id",
      "source": "node-id",
      "target": "node-id",
      "type": "arrow",
      "animated": true,
      "style": { "stroke": "#228be6", "strokeWidth": 2 }
    }
  ]
}
```

---

## Node Types

### Data Sources (Max 1)
- `website` - Website crawling
- `multiple_pages` - CSV/TXT with URLs
- `single_page` - Single page scraping
- `confluence` - Confluence crawler

### Processing
- `textSplitter` - Document chunking

### AI Tools
- `embeddingGenerator` - Text to vectors
- `textSummarizer` - Summarization
- `contentClassifier` - Classification
- `contentEnricher` - Enrichment
- `translation` - Translation

### Storage & Output
- `vectorDatabase` - Vector storage
- `fileExport` - File output
- `reportGenerator` - Reports
- `analytics` - Analytics
- `notification` - Notifications

---

## Validation Rules

### Required Nodes
1. At least 1 data source
2. Document splitter
3. Embedding generator
4. Vector database

### Connection Flow
```
Data Source → Document Splitter → AI Tools → Vector Database → Output
```

---

## Configuration Examples

### Website Crawler Node
```typescript
{
  scraping_mode: 'website',
  url: 'https://example.com',
  crawl_depth: 4,
  css_selector: 'main > article',
  allowed_subdomains: ['www', 'docs'],
  blocked_subdomains: ['admin'],
  content_filter_threshold: 0.6
}
```

### Text Splitter Node
```typescript
{
  chunk_size: 1000,
  chunk_overlap: 200,
  batch_size: 100
}
```

---

## Integration Checklist

### Frontend
- [ ] Uncomment/replace `// TODO: Implement save logic` at line 140
- [ ] Call API to save pipeline
- [ ] Uncomment/replace `// TODO: Implement run logic` at line 145
- [ ] Stream real logs via WebSocket or polling
- [ ] Handle errors and user feedback

### Backend - Pipeline Endpoints Needed
```
POST   /api/pipelines              # Create/Save
GET    /api/pipelines              # List all
GET    /api/pipelines/:id          # Get one
PUT    /api/pipelines/:id          # Update
DELETE /api/pipelines/:id          # Delete
POST   /api/pipelines/:id/run      # Execute
WS     /ws/pipelines/:id/logs      # Stream logs
```

### Backend - Database Schema Needed
```
pipelines table:
- id (UUID)
- name (string)
- description (string)
- nodes (JSON/JSONB)
- edges (JSON/JSONB)
- status (enum)
- created_at (timestamp)
- updated_at (timestamp)
- created_by (user_id)
```

---

## Save Button Implementation Example

```typescript
// In index.tsx, replace handleSavePipeline
const handleSavePipeline = useCallback(async () => {
  try {
    const pipeline = savePipeline();
    const response = await api.post('/pipelines', {
      name: 'My Pipeline',
      description: 'Pipeline description',
      nodes: pipeline.nodes,
      edges: pipeline.edges
    });
    showNotification({
      title: 'Success',
      message: 'Pipeline saved successfully'
    });
  } catch (error) {
    showNotification({
      title: 'Error',
      message: 'Failed to save pipeline'
    });
  }
}, [savePipeline]);
```

---

## Run Button Implementation Example

```typescript
// In index.tsx, replace handleRunPipeline
const handleRunPipeline = useCallback(async () => {
  if (isRunning) {
    setIsRunning(false);
    return;
  }
  
  setIsRunning(true);
  try {
    const pipeline = savePipeline();
    const response = await api.post(`/pipelines/${pipelineId}/run`, {
      nodes: pipeline.nodes,
      edges: pipeline.edges
    });
    
    // Stream logs via WebSocket
    ws.connect(`/ws/pipelines/${response.id}/logs`);
  } catch (error) {
    setIsRunning(false);
  }
}, [isRunning, savePipeline]);
```

---

## Testing the Frontend (Without Backend)

1. Open browser console and add a pipeline
2. Check `savePipeline()` output
3. Verify all required nodes are present
4. Check validation status
5. Try invalid configurations

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Nodes won't connect | Check validation rules in `pipelineRules.ts` |
| Form won't save | Check form validation errors in browser console |
| Canvas not responding | Check React Flow version compatibility |
| Toolbox dragging issues | Ensure `onDragStart` is setting data transfer correctly |

---

## Performance Notes

- Current canvas: 600px height, unlimited nodes
- Uses React Flow's built-in optimization
- Auto-connection triggers on every node add (O(n) complexity)
- Form validation is real-time
- No major performance issues with <20 nodes

---

## Style & Theme

- **Primary Color**: #45c9bb (teal)
- **Status Colors**: 
  - Pending: #868e96 (gray)
  - Running: #228be6 (blue)
  - Completed: #51cf66 (green)
  - Failed: #ff6b6b (red)
- **UI Framework**: Mantine v7.17.8
- **Icons**: Tabler Icons

---

## Related Documentation

- Mantine Form: https://mantine.dev/form/use-form/
- React Flow: https://reactflow.dev/
- TypeScript: https://www.typescriptlang.org/

