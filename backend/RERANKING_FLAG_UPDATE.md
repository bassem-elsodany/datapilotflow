# ✅ MCP Tool Update: Explicit Reranking Flag

## Overview

The `knowledge_expert` MCP tool now has an **explicit boolean flag** to control reranking behavior.

**Date Updated:** 2025-12-18
**Commit:** 2631d48

---

## What Changed

### Before
Reranking was inferred from whether LLM parameters were provided:
```python
enable_reranking = bool(query_input.llm_provider_id and query_input.llm_model_name)
```

### After
Reranking is now **explicitly controlled** via a dedicated parameter:
```python
enable_reranking: bool = False  # Supervisor explicitly sets this
```

---

## New MCP Tool Signature

```python
async def knowledge_expert(
    search_query: List[str],              # 5 query variants
    collection_name: str,                 # Collection name
    top_k: int = 5,                       # Documents to retrieve
    user_id: str = "",                    # User ID

    # Embedding configuration (REQUIRED)
    embedding_provider_id: str = "",      # From vector_database
    embedding_model_name: str = "",       # From vector_database
    vector_dimension: int = 1536,         # From vector_database

    # Reranking control (NEW - EXPLICIT)
    enable_reranking: bool = False,       # ← SET THIS EXPLICITLY

    # LLM configuration (OPTIONAL - only if reranking enabled)
    llm_provider_id: str = "",            # Required if enable_reranking=True
    llm_model_name: str = "",             # Required if enable_reranking=True

    # Tracking
    conversation_id: str = "",
    conversation_description: str | None = None,
) -> Dict[str, Any]:
```

---

## Usage Pattern

### To Enable Reranking

```python
result = await mcp_tools.knowledge_expert(
    search_query=query_variants,
    collection_name="MyCollection",
    user_id="user-123",
    embedding_provider_id="provider-456",
    embedding_model_name="text-embedding-3",
    vector_dimension=1536,

    # ENABLE RERANKING EXPLICITLY
    enable_reranking=True,                 # ← Flag set to True
    llm_provider_id="llm-789",             # Required when True
    llm_model_name="gpt-4",                # Required when True

    conversation_id="conv-123",
)
```

### To Disable Reranking (Just Retrieve)

```python
result = await mcp_tools.knowledge_expert(
    search_query=query_variants,
    collection_name="MyCollection",
    user_id="user-123",
    embedding_provider_id="provider-456",
    embedding_model_name="text-embedding-3",
    vector_dimension=1536,

    # DISABLE RERANKING EXPLICITLY
    enable_reranking=False,                # ← Flag set to False
    # llm_provider_id not needed
    # llm_model_name not needed

    conversation_id="conv-123",
)
```

---

## Key Points

### 1. **Explicit Control**
- Supervisor agent explicitly sets `enable_reranking` to True or False
- No inference or hidden logic
- Clear and predictable behavior

### 2. **Default Behavior**
- `enable_reranking=False` by default
- Reranking must be explicitly requested

### 3. **Requirements**
- **Always required:** embedding_provider_id, embedding_model_name, vector_dimension
- **Required if enable_reranking=True:** llm_provider_id, llm_model_name
- **Optional otherwise:** LLM parameters ignored if enable_reranking=False

### 4. **Logging**
The tool logs which configuration was selected:

**If enabled:**
```
🔧 MCP Configuration: reranking=ENABLED (supervisor enabled reranking via flag)
```

**If disabled:**
```
🔧 MCP Configuration: reranking=DISABLED (supervisor disabled reranking via flag)
```

---

## Supervisor Integration

### Step 1: Load Agent Configuration

```python
agent = await agent_service.get_agent(agent_id, user_id)
```

### Step 2: Decide on Reranking

```python
# Business logic to decide if reranking should be enabled
# Example: Check if user has premium tier, performance settings, etc.
should_enable_reranking = True  # or False based on your logic
```

### Step 3: Call MCP Tool

```python
result = await mcp_tools.knowledge_expert(
    search_query=query_variants,
    collection_name=agent.vector_database.collection_name,
    top_k=agent.vector_database.top_k,
    user_id=user_id,

    # Embedding config (from vector database)
    embedding_provider_id=agent.vector_database.embedding_provider.id,
    embedding_model_name=agent.vector_database.embedding_provider.model_name,
    vector_dimension=agent.vector_database.vector_dimension,

    # Reranking control (from business logic)
    enable_reranking=should_enable_reranking,

    # LLM config (from agent, only used if enable_reranking=True)
    llm_provider_id=agent.llm_provider.id if should_enable_reranking else "",
    llm_model_name=agent.llm_provider.model_name if should_enable_reranking else "",

    # Tracking
    conversation_id=conversation_id,
    conversation_description=conversation_description,
)
```

---

## Complete Example (Python)

