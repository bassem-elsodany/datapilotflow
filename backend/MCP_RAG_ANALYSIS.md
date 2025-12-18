# MCP RAG Server Analysis: Reranking & Embedding Provider Issues

## Current State Overview

### MCP Server (server.py) - Lines 32-189
The RAG MCP server is a tool exposed to Assistant agents for knowledge retrieval via the `knowledge_expert` tool.

**Current Configuration (Lines 96-122):**
```python
enable_reranking = False                    # ❌ DISABLED
relevance_threshold = 0.5                   # Not used (reranking disabled)
enable_llm_generation = False
selected_strategy = "custom_variants"
```

**Current Parameters Passed to RAG Workflow (Lines 103-122):**
- ✅ `collection_name` - Vector DB collection name
- ✅ `user_id` - For tracking
- ❌ `llm_provider_id` - LLM provider (for query enhancement, NOT embedding)
- ❌ `llm_model_name` - LLM model name (for query enhancement, NOT embedding)
- ❌ Missing: `embedding_provider_id` - Embedding provider for converting variants to vectors
- ❌ Missing: `embedding_model_name` - Embedding model name

**MCP Tool Input Schema (tools.py Lines 33-49):**
- Accepts: `llm_provider_id`, `llm_model_name`
- Missing: Embedding provider fields

---

## Problem Analysis

### Issue 1: Reranking Disabled in Assistant Mode

**Current Line 97:**
```python
enable_reranking = False
```

**Problem:**
- Reranking is always disabled when using the MCP tool in assistant agent mode
- This means the `document_judger` node (nodes/document_judger.py) is never executed
- Documents are returned in RRF fusion order, not relevance-ranked order
- Document quality is not evaluated by LLM before returning to assistant

**Architecture Complexity:**
- Assistant agents need reranking disabled by default to avoid double-processing
- BUT: The MCP tool should enable reranking using the agent's primary LLM
- Current code comment says "ASSISTANT MODE: Fixed configuration" but doesn't match requirement

---

### Issue 2: Wrong Provider Type Being Passed

**Current Situation (server.py Lines 38-39, 90-91, 106-107):**
```python
llm_provider_id: str = "",
llm_model_name: str = "",
# ...
llm_provider_id=llm_provider_id,
llm_model_name=llm_model_name,
```

**Problem:**
The MCP tool receives `llm_provider_id` and `llm_model_name` which are used in two different ways:

1. **In RAG Workflow (generate_response_rag.py Lines 153-203):**
   - Used to create the PRIMARY LLM CLIENT
   - Used for: Query enhancement, reranking (when enabled), answer generation (when enabled)
   - ✅ This is correct for assistant mode

2. **In Vector Search (retrieval_tools.py Lines 82-90):**
   - Milvus query uses `vector_dimension=1536` (hardcoded!)
   - The actual embedding happens INSIDE MilvusClientWrapper
   - ❌ MilvusClientWrapper doesn't know which embedding model to use
   - ❌ Currently assumes standard OpenAI embeddings (1536 dimensions)

**Why This Matters:**
- If collection was created with OpenAI embeddings (1536 dims), this works
- If collection was created with Jina/Cohere/other embeddings (different dims), this FAILS
- The MCP tool MUST know the EMBEDDING provider to:
  1. Know the vector dimension
  2. Convert query variants to embeddings using the SAME model used during collection creation
  3. Ensure vector similarity search works correctly

---

## Data Flow Analysis

### Current Flow (INCORRECT):
```
Assistant Agent
     ↓
MCP Tool: knowledge_expert(
  llm_provider_id="provider-123",
  llm_model_name="gpt-4",
  collection_name="MyCollection"
)
     ↓
RAG Workflow Config:
  - llm_provider_id (for enhancement LLM) ✅
  - collection_name ✅
  - embedding_provider_id ❌ MISSING
  - embedding_model_name ❌ MISSING
     ↓
Document Retriever:
  - Creates MilvusRetriever without embedding info
  - Milvus hardcodes vector_dimension=1536
  - Query variants converted to embeddings with UNKNOWN model
     ↓
Vector Search FAILS if collection used different embedding model!
```

