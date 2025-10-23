# Pipeline Builder Implementation Summary

## Overview

Successfully implemented a complete **Visual Pipeline Builder** system that allows users to create data processing workflows using a drag-and-drop interface instead of multiple separate wizards. When users save a pipeline, the system creates all necessary objects (sources, splitters, collections, jobs) and links them together automatically.

---

## Architecture

### Core Concept

The pipeline builder is a **graphical wizard alternative**:
- **Traditional Flow**: User creates source (wizard) → Creates job (wizard) → Links manually
- **Pipeline Builder**: User drags nodes → Configures visually → Click "Save" → All objects created and linked automatically

### Data Flow

```
Frontend Pipeline Builder (React Flow)
    ↓ [Save Button]
    ↓ POST /api/v1/pipelines
    ↓
Backend Pipeline Service
    ↓ [Stores visual template in MongoDB]
    ↓
Pipeline Document (nodes + edges + config)
    ↓ [Run Button]
    ↓ POST /api/v1/pipelines/{id}/execute
    ↓
Pipeline Executor
    ↓ [Converts visual graph to actual objects]
    ↓
Creates: KnowledgeSource → DocumentSplitter → VectorDBCollection → KnowledgeJob
    ↓
Executes via RabbitMQ
```

---

## Implementation Details

### Backend Components

#### 1. Domain Models (`src/domain/knowledge/pipeline.py`)

**Key Models:**
- `Pipeline` - Stores the visual pipeline template
- `PipelineNode` - Represents each node in the graph (14 types supported)
- `PipelineEdge` - Connections between nodes
- `PipelineExecutionStatus` - Real-time execution tracking

**Node Types:**
```python
# Data Sources
- website, multiple_pages, single_page, confluence

# Processing
- textSplitter

# AI Tools
- embeddingGenerator, textSummarizer, contentClassifier, contentEnricher, translation

# Storage/Output
- vectorDatabase, fileExport, reportGenerator, analytics, notification
```

**Node Configuration Schemas:**
Each node type has its own configuration schema (e.g., `WebsiteNodeConfig`, `TextSplitterNodeConfig`) that maps to the existing service models.

#### 2. Data Access Layer (`src/services/knowledge/dao/pipeline_dao.py`)

**PipelineDAO extends MongoClientWrapper:**
- CRUD operations for pipeline documents
- User-scoped queries (each user sees only their pipelines)
- Status tracking methods
- Node status updates during execution

**MongoDB Collection:** `pipelines`

**Indexes:**
- `user_id + created_at` (for listing user pipelines)
- `status` (for filtering by execution state)
- `name` (text search)

#### 3. Service Layer (`src/services/knowledge/pipeline_service.py`)

**PipelineService orchestrates existing services:**

**Key Methods:**
- `create_pipeline()` - Save visual template
- `execute_pipeline()` - Convert template to actual execution:
  1. Extract source config from data source nodes
  2. Extract splitter config from splitter nodes
  3. Extract vectordb config from storage nodes
  4. Create `KnowledgeSource` via existing service
  5. Create `DocumentSplitter` via existing service
  6. Create `VectorDBCollection` via existing service
  7. Create and execute `KnowledgeJob` via existing service

**Configuration Extraction:**
- `_extract_source_config()` - Converts node config to `KnowledgeSourceConfigCreate`
- `_extract_splitter_config()` - Converts node config to `DocumentSplitterCreate`
- `_extract_vectordb_config()` - Converts node config to `VectorDBCollectionCreate`

#### 4. API Router (`src/api/routers/knowledge/pipeline_router.py`)

**REST Endpoints:**
```python
POST   /api/v1/pipelines              # Create new pipeline
GET    /api/v1/pipelines              # List user's pipelines
GET    /api/v1/pipelines/{id}         # Get specific pipeline
PUT    /api/v1/pipelines/{id}         # Update pipeline
DELETE /api/v1/pipelines/{id}         # Delete pipeline
POST   /api/v1/pipelines/{id}/execute # Execute pipeline
GET    /api/v1/pipelines/{id}/status  # Get execution status
```

