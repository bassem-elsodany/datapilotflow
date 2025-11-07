# Supervisor RAG-First Routing Fix

## Problem

The supervisor was skipping the RAG agent and routing directly to the task agent, which violates the principle that **RAG is the only source of truth**.

### Example from Logs:
```
Query: "generate flow with http listener using apikit"

Actual behavior:
❌ Supervisor → Task Agent (with task_planner tool)
❌ agents_executed: []
❌ No RAG retrieval performed

Expected behavior:
✅ Supervisor → RAG Agent (retrieve context) → Task Agent (use context)
✅ agents_executed: ["rag_expert", "task_expert"]
✅ RAG knowledge used to ground the response
```

---

## Root Cause

The original supervisor prompt allowed the LLM to choose whether to use RAG based on query type:
- "If query needs information from documents → use rag_expert"
- "If query needs task execution → use task_expert"

This gave the supervisor discretion to skip RAG for "task-only" queries, which is incorrect.

---

## Solution

Updated the supervisor system prompt to **ENFORCE** RAG-first routing:

### 1. Updated Supervisor Prompt (`src/agents/common/prompts/supervisor_prompts.py`)

**NEW RULES:**

```
**CRITICAL ROUTING RULES:**
1. **ALWAYS start with rag_expert** - The knowledge base must be consulted first for every query
2. The rag_expert retrieves relevant context, documentation, and grounding information
3. After RAG retrieval, route to task_expert to process the query using the retrieved context
4. The task_expert MUST use the RAG-provided knowledge to ensure accuracy

**Workflow:**
User Query → rag_expert (retrieve knowledge) → task_expert (process with context) → Final Response
```

**Key Changes:**
- ✅ **"ALWAYS start with rag_expert"** - No exceptions
- ✅ **"MUST be consulted for EVERY query"** - Mandatory, not optional
- ✅ **"PRIMARY SOURCE OF TRUTH"** - Emphasizes importance
- ✅ Explicit workflow: RAG first, then Task Agent

### 2. Added Explicit Routing Instructions (`generate_response_supervisor.py`)

Added at runtime for each query:

```python
supervisor_prompt += """

**IMPORTANT: For this query, you MUST:**
1. First, call rag_expert to retrieve relevant knowledge from the knowledge base
2. Then, call task_expert to process the query using the retrieved context
3. Never skip the rag_expert - it is the source of truth"""
```

This reinforces the routing rules for every single query.

### 3. Added Tool Call Logging

Added detailed logging to track routing:

```python
# Log all tool calls for debugging
logger.info(f"🔧 Tool call detected: {tool_name}")
```

This helps us verify that the supervisor is following the routing rules.

---

## Expected Behavior After Fix

### Query Flow:
```
1. User Query: "generate flow with http listener using apikit"
   ↓
2. Supervisor receives query
   ↓
3. Supervisor calls rag_expert (transfer_to_rag_expert)
   ↓
4. RAG Agent:
   - Enhances query (decomposition strategy)
   - Retrieves relevant documents from knowledge base
   - Returns context about MuleSoft, APIkit, HTTP listeners
   ↓
5. Supervisor calls task_expert (transfer_to_task_expert) with RAG context
   ↓
6. Task Agent:
   - Receives RAG-retrieved knowledge
   - Uses task_planner tool with context
   - Generates response grounded in retrieved documentation
   ↓
7. Final Response: Accurate answer based on knowledge base
```

### Logs Should Show:
```
✅ 🔧 Tool call detected: transfer_to_rag_expert
✅ 🔄 Supervisor routing to: rag_expert
✅ 📊 RAG Agent: Retrieving documents...
✅ 🔧 Tool call detected: transfer_to_task_expert
✅ 🔄 Supervisor routing to: task_expert
✅ 📋 Planning task with RAG context...
✅ agents_executed: ["rag_expert", "task_expert"]
```

---

## Benefits

1. **Accuracy** - All responses grounded in knowledge base (source of truth)
2. **Consistency** - RAG always consulted, no skipping
3. **Context** - Task agent always has relevant context from RAG
4. **Auditability** - Clear routing path in logs

---

## Testing

To verify the fix:

1. **Send any query** to a supervisor-mode conversation
2. **Check logs** for routing:
   ```
   ✅ Should see: "🔄 Supervisor routing to: rag_expert" FIRST
   ✅ Should see: "🔄 Supervisor routing to: task_expert" SECOND
   ✅ agents_executed should be: ["rag_expert", "task_expert"]
   ```
3. **Verify RAG stages** are emitted:
   - query_enhancement
   - document_retrieval
   - document_judging (if enabled)
   - response_generation

---

## Files Modified

1. ✅ `src/agents/common/prompts/supervisor_prompts.py`
   - Lines 14-38: Updated routing rules to enforce RAG-first

2. ✅ `src/services/conversation/generate_response_supervisor.py`
   - Lines 182-187: Added explicit routing instructions
   - Line 250: Added tool call logging

---

## Important Notes

- **RAG is mandatory** - Every query must go through RAG first
- **No exceptions** - Even for "simple" queries, RAG provides context
- **Sequential routing** - RAG → Task Agent (never Task Agent alone)
- **Source of truth** - Knowledge base is the authoritative source