### Required Flow (CORRECT):
```
Assistant Agent with Agent Config:
  - llm_provider_id: "provider-123"        (LLM for enhancement/reranking)
  - llm_model_name: "gpt-4"
  - embedding_provider_id: "emb-456"      (Embedding for vectorization)
  - embedding_model_name: "text-embedding-3-small"
  - vector_dimension: 1536
     ↓
MCP Tool: knowledge_expert(
  ...,
  embedding_provider_id="emb-456",        ← NEW
  embedding_model_name="text-embedding-3-small", ← NEW
  vector_dimension=1536                   ← NEW
)
     ↓
RAG Workflow Config includes embedding info
     ↓
Document Retriever:
  - Creates MilvusRetriever with CORRECT embedding config
  - MilvusClientWrapper initializes with CORRECT vector_dimension
  - Query variants converted with CORRECT embedding model
     ↓
Vector Search SUCCEEDS with accurate similarity scores
     ↓
Reranking enabled:
  - document_judger uses agent's primary LLM
  - Reranks documents for better relevance
     ↓
Returns top ranked documents to Assistant
```

---

## Collection Configuration Context

### Vector DB Collection Structure (VectorDBCollection model):
From `src/domain/knowledge/vectordb_collection.py`:
```python
embedding_model_provider_id: str           # ID of embedding provider
embedding_model_name: str                  # Name of embedding model
vector_dimension: int                      # Dimension of embeddings (e.g., 1536, 384)
collection_name: str                       # Milvus collection name
```

**Key Point:** Collections store their embedding provider info. This info MUST be passed to the MCP tool when called.

---

## Agent Configuration Context

### Agent Model (src/domain/agent/models.py):
```python
llm_provider: Optional[ProviderConfig]     # Primary LLM for enhancement/reranking/generation
vector_database: Optional[VectorDatabaseConfig]  # Contains:
  - collection_name
  - embedding_provider (ID + model name)   # ← This contains embedding info!
  - vector_dimension
  - top_k
reranker: Optional[RerankerConfig]         # Separate reranker provider (optional)
```

**Key Point:** The agent ALREADY knows which embedding provider was used for the collection. This must be passed to the MCP tool.

---

## Supervisor/Assistant Integration Context

### How Assistant Calls MCP Tool:
The supervisor agent (in assistant_mode_view) calls the MCP tool with agent config.
Currently it likely passes:
- `llm_provider_id` and `llm_model_name` from agent's primary LLM
- But NOT the embedding provider info from agent's vector_database config

---

## Implementation Requirements

### Requirement 1: Enable Reranking in MCP Mode
- Change: `enable_reranking = False` → `enable_reranking = True`
- Rationale: Documents should be ranked by relevance before returning to assistant
- Using: Agent's primary LLM (already passed as `llm_provider_id`)
- Impact: Slightly higher latency, significantly better result quality

### Requirement 2: Add Embedding Provider Parameters
Add to RAGQueryInput schema (tools.py):
```python
embedding_provider_id: str      # NEW
embedding_model_name: str       # NEW
vector_dimension: int           # NEW (from collection config)
```

### Requirement 3: Update MCP Tool Signature
Update `knowledge_expert` function signature (server.py):
```python
async def knowledge_expert(
    search_query: List[str],
    collection_name: str,
    top_k: int = 5,
    user_id: str = "",
    llm_provider_id: str = "",          # LLM for enhancement/reranking
    llm_model_name: str = "",
    embedding_provider_id: str = "",    # NEW - Embedding provider
    embedding_model_name: str = "",     # NEW - Embedding model
    vector_dimension: int = 1536,       # NEW - Embedding dimensions
    conversation_id: str = "",
    conversation_description: str | None = None,
) -> Dict[str, Any]:
```