All endpoints require JWT authentication and are user-scoped.

#### 5. API Server Integration (`src/api_server.py`)

Router registered at `/api/v1/pipelines` with tag "Pipeline Management".

---

### Frontend Components

#### 1. API Resource (`dashboard/src/api/resources/pipelines.ts`)

**Zod Schemas:**
- All models validated with Zod (type-safe at runtime)
- Matches backend Pydantic models exactly

**React Query Hooks:**
```typescript
useGetPipelines()                    // List all pipelines
useGetPipeline(pipelineId)           // Get specific pipeline
useCreatePipeline()                  // Create new pipeline
useUpdatePipeline()                  // Update existing pipeline
useDeletePipeline()                  // Delete pipeline
useExecutePipeline()                 // Execute pipeline
useGetPipelineStatus(pipelineId)     // Poll for execution status
```

**Cache Management:**
- Auto-invalidates related queries on mutations
- Optimistic updates for better UX

#### 2. API Endpoints Config (`dashboard/src/config.ts`)

Added `pipelines` section:
```typescript
pipelines: {
  list: '/pipelines',
  create: '/pipelines',
  pipeline: (pipelineId: string) => `/pipelines/${pipelineId}`,
  update: (pipelineId: string) => `/pipelines/${pipelineId}`,
  delete: (pipelineId: string) => `/pipelines/${pipelineId}`,
  execute: (pipelineId: string) => `/pipelines/${pipelineId}/execute`,
  status: (pipelineId: string) => `/pipelines/${pipelineId}/status`,
}
```

#### 3. Pipeline Builder Page (`dashboard/src/pages/dashboard/management/pipeline-builder/index.tsx`)

**Save Button Implementation:**
```typescript
handleSavePipeline():
  1. Validate pipeline structure
  2. Transform ReactFlow nodes/edges to API format
  3. POST to /api/v1/pipelines (create) or PUT (update)
  4. Show success/error notification
  5. Store pipeline ID for subsequent updates
```

**Run Button Implementation:**
```typescript
handleRunPipeline():
  1. Validate pipeline structure
  2. Auto-save if not already saved
  3. POST to /api/v1/pipelines/{id}/execute
  4. Show execution started notification with Job ID
  5. Track execution status
```

**Key Features:**
- Validation before save/run
- Automatic pipeline ID tracking
- Success/error notifications
- Loading states during API calls
- Idempotent save (create or update based on state)

---

## Data Models Mapping

### Frontend to Backend Mapping

**ReactFlow Node → PipelineNode:**
```typescript
{
  id: "uuid",
  type: "pipelineNode",          // ReactFlow type
  position: { x: 100, y: 200 },
  data: {
    id: "uuid",
    type: "website",             // Our node type
    name: "My Website Source",
    status: "pending",
    configured: true,
    config: { url: "...", ... }  // Node-specific config
  }
}
```

**PipelineNode → KnowledgeSource:**
When executing, the service extracts `config` from nodes and creates actual resources:
```python
# From node config
{
  "type": "website",
  "config": {
    "url": "https://example.com",
    "crawl_depth": 2,
    ...
  }
}

# Creates KnowledgeSourceConfigCreate
{
  "name": "Website Source",
  "url": "https://example.com",
  "scraping_mode": "website",
  "crawl_depth": 2,
  ...
}
```

---

## Execution Flow Example

### User Creates Pipeline in UI

1. **Drag nodes onto canvas:**
   - Website Source node
   - Text Splitter node
   - Embedding Generator node
   - Vector Database node

2. **Configure each node:**
   - Website: `url: "https://docs.example.com"`, `crawl_depth: 2`
   - Splitter: `chunk_size: 512`, `chunk_overlap: 50`
   - Embedding: `model: "text-embedding-3-small"`, `dimension: 1536`
   - VectorDB: `collection_name: "docs_collection"`

