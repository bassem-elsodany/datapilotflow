# Real-Time Workflow Visualization - Implementation Summary

## Overview
Added a real-time workflow visualization panel that shows the current LangGraph execution state in the conversation window.

---

## Frontend Changes (`dashboard/src/pages/dashboard/apps/knowledge/conversation-window.tsx`)

### 1. Layout Structure
```
┌─────────────────────────────────────────────┐
│          Header (Fixed)                      │
├───────────────────────┬─────────────────────┤
│ Left Column (flex: 1) │ Right Column (400px)│
│                       │                      │
│ ┌───────────────────┐ │ ┌─────────────────┐ │
│ │ ScrollArea        │ │ │ Workflow Panel  │ │
│ │ (Messages)        │ │ │ (No Scroll)     │ │
│ │ - Auto scroll     │ │ │ - Always visible│ │
│ │ - Visible scrollbar│ │ │ - Replaces each │ │
│ └───────────────────┘ │ │   query         │ │
│                       │ └─────────────────┘ │
├───────────────────────┴─────────────────────┤
│          Input Area (Fixed)                  │
└─────────────────────────────────────────────┘
```

### 2. State Management
Added `workflowState` to track:
- `currentNode`: Current LangGraph node executing
- `completedNodes`: Array of finished nodes
- `originalQuery`: User's input query
- `transformedQuery`: Enhanced query (if strategy applied)
- `strategy`: Selected enhancement strategy
- `documentCount`: Number of retrieved documents
- `isActive`: Whether workflow is currently running

### 3. WebSocket Message Handlers
Updated handlers for:
- `workflow_started`: Initialize workflow state
- `query_enhancement`: Track query transformation
- `document_retrieval`: Track document count
- `document_reranking`: Track reranking progress
- `response_generation`: Track final generation
- `completed`: Reset workflow state

### 4. Workflow Visualization Components
**Always Visible Right Panel:**
- Header with "Workflow Pipeline" title
- Active badge when workflow is running
- Empty state when no query sent

**Query Display:**
- Original query card (user input)
- Transformed query card (if strategy applied, highlighted in blue)

**Pipeline Steps (Dynamic):**
1. **Query Enhancement** (conditional - only if strategy ≠ 'native')
   - Shows strategy name
   - Current: Blue background + spinner
   - Complete: Green background + checkmark

2. **Document Retrieval** (always shown)
   - Shows document count when retrieved
   - Current: Blue background + spinner
   - Complete: Green background + checkmark

3. **Document Reranking** (conditional - only if reranking enabled)
   - Shows reranking progress
   - Current: Blue background + spinner
   - Complete: Green background + checkmark

4. **Response Generation** (always shown)
   - Shows LLM generation progress
   - Current: Blue background + spinner
   - Complete: Green background + checkmark

### 5. Auto-Scroll Fix
**Problem:** `scrollIntoView()` was scrolling the entire page
**Solution:** Only scroll the ScrollArea viewport
```tsx
const viewport = scrollAreaRef.current.querySelector('.mantine-ScrollArea-viewport');
if (viewport) {
  viewport.scrollTop = viewport.scrollHeight;
}
```

### 6. Layout Constraints
- Root container: `height: '100%'`, `overflow: 'hidden'`
- Left column: `flex: 1`, has ScrollArea with visible scrollbar
- Right column: `width: '400px'`, NO scroll, `overflow: 'hidden'`
- Prevents any page-level scrolling

---

## Backend Changes (`backend/src/api/routers/agent/agent_websocket_router.py`)

### Enhanced WebSocket Messages
Added to stage updates:
```python
stage_data = {
    "node": current_node,
    "description": info["description"],
    "execution_time_ms": chunk.get("execution_time_ms", 0),
}

# Include enhanced query if available
if chunk.get("enhanced_query"):
    stage_data["enhanced_query"] = chunk["enhanced_query"]

# Include document count if available
if chunk.get("retrieved_documents"):
    stage_data["document_count"] = len(chunk["retrieved_documents"])
```

---