### Requirement 4: Pass Embedding Info to Workflow
Update workflow_config (server.py Lines 103-122):
```python
workflow_config = {
    "collection_name": query_input.collection_name,
    "user_id": query_input.user_id,
    "llm_provider_id": query_input.llm_provider_id,          # For enhancement/reranking
    "llm_model_name": query_input.llm_model_name,
    "embedding_provider_id": query_input.embedding_provider_id,  # NEW
    "embedding_model_name": query_input.embedding_model_name,    # NEW
    "vector_dimension": query_input.vector_dimension,             # NEW
    "top_k": query_input.top_k,
    "enable_reranking": True,                                     # CHANGED from False
    "reranking_config": {
        "relevance_threshold": 0.5,
        "use_score_based": True,
    },
    # ... rest of config
}
```

### Requirement 5: Update Document Retriever
Update document_retriever.py to accept embedding info:
- Pass `embedding_provider_id` to MilvusRetriever
- Pass `embedding_model_name` to MilvusRetriever
- Pass `vector_dimension` to MilvusRetriever (instead of hardcoded 1536)

### Requirement 6: Update MilvusRetriever
Update tools/retriever_tool.py to accept and use embedding info:
- Accept `embedding_provider_id`, `embedding_model_name`, `vector_dimension`
- Pass these to MilvusClientWrapper for proper vector dimension validation
- Use embedding provider to convert query variants to vectors (future enhancement)

---

## File Changes Summary

### Files to Modify:
1. **tools.py** - Add embedding fields to RAGQueryInput schema
2. **server.py** - Add embedding params, enable reranking, pass to workflow
3. **nodes/document_retriever.py** - Accept and use embedding info
4. **tools/retriever_tool.py** - Update MilvusRetriever to handle embedding config

### Files NOT to Modify (Already Support This):
- ✅ generate_response_rag.py - Already handles llm_provider_id correctly
- ✅ document_judger.py - Already uses llm_client for reranking
- ✅ MilvusClientWrapper - Already accepts vector_dimension

---

## Risk Assessment

### Low Risk:
- ✅ Adding embedding provider fields (backward compatible if optional with defaults)
- ✅ Enabling reranking (uses existing document_judger node)
- ✅ Passing additional config to workflow (workflow already extracts what it needs)

### Medium Risk:
- ⚠️ Must ensure embedding_provider_id is passed from supervisor/assistant
- ⚠️ Must handle case where embedding info is not provided (fallback to defaults)

### High Risk:
- ❌ If embedding_provider_id/model are wrong, vector search will fail silently
- ❌ Dimension mismatches will cause "vector has wrong dimension" errors

---

## Implementation Plan (Step-by-Step)

### Phase 1: Data Structure Updates
1. Update RAGQueryInput schema to include embedding fields
2. Update MCP tool definition to document new fields
3. Add fields to workflow config initialization

### Phase 2: MCP Server Updates
1. Add embedding_provider_id, embedding_model_name, vector_dimension parameters
2. Change enable_reranking from False to True
3. Pass embedding fields to workflow_config

### Phase 3: Workflow Integration
1. Update document_retriever to extract embedding info from config
2. Pass embedding info to MilvusRetriever
3. Update MilvusRetriever to accept and validate embedding config
4. Add logging to show which embedding model is being used

### Phase 4: Supervisor Integration
1. Update supervisor agent to extract embedding info from agent's vector_database config
2. Pass embedding fields when calling MCP tool
3. Add error handling for missing embedding info

### Phase 5: Testing & Validation
1. Test with collection using standard OpenAI embeddings (1536 dims)
2. Test with collection using different embedding models
3. Test reranking enabled vs disabled
4. Verify vector dimensions match expectations
5. Check relevance improvement with reranking enabled

---

## Questions for Implementation

1. **Should embedding provider be optional?**
   - If not provided, fallback to 1536 dimension + generic embedding?
   - Or require it always?

2. **Should reranking always be enabled in MCP mode?**
   - Or should it be configurable?
   - Current answer: YES, enable by default for better quality

3. **How should supervisor call MCP tool?**
   - Should supervisor extract embedding info from agent config?
   - Or should API endpoint that calls MCP tool add it?

4. **Error handling for dimension mismatch?**
   - Fallback to first N dimensions?
   - Raise error and fail gracefully?
   - Log warning and continue?

5. **Performance impact of reranking?**
   - How much latency increase?
   - Should there be a mode to disable for high-latency scenarios?