3. **Click "Save":**
   ```json
   POST /api/v1/pipelines
   {
     "name": "Documentation Pipeline",
     "nodes": [
       { "id": "node-1", "type": "website", "config": {...} },
       { "id": "node-2", "type": "textSplitter", "config": {...} },
       { "id": "node-3", "type": "embeddingGenerator", "config": {...} },
       { "id": "node-4", "type": "vectorDatabase", "config": {...} }
     ],
     "edges": [
       { "source": "node-1", "target": "node-2" },
       { "source": "node-2", "target": "node-3" },
       { "source": "node-3", "target": "node-4" }
     ]
   }
   ```

4. **Backend stores in MongoDB:**
   - Collection: `pipelines`
   - Document contains entire visual configuration
   - Status: `draft`

5. **Click "Run":**
   ```json
   POST /api/v1/pipelines/{pipeline_id}/execute
   ```

6. **Backend executes:**
   ```python
   # 1. Create Knowledge Source
   source = knowledge_source_service.create_knowledge_source_config(
       KnowledgeSourceConfigCreate(
           name="Documentation Pipeline - Source",
           url="https://docs.example.com",
           scraping_mode="website",
           crawl_depth=2
       ),
       user_id
   )

   # 2. Create Document Splitter
   splitter = document_splitter_service.create_splitter(
       DocumentSplitterCreate(
           name="Documentation Pipeline - Splitter",
           chunk_size=512,
           chunk_overlap=50
       ),
       user_id
   )

   # 3. Create Vector DB Collection
   collection = vectordb_collection_service.create_collection(
       VectorDBCollectionCreate(
           name="docs_collection",
           model_name="text-embedding-3-small",
           vector_dimension=1536
       ),
       user_id
   )

   # 4. Create and Execute Knowledge Job
   job = knowledge_job_service.create_knowledge_job(
       source.id,
       KnowledgeJobCreate(
           name="Documentation Pipeline - Execution",
           splitter_id=splitter.id,
           existing_collection_id=collection.id,
           batch_size=100
       ),
       user_id
   )

   # 5. Execute via RabbitMQ
   knowledge_job_service.execute_job(job.id, user_id)
   ```

7. **Response:**
   ```json
   {
     "pipeline_id": "...",
     "job_id": "...",
     "knowledge_source_id": "...",
     "status": "running",
     "message": "Pipeline execution started. Job ID: ..."
   }
   ```

---

## Files Created/Modified

### Backend Files Created
1. `src/domain/knowledge/pipeline.py` - Domain models (509 lines)
2. `src/services/knowledge/dao/pipeline_dao.py` - DAO (222 lines)
3. `src/services/knowledge/pipeline_service.py` - Service (394 lines)
4. `src/api/routers/knowledge/pipeline_router.py` - Router (199 lines)

### Backend Files Modified
1. `src/domain/knowledge/__init__.py` - Export pipeline models
2. `src/services/knowledge/dao/__init__.py` - Export PipelineDAO
3. `src/api/routers/__init__.py` - Export pipeline_router
4. `src/api_server.py` - Register pipeline_router

### Frontend Files Created
1. `dashboard/src/api/resources/pipelines.ts` - API hooks (237 lines)

### Frontend Files Modified
1. `dashboard/src/config.ts` - Add pipeline endpoints
2. `dashboard/src/api/resources/index.ts` - Export pipelines
3. `dashboard/src/pages/dashboard/management/pipeline-builder/index.tsx` - Implement Save/Run

---

## Testing Recommendations

### Manual Testing Flow

1. **Start Backend:**
   ```bash
   python run_api_server.py
   ```

2. **Start Frontend:**
   ```bash
   cd dashboard && npm run dev
   ```

3. **Open Pipeline Builder:**
   Navigate to: `http://localhost:5173/dashboard/management/pipeline-builder`

4. **Create Pipeline:**
   - Drag a "Website" node
   - Configure URL and settings
   - Drag a "Text Splitter" node
   - Drag an "Embedding Generator" node
   - Drag a "Vector Database" node
   - Connect them in order

5. **Save Pipeline:**
   - Click "Save" button
   - Check notification for success
   - Check browser console for pipeline ID
   - Verify in MongoDB: `db.pipelines.find()`