## Prompt Improvements (`backend/src/workflow/prompts/generation_prompts.py`)

### Strict Context-Only Prompts
Added **CRITICAL RULES** to prevent hallucination:
1. **ONLY USE PROVIDED CONTEXT**: Cannot use external knowledge
2. **NO HALLUCINATION**: Must say "I cannot answer" if context insufficient
3. **VERIFY BEFORE ANSWERING**: Check context before generating
4. **STAY IN SCOPE**: Reject out-of-domain questions with helpful message

### Out-of-Scope Response Format
```
I cannot find information about [topic] in the available knowledge base.

The retrieved documents appear to be about [actual content], which doesn't match your question.

**Please:**
- Rephrase your question to align with the knowledge base content
- Or verify that the correct vector database/collection is selected
- Or upload documents related to [topic] first

**Available topics in this knowledge base:** [inferred topics]
```

### Jinja2 Template Fixes
Changed all prompts from `{variable}` to `{{ variable }}` syntax:
- `generation_prompts.py`
- `judge_prompts.py`
- `step_back_prompts.py`
- `hyde_prompts.py`
- `multi_query_prompts.py`
- `decomposition_prompts.py`
- `rag_fusion_prompts.py`

---

## Key Features

### ✅ Real-Time Visualization
- Shows current LangGraph node being executed
- Updates in real-time via WebSocket
- Visual progress indicators (spinner for current, checkmark for complete)

### ✅ Query Transformation Display
- Shows original user query
- Shows transformed query (if enhancement strategy used)
- Displays strategy name

### ✅ Conditional Rendering
- Query enhancement step: Only shows if strategy ≠ 'native'
- Reranking step: Only shows if reranking is enabled
- Adapts to conversation configuration

### ✅ Independent Scrolling
- Left column: Scrolls messages with visible scrollbar
- Right column: No scroll, always visible
- Page: No scroll at all

### ✅ Context-Only Responses
- LLM strictly limited to retrieved documents
- Rejects out-of-domain questions gracefully
- Provides helpful guidance when context is insufficient

---

## Testing Checklist

### Layout
- [ ] Left column scrolls independently with visible scrollbar
- [ ] Right column always visible, no scroll
- [ ] No page-level scrolling
- [ ] Input area fixed at bottom
- [ ] Header fixed at top

### Workflow Visualization
- [ ] Right panel shows "Send a query" initially
- [ ] Panel updates when query is sent
- [ ] Current node shows blue background + spinner
- [ ] Completed nodes show green background + checkmark
- [ ] Query transformation displayed correctly
- [ ] Document count shown when retrieved
- [ ] Steps adapt to conversation config (strategy, reranking)

### Auto-Scroll
- [ ] Left column auto-scrolls to bottom on new messages
- [ ] Right column stays at top (no scroll)
- [ ] Page doesn't scroll

### Context Handling
- [ ] LLM answers from context correctly
- [ ] Out-of-domain questions get helpful rejection message
- [ ] Empty context handled gracefully
- [ ] Markdown renders properly in UI

---

## Known Issues
None at this time.

---

## Files Modified

### Frontend
- `dashboard/src/pages/dashboard/apps/knowledge/conversation-window.tsx`
- `dashboard/src/components/streaming-message.tsx`

### Backend
- `backend/src/api/routers/agent/agent_websocket_router.py`
- `backend/src/workflow/prompts/generation_prompts.py`
- `backend/src/workflow/prompts/judge_prompts.py`
- `backend/src/workflow/prompts/step_back_prompts.py`
- `backend/src/workflow/prompts/hyde_prompts.py`
- `backend/src/workflow/prompts/multi_query_prompts.py`
- `backend/src/workflow/prompts/decomposition_prompts.py`
- `backend/src/workflow/prompts/rag_fusion_prompts.py`
- `backend/src/workflow/nodes/answer_generator.py`

---

## Next Steps
1. Restart dashboard dev server
2. Navigate to conversation window
3. Send a query
4. Verify workflow visualization appears and updates in real-time
5. Verify scrolling behavior is correct

