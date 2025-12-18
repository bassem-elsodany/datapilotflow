# ✅ Assistant Agent Factory Update

## Overview

Updated the assistant agent factory to provide complete MCP tool parameters in the system prompt.

**Commit:** 26ceb1d
**Date:** 2025-12-18

---

## What Changed

### Issue Fixed

The assistant agent was referencing the old `agent.enhancement` structure which no longer exists. The factory was not providing embedding provider and reranking information needed for the MCP RAG tool.

### Solution

Updated `src/agents/assistant_agent/factory.py` to:

1. **Extract Embedding Configuration** (from vector_database)
   - `embedding_provider_id` - ID of the embedding provider
   - `embedding_model_name` - Name of the embedding model
   - `vector_dimension` - Vector dimension (e.g., 1536 for OpenAI)

2. **Extract LLM Configuration** (from agent.llm_provider)
   - `llm_provider_id` - Agent's primary LLM provider ID
   - `llm_model_name` - Agent's primary LLM model name

3. **Determine Reranking Flag**
   - `enable_reranking` - Set to `True` if agent has LLM provider configured
   - Automatically derived from LLM provider availability

4. **Updated System Prompt**
   - Added comprehensive "MCP Tool Parameters" section
   - Clear instructions on required vs optional parameters
   - Example of what to provide when calling `knowledge_expert`

---

## System Prompt Output

The assistant now receives a complete tool parameter section like:

```
## MCP Tool Parameters (Required for knowledge_expert and similar tools):

### Embedding Configuration (REQUIRED - from vector database):
- collection_name: "MyCollection"
- embedding_provider_id: "provider-456"
- embedding_model_name: "text-embedding-3"
- vector_dimension: 1536

### Reranking Configuration:
- enable_reranking: true

### LLM Configuration (for reranking - required if enable_reranking is True):
- llm_provider_id: "llm-789"
- llm_model_name: "gpt-4"

### General Context:
- user_id: "user-123"
- conversation_id: "conv-456"
- top_k: 5

When calling knowledge_expert or similar RAG tools, ALWAYS provide:
1. embedding_provider_id, embedding_model_name, vector_dimension (REQUIRED)
2. enable_reranking flag (set to true)
3. llm_provider_id, llm_model_name (REQUIRED if enable_reranking is true)
4. user_id, conversation_id, collection_name, top_k (REQUIRED)
```

---

## Code Changes

### Before (Broken)
```python
llm_provider = (
    agent_config.enhancement.provider.id          # ❌ OLD - doesn't exist
    if agent_config.enhancement and agent_config.enhancement.provider
    else ""
)
llm_model = (
    agent_config.enhancement.provider.model_name  # ❌ OLD - doesn't exist
    if agent_config.enhancement and agent_config.enhancement.provider
    else ""
)

# Missing embedding provider and reranking flag
```

### After (Fixed)
```python
# Embedding provider configuration (from vector database collection)
embedding_provider_id = (
    agent_config.vector_database.embedding_provider.id
    if agent_config.vector_database and agent_config.vector_database.embedding_provider
    else ""
)
embedding_model_name = (
    agent_config.vector_database.embedding_provider.model_name
    if agent_config.vector_database and agent_config.vector_database.embedding_provider
    else ""
)
vector_dimension = (
    agent_config.vector_database.vector_dimension
    if agent_config.vector_database
    else 1536
)

# LLM provider configuration (from agent's primary LLM provider)
llm_provider = (
    agent_config.llm_provider.id
    if agent_config.llm_provider
    else ""
)
llm_model = (
    agent_config.llm_provider.model_name
    if agent_config.llm_provider
    else ""
)

# Reranking configuration (controlled by supervisor logic)
enable_reranking = bool(llm_provider and llm_model)
```

---

## How It Works

### 1. Load Agent Configuration
```python
agent_config = agent_service.get_agent(conversation.agent_id, user_id)
```