6. **Run Pipeline:**
   - Click "Run Pipeline" button
   - Check notification for job ID
   - Monitor in MongoDB: `db.knowledge_jobs.find()`
   - Check RabbitMQ for job messages

### API Testing with cURL

```bash
# Create pipeline
curl -X POST http://localhost:8000/api/v1/pipelines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Pipeline",
    "nodes": [
      {
        "id": "node-1",
        "type": "website",
        "name": "Website Source",
        "position": {"x": 100, "y": 100},
        "config": {"url": "https://example.com"}
      }
    ],
    "edges": []
  }'

# List pipelines
curl http://localhost:8000/api/v1/pipelines \
  -H "Authorization: Bearer $TOKEN"

# Execute pipeline
curl -X POST http://localhost:8000/api/v1/pipelines/{id}/execute \
  -H "Authorization: Bearer $TOKEN"

# Get status
curl http://localhost:8000/api/v1/pipelines/{id}/status \
  -H "Authorization: Bearer $TOKEN"
```

---

## Future Enhancements

### Phase 1 (Current) - Complete ✓
- [x] Pipeline CRUD operations
- [x] Visual builder Save/Run buttons
- [x] Basic execution (create all objects)
- [x] Status tracking

### Phase 2 - Enhancements
- [ ] Pipeline templates (save as template, load template)
- [ ] Pipeline versioning (track changes over time)
- [ ] Scheduled pipeline execution (cron-like)
- [ ] Pipeline sharing between users

### Phase 3 - Advanced Features
- [ ] WebSocket for real-time execution logs
- [ ] Node-level status visualization during execution
- [ ] Parallel node execution (where possible)
- [ ] Pipeline execution history dashboard
- [ ] Export/import pipelines as JSON
- [ ] Pipeline marketplace (community templates)

### Phase 4 - Analytics
- [ ] Pipeline performance metrics
- [ ] Cost estimation before execution
- [ ] Execution time predictions
- [ ] Resource usage monitoring

---

## Known Limitations

1. **No Partial Execution**: Pipeline must execute all nodes sequentially. Cannot pause/resume at specific nodes.

2. **No Conditional Logic**: All nodes execute unconditionally. No if/else branching yet.

3. **No Loop Support**: Cannot repeat a section of the pipeline.

4. **Single User Ownership**: Pipelines cannot be shared or collaborated on yet.

5. **No Real-time Logs**: WebSocket integration for live logs not implemented yet.

6. **Basic Error Handling**: If one node fails, entire pipeline fails (no retry logic).

---

## Troubleshooting

### Pipeline Save Fails

**Issue**: API returns 400 Bad Request

**Solutions:**
- Check that all required node configurations are filled
- Ensure at least one data source node exists
- Verify edges connect compatible node types
- Check browser console for validation errors

### Pipeline Execution Fails

**Issue**: API returns 500 Internal Server Error

**Solutions:**
- Check backend logs for detailed error
- Verify all referenced IDs exist (model providers, etc.)
- Ensure MongoDB is running
- Ensure RabbitMQ is running
- Check that all node configs are valid

### Frontend Shows Loading Forever

**Issue**: API hooks stuck in loading state

**Solutions:**
- Check CORS settings in backend
- Verify JWT token is valid
- Check browser network tab for failed requests
- Ensure backend is running on correct port

---

## Summary

Successfully implemented a complete **Visual Pipeline Builder** that:
- ✅ Saves pipeline templates to MongoDB
- ✅ Converts visual graphs to actual knowledge processing jobs
- ✅ Orchestrates existing services (sources, splitters, collections, jobs)
- ✅ Provides RESTful API for CRUD operations
- ✅ Integrates with React frontend via React Query hooks
- ✅ Validates pipelines before save/execute
- ✅ Shows success/error notifications
- ✅ Tracks execution status

**Total Lines of Code**: ~1,500 lines across backend and frontend

**Development Time**: Approximately 4-5 hours

**Ready for Testing**: Yes ✅

The pipeline builder replaces the need for multiple separate wizards, providing a more intuitive visual interface for creating complex data processing workflows.
