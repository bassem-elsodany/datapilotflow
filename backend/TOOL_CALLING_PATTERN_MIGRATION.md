# Tool Calling Pattern Migration

**Date**: November 7, 2025  
**Status**: ✅ Complete

## Summary

Migrated from the deprecated `langgraph-supervisor` library to the **official LangChain Tool Calling Pattern** as recommended in the [official multi-agent documentation](https://docs.langchain.com/oss/python/langchain/multi-agent).

---

## What Changed

### ❌ **OLD Architecture** (langgraph-supervisor library)

```
User Query
    ↓
[langgraph-supervisor] (library-managed orchestration)
    ├─ rag_expert (RAG workflow) ← KeyError: 'messages'
    └─ task_expert (ReAct agent)
```

**Problems:**
- `langgraph-supervisor` is **deprecated** by LangChain
- Library expects **message-based state** format
- RAG agent uses **custom TypedDict state**
- **Incompatible** → `KeyError: 'messages'`
- Missing `user_id` and config in invocations

### ✅ **NEW Architecture** (Tool Calling Pattern)

```
User Query
    ↓
[Main ReAct Agent] (create_react_agent)
    ↓
Tools available:
    • retrieve_knowledge (RAG agent wrapped as tool)
    • python_code_generator
    • code_explainer
    • task_planner
    • calculator
    • text_analyzer
    ↓
[Final Response]
```

**Benefits:**
- ✅ **Official LangChain recommended pattern**
- ✅ RAG agent **completely unchanged** (custom state intact)
- ✅ Proper config passing (user_id, collection_name, etc.)
- ✅ Natural RAG-first execution
- ✅ Full control over context engineering
- ✅ Simpler architecture, fewer dependencies

---

## Technical Details

### RAG Tool Wrapper

The RAG agent is wrapped as a tool using LangChain's `@tool` decorator:

```python
@tool(
    "retrieve_knowledge",
    description="Retrieves and ranks relevant documents from the knowledge base..."
)
def retrieve_knowledge_tool(
    search_query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> str:
    # Create RAG input state (custom format)
    rag_input_state = {
        "original_query": search_query,
        "conversation_id": conversation_id,
        "config": workflow_config,  # Includes user_id, collection_name, etc.
    }
    
    # Invoke RAG workflow (unchanged)
    rag_result = rag_workflow.invoke(rag_input_state)
    
    # Extract and format results
    final_answer = rag_result.get("final_answer")
    documents = rag_result.get("retrieved_documents")
    
    # Return formatted response for main agent
    return formatted_response
```

### Main Agent Creation

```python
# Get task tools
task_tools = get_task_agent_tools()

# Combine RAG tool + task tools
all_tools = [retrieve_knowledge_tool] + task_tools

# Create main ReAct agent
main_agent = create_react_agent(
    model=llm_client,
    tools=all_tools,
    state_modifier=system_prompt,
)

# Execute
async for event in main_agent.astream_events(...):
    # Process events and stream to frontend
```

### System Prompt Strategy

The main agent's system prompt explicitly instructs RAG-first execution:

```
**CRITICAL: RAG-First Execution:**
For EVERY user query:
1. Call `retrieve_knowledge` to get grounded information
2. Use the retrieved knowledge to formulate your response
3. Only use task tools if additional processing is needed
4. Never skip the knowledge retrieval step
```

---

## Files Changed

### Modified

- ✅ `/src/services/conversation/generate_response_supervisor.py`
  - Complete rewrite using Tool Calling pattern
  - Removed `langgraph-supervisor` imports
  - Created `retrieve_knowledge_tool` wrapper
  - Simplified execution logic
  - Preserved all event streaming

- ✅ `/pyproject.toml`
  - Removed `langgraph-supervisor>=0.0.30` dependency

### Deleted

- ✅ `/src/agents/supervisor_agent/` (entire folder - legacy custom supervisor)
- ✅ `/src/orchestration/` (entire folder - legacy orchestrator)
- ✅ `processing_steps` field removed from all agent states

### Unchanged

- ✅ `/src/agents/rag_agent/` - **NO CHANGES** (as requested)
- ✅ `/src/agents/task_agent/tools/` - Tools preserved
- ✅ Frontend - No changes needed (same event format)

---

## Testing Checklist

Run these tests to verify the migration:

1. **Basic RAG Query**
   ```bash
   # Test: "What is MuleSoft APIkit?"
   # Expected: retrieve_knowledge tool called, proper response
   ```

2. **Task Query**
   ```bash
   # Test: "Generate Python code for HTTP request"
   # Expected: retrieve_knowledge called first, then task tools
   ```

3. **Mixed Query**
   ```bash
   # Test: "Explain Mule 4 connectors and generate example code"
   # Expected: Both RAG and task tools used
   ```

4. **Event Streaming**
   - Verify `supervisor_progress` events emitted
   - Verify `streaming_response` with metadata
   - Verify `workflow_complete` with documents

5. **RAG Agent Internals**
   - Verify config with `user_id` passed correctly
   - Verify no `KeyError: 'messages'`
   - Verify documents retrieved and returned

---

## Migration Benefits

| Aspect | Before (langgraph-supervisor) | After (Tool Calling) |
|--------|-------------------------------|----------------------|
| **Architecture** | Library-managed, black box | Explicit, controllable |
| **RAG Agent** | Format conversion issues | Works as-is |
| **Config Passing** | Missing user_id | Properly passed |
| **Maintenance** | Deprecated library | Official pattern |
| **Dependencies** | +1 external library | Built-in LangChain |
| **Debugging** | Difficult | Transparent |
| **Flexibility** | Limited | Full control |

---

## References

- [LangChain Multi-Agent Docs](https://docs.langchain.com/oss/python/langchain/multi-agent)
- [Tool Calling Pattern Tutorial](https://docs.langchain.com/oss/python/langchain/multi-agent#tool-calling)
- [create_react_agent API](https://python.langchain.com/api_reference/langgraph/prebuilt/langgraph.prebuilt.chat_agent_executor.create_react_agent.html)

---

## Next Steps

✅ **Migration Complete** - Ready for testing and deployment!

If issues arise, the architecture is now:
1. **Simpler** - easier to debug
2. **Aligned** - with LangChain recommendations
3. **Maintainable** - no deprecated dependencies
4. **Flexible** - full control over agent interactions