### 2. Extract Embedding Details
```python
embedding_provider_id = agent_config.vector_database.embedding_provider.id
embedding_model_name = agent_config.vector_database.embedding_provider.model_name
vector_dimension = agent_config.vector_database.vector_dimension
```

### 3. Extract LLM Details
```python
llm_provider = agent_config.llm_provider.id
llm_model = agent_config.llm_provider.model_name
```

### 4. Determine Reranking
```python
enable_reranking = bool(llm_provider and llm_model)
# True if agent has LLM provider configured
# False if agent doesn't have LLM provider
```

### 5. Include in System Prompt
```python
system_prompt += f"""
## MCP Tool Parameters...
- enable_reranking: {str(enable_reranking).lower()}
- llm_provider_id: "{llm_provider}"
- llm_model_name: "{llm_model}"
...
"""
```

---

## Assistant Behavior

When the assistant is initialized, it receives all required parameters in the system prompt. This allows it to:

1. **Know what embedding configuration to use**
   - Embedding provider ID, model name, and vector dimension
   - Used for vector search in the knowledge base

2. **Know whether reranking is enabled**
   - If `enable_reranking: true` → provide LLM parameters
   - If `enable_reranking: false` → don't provide LLM parameters

3. **Know what LLM to use for reranking**
   - If reranking enabled → use the provided LLM provider
   - Used to rank documents by relevance

4. **Know the context for calls**
   - Collection name, user ID, conversation ID
   - Top-K value for document retrieval

---

## Safeguards & Fallbacks

### If No Vector Database
```python
collection_name = "LongTermMemory"
vector_dimension = 1536
embedding_provider_id = ""
embedding_model_name = ""
```

### If No LLM Provider
```python
llm_provider = ""
llm_model = ""
enable_reranking = False  # Reranking disabled
```

### If No Agent Config
```python
logger.warning(f"No agent found for conversation {conversation_id}, using default context")
# System prompt won't have MCP tool parameters section
```

---

## Files Modified

- ✅ `src/agents/assistant_agent/factory.py` - Updated system prompt generation

---

## Verification

All files compile successfully:
- ✅ assistant_agent/factory.py
- ✅ rag_agent/mcp/server.py
- ✅ rag_agent/mcp/tools.py
- ✅ rag_agent/nodes/document_retriever.py
- ✅ rag_agent/tools/retriever_tool.py

---

## Integration with MCP Tool

The system prompt now provides the assistant with all parameters needed for the `knowledge_expert` MCP tool:

```python
# Assistant receives this in system prompt, then calls:
await mcp_client.knowledge_expert(
    search_query=["variant1", "variant2", "variant3", "variant4", "variant5"],
    collection_name="MyCollection",                    # From system prompt
    user_id="user-123",                                # From system prompt
    embedding_provider_id="provider-456",              # From system prompt
    embedding_model_name="text-embedding-3",           # From system prompt
    vector_dimension=1536,                             # From system prompt
    enable_reranking=True,                             # From system prompt
    llm_provider_id="llm-789",                         # From system prompt
    llm_model_name="gpt-4",                            # From system prompt
    conversation_id="conv-456",                        # From system prompt
    top_k=5,                                           # From system prompt
)
```

---

## Next Steps

The assistant agent is now properly configured to call the MCP RAG tool with:

1. ✅ Embedding configuration (required)
2. ✅ Reranking flag (explicit control)
3. ✅ LLM configuration (for reranking)
4. ✅ All contextual information needed

The agent can generate appropriate queries and call the tool correctly with all required parameters.

---

## Summary

**Problem:** Assistant agent factory was referencing old agent structure and missing embedding/reranking parameters.

**Solution:** Updated factory to extract embedding and LLM config from the new agent structure and include comprehensive MCP tool parameters in system prompt.

**Result:** Assistant agents now have complete information to call MCP RAG tools correctly.

---

**Status:** ✅ Complete
**Compilation:** ✅ All files compile successfully
**Ready for Testing:** ✅ Yes

*Generated: 2025-12-18*
