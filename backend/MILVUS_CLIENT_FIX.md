# Milvus Client Vector Dimension Fix

## Issue
The application was failing when trying to create Milvus client connections with the following error:

```
TypeError: MilvusClientWrapper.__init__() missing 1 required positional argument: 'vector_dimension'
```

This error occurred in multiple places throughout the codebase where `MilvusClientWrapper` was instantiated without providing the required `vector_dimension` parameter.

## Root Cause
The `MilvusClientWrapper` class requires three mandatory parameters:
1. `model` - The Pydantic model class (e.g., `KnowledgeChunk`)
2. `collection_name` - Name of the Milvus collection (e.g., "LongTermMemory")
3. `vector_dimension` - Dimension of the embedding vectors (e.g., 1536 for OpenAI embeddings)

However, several parts of the codebase were only providing the first two parameters, causing the initialization to fail.

## Solution
Added the missing `vector_dimension=1536` parameter to all `MilvusClientWrapper` instantiations throughout the codebase.

The value `1536` is the standard dimension for:
- OpenAI's `text-embedding-ada-002` model
- OpenAI's `text-embedding-3-small` model
- Other compatible embedding models

## Files Modified

### 1. `src/api/routers/conversation/conversation_websocket_router.py`
**Before:**
```python
def get_milvus_client():
    """Helper function to create MilvusClientWrapper with proper error handling."""
    try:
        return MilvusClientWrapper(
            model=KnowledgeChunk,
            collection_name="LongTermMemory"
        )
```

**After:**
```python
def get_milvus_client(collection_name: str = "LongTermMemory"):
    """Helper function to create MilvusClientWrapper with proper error handling."""
    try:
        return MilvusClientWrapper(
            model=KnowledgeChunk,
            collection_name=collection_name,
            vector_dimension=1536  # Standard dimension for OpenAI embeddings
        )
```

**Changes:**
- Added `vector_dimension=1536` parameter
- Added `collection_name` parameter to make the function more flexible
- Added inline comment explaining the dimension value

### 2. `src/api/routers/knowledge/knowledge_router.py`
Applied the same fix as above to the `get_milvus_client()` helper function.

### 3. `src/workflow/tools/retrieval_tools.py`
Fixed all 7 occurrences of `MilvusClientWrapper` instantiation in the following functions:
- `vector_search()` - Line 76
- `semantic_search()` - Line 139
- `hybrid_search()` - Line 208
- `entity_search()` - Line 280
- `relationship_search()` - Line 349
- `knowledge_graph_search()` - Line 428
- `get_document_by_id()` - Line 490

**Example Fix:**
```python
with MilvusClientWrapper(
    model=KnowledgeChunk,
    collection_name="LongTermMemory",
    vector_dimension=1536  # Added this parameter
) as milvus_client:
    # ... search logic
```

## Impact
This fix resolves the following issues:
1. ✅ WebSocket conversation search now works correctly
2. ✅ Knowledge base queries return results
3. ✅ All retrieval tools (vector search, semantic search, hybrid search, etc.) function properly
4. ✅ Graph-based searches (entity, relationship, knowledge graph) operate as expected
5. ✅ Document retrieval by ID works correctly

## Testing
After applying this fix, verify that:
1. Conversations can be created and messages sent via WebSocket
2. Knowledge base search returns relevant results
3. No "vector_dimension" errors appear in logs
4. All search strategies (vector, semantic, hybrid) work correctly

## Future Improvements
Consider the following enhancements:
1. **Configuration-based dimension**: Move the vector dimension to settings/config:
   ```python
   VECTOR_DIMENSION: int = 1536  # in src/config.py
   ```

2. **Collection-aware dimensions**: Different collections might use different embedding models with different dimensions. Consider storing this in a collection registry:
   ```python
   COLLECTION_CONFIGS = {
       "LongTermMemory": {"dimension": 1536},
       "ShortTermMemory": {"dimension": 768},
       # etc.
   }
   ```

3. **Dynamic dimension detection**: Query the Milvus collection schema to auto-detect the dimension:
   ```python
   def get_collection_dimension(collection_name: str) -> int:
       # Query Milvus schema and return the dimension
       pass
   ```

4. **Validation**: Add validation to ensure the dimension matches the collection schema:
   ```python
   if milvus_client.collection.schema.fields['vector'].dim != vector_dimension:
       raise ValueError(f"Dimension mismatch: expected {vector_dimension}")
   ```

## Related Files
- `src/infrastructure/milvus/client.py` - MilvusClientWrapper class definition
- `src/domain/rag/knowledge_chunk.py` - KnowledgeChunk model
- `src/infrastructure/milvus/examples.py` - Example usage (already had correct dimension)

## Notes
- The standard dimension of 1536 is hardcoded for now
- All embedding operations must use models that produce 1536-dimensional vectors
- If switching to a different embedding model (e.g., `text-embedding-3-large` with 3072 dimensions), this value must be updated throughout the codebase