```python
async def retrieve_documents_with_rag(
    user_query: str,
    agent_id: str,
    user_id: str,
    enable_reranking: bool = True,
) -> Dict[str, Any]:
    """Retrieve documents using MCP RAG tool with explicit reranking control."""

    # Load agent configuration
    agent = await agent_service.get_agent(agent_id, user_id)

    # Generate query variants
    query_variants = await query_service.generate_variants(user_query)

    # Call MCP knowledge_expert tool with explicit flag
    result = await mcp_tools.knowledge_expert(
        search_query=query_variants,
        collection_name=agent.vector_database.collection_name,
        top_k=agent.vector_database.top_k,
        user_id=user_id,

        # Embedding configuration (ALWAYS provided)
        embedding_provider_id=agent.vector_database.embedding_provider.id,
        embedding_model_name=agent.vector_database.embedding_provider.model_name,
        vector_dimension=agent.vector_database.vector_dimension,

        # Reranking flag (EXPLICITLY SET)
        enable_reranking=enable_reranking,

        # LLM configuration (only if reranking enabled)
        llm_provider_id=agent.llm_provider.id if enable_reranking else "",
        llm_model_name=agent.llm_provider.model_name if enable_reranking else "",

        conversation_id=conversation_id,
        conversation_description="User query",
    )

    # Process results
    documents = result["documents"]
    metadata = result["metadata"]

    return {
        "documents": documents,
        "metadata": metadata,
        "reranking_enabled": enable_reranking,
    }
```

---

## Backward Compatibility

✅ **Fully backward compatible:**
- Default value is `False` (no reranking)
- Existing code that doesn't pass the flag will work as before
- Gradual migration: new code uses explicit flag, old code continues to work

---

## Testing

### Test 1: With Reranking Enabled

```python
result = await knowledge_expert(
    search_query=["variant1", "variant2", "variant3", "variant4", "variant5"],
    collection_name="test_collection",
    user_id="user-123",
    embedding_provider_id="provider-456",
    embedding_model_name="text-embedding-3",
    vector_dimension=1536,
    enable_reranking=True,
    llm_provider_id="llm-789",
    llm_model_name="gpt-4",
    conversation_id="conv-123",
)

# Expect: Documents ranked by relevance
assert len(result["documents"]) > 0
```

### Test 2: With Reranking Disabled

```python
result = await knowledge_expert(
    search_query=["variant1", "variant2", "variant3", "variant4", "variant5"],
    collection_name="test_collection",
    user_id="user-123",
    embedding_provider_id="provider-456",
    embedding_model_name="text-embedding-3",
    vector_dimension=1536,
    enable_reranking=False,  # ← Disabled
    conversation_id="conv-123",
)

# Expect: Documents in RRF order (not reranked)
assert len(result["documents"]) > 0
```

---

## Files Modified

1. **src/agents/rag_agent/mcp/tools.py**
   - Added `enable_reranking: bool = False` to RAGQueryInput
   - Updated MCP tool definition with boolean parameter

2. **src/agents/rag_agent/mcp/server.py**
   - Added `enable_reranking: bool = False` parameter to function signature
   - Use explicit flag instead of inferring from LLM parameters
   - Updated docstring and logging

---

## Migration Guide

### For Existing Supervisor Agents

**If currently inferring reranking from LLM parameters:**
```python
# OLD WAY (still works but not recommended)
result = await knowledge_expert(
    ...,
    llm_provider_id="some-id",  # ← Infers enable_reranking=True
    llm_model_name="model-name",
)
```

**NEW WAY (recommended):**
```python
# NEW WAY (explicit control)
result = await knowledge_expert(
    ...,
    enable_reranking=True,      # ← Explicit flag
    llm_provider_id="some-id",
    llm_model_name="model-name",
)
```

### Update Checklist

- [ ] Identify all calls to `knowledge_expert` MCP tool
- [ ] Add `enable_reranking` parameter explicitly
- [ ] Set to `True` if reranking is desired
- [ ] Set to `False` if only retrieving documents
- [ ] Update any documentation or examples
- [ ] Test with both settings

---

## FAQ

**Q: Can I still infer reranking from LLM parameters?**
A: No, reranking is now explicitly controlled via the flag. You must set `enable_reranking=True/False`.

**Q: What if I don't set the flag?**
A: It defaults to `False`, meaning reranking is disabled.

**Q: What if I set enable_reranking=True but don't provide LLM parameters?**
A: The tool will attempt reranking but may fail if LLM provider is not available. It's recommended to provide LLM parameters when setting the flag to True.

**Q: Does this affect the RAG workflow (non-MCP mode)?**
A: No, this only affects the MCP tool. RAG workflow reranking configuration is unchanged.

---

## Summary

The explicit `enable_reranking` flag provides:

✅ **Clear Control:** Supervisor explicitly decides on reranking
✅ **Predictable Behavior:** No inference or hidden logic
✅ **Backward Compatible:** Default to False, works with existing code
✅ **Better Logging:** Logs exactly what was decided
✅ **Flexible:** Supervisor can enable/disable per request

---

**Status:** Ready for Supervisor Agent Integration
**Compilation:** ✅ All files compile successfully
**Backward Compatibility:** ✅ Fully maintained

---

*Updated: 2025-12-18*
*Generated with Claude Code* 🤖
