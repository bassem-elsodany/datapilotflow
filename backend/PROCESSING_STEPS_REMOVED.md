# Removed Unused `processing_steps` Tracking

## Problem

The RAG agent nodes were trying to append to `state["processing_steps"]`, which caused a `KeyError` when the RAG agent was called from the supervisor.

### Error Log:
```
KeyError: 'processing_steps'
  File "src/agents/rag_agent/nodes/document_retriever.py", line 30
    state["processing_steps"].append("document_retrieval")
```

## Investigation

Found that `processing_steps` was:
- ✅ Defined in `RAGWorkflowState` as a required field
- ✅ Appended to in 4 nodes:
  - `document_retriever.py`
  - `document_judger.py`
  - `answer_generator.py`
  - `raw_response_formatter.py`
- ❌ **NEVER actually read or used anywhere**

It was just legacy tracking metadata with no functional purpose.

## Solution

**Removed all `processing_steps` tracking** to fix supervisor integration:

### Files Modified:

1. ✅ `src/agents/rag_agent/nodes/document_retriever.py`
   - Removed lines 30-32: `processing_steps` append

2. ✅ `src/agents/rag_agent/nodes/document_judger.py`
   - Removed line 97: `processing_steps` append

3. ✅ `src/agents/rag_agent/nodes/answer_generator.py`
   - Removed line 28: `processing_steps` append

4. ✅ `src/agents/rag_agent/nodes/raw_response_formatter.py`
   - Removed line 27: `processing_steps` append

5. ✅ `src/agents/rag_agent/state.py`
   - Made `processing_steps` optional: `Optional[List[str]]`
   - Added comment: "Legacy field, no longer used"
   - Made `errors` optional too for consistency

## Benefits

1. ✅ **Fixes KeyError** - No more crashes when RAG agent called from supervisor
2. ✅ **Cleaner Code** - Removed unused tracking logic
3. ✅ **Better Compatibility** - RAG agent works with any state structure
4. ✅ **Simplified Maintenance** - Less code to maintain

## Why `processing_steps` Wasn't Needed

- **Not used for control flow** - Doesn't affect workflow decisions
- **Not used for output** - Doesn't appear in responses
- **Not used for debugging** - Node logs already show execution order
- **Not used for monitoring** - Better tracking via proper logging

The workflow execution order is already clear from:
- Node start/finish logs: `🚀 [NODE START] document_retriever`
- Supervisor routing events: `🔄 Supervisor routing to: rag_expert`
- Progress events: `workflow_progress` with stage names

## Impact

- ✅ No breaking changes - field still exists (optional)
- ✅ Backward compatible - existing code won't break
- ✅ Forward compatible - supervisor integration now works
- ✅ No functional changes - only removed unused metadata

## Testing

To verify the fix:

```bash
# Send query through supervisor mode
# Should now see:
✅ RAG agent executes without KeyError
✅ All nodes complete successfully
✅ No "processing_steps" errors in logs
```

