# Guide: How to Get LLM to Call Multiple Tools

## The Issue

When you bind multiple tools, the LLM intelligently selects the MOST appropriate one for the query. For single-task requests, this is correct and efficient.

**Current behavior:**
```
User: "Create an HTTP listener flow"
→ LLM selects: mulesoft_flow_generator
→ Result: ✅ Flow generated (single tool)
```

**What you might want:**
```
User: "Create an HTTP listener flow"
→ LLM selects: mulesoft_get_flow_examples + mulesoft_flow_generator
→ Result: ✅ Examples retrieved, then flow generated (multiple tools)
```

---

## Strategy 1: Ask LLM Explicitly (Easiest)

### How It Works
Update the system prompt to encourage multi-tool workflows.

### Example Update to supervisor_prompts.py

Add this to STEP 4 (Tool Selection):

```python
**STEP 4️⃣: DECIDE WHICH TOOLS TO USE**

For generation tasks, consider using MULTIPLE tools:
- If task involves error handling → Call mulesoft_get_error_handling_examples FIRST
- If task involves data transformation → Call mulesoft_get_dataweave_examples FIRST
- If task involves configuration → Call mulesoft_get_configuration_examples FIRST
- Then call mulesoft_flow_generator with the enriched knowledge

This multi-step approach ensures the generator has specific, concrete examples
as reference material, leading to better results.
```

### Test Query
```
"Create an HTTP listener flow with proper error handling"
```

### Expected LLM Behavior
LLM sees "error handling" and follows:
1. Call mulesoft_get_error_handling_examples
2. Accumulate knowledge
3. Call mulesoft_flow_generator with enriched context

### Pros & Cons
- ✅ Simple: Just update prompt
- ✅ Explicit: Clear instructions
- ❌ May not always work: LLM might still choose efficiency over thoroughness
- ❌ Requires prompt tuning

---

## Strategy 2: Tool Naming & Descriptions (Medium)

### How It Works
Make tool descriptions more compelling so LLM wants to call them.

### Update Tool Descriptions

**Current (gets skipped):**
```
mulesoft_get_error_handling_examples: "Get error handling examples"
```

**Better (encourages usage):**
```
mulesoft_get_error_handling_examples: "Get concrete error handling code examples.
IMPORTANT: Call this FIRST if user asks about error handling.
Contains production-ready error catching patterns.
Use BEFORE generating flows with error handling."
```

### Where to Update
File: `src/agents/assistant_agent/tools/tool_factory.py`

Look for tool description definitions and add priority language.

### Pros & Cons
- ✅ Medium effort
- ✅ Works well with good prompt engineering
- ❌ Requires updating each tool definition
- ❌ Still subject to LLM judgment

---

## Strategy 3: Restructure Tools (Best Long-Term)

### How It Works
Make helper tools conditions for the generator, not separate tools.

### Before (Current)
```
Available Tools:
  - mulesoft_flow_generator
  - mulesoft_get_error_handling_examples
  - mulesoft_get_dataweave_examples
  - mulesoft_get_configuration_examples
```

### After (Recommended)
```
Available Tools:
  - mulesoft_flow_generator_with_error_handling
  - mulesoft_flow_generator_with_dataweave
  - mulesoft_flow_generator_with_configuration
  - mulesoft_flow_generator_advanced (combines all)
```

OR

```
Available Tools:
  - mulesoft_flow_generator (smart enough to call internal helpers)
  - mulesoft_get_flow_examples (reference only)
  - mulesoft_analyze_flow (validation)
```

### Implementation
Modify `tool_factory.py` to:
1. Create specialized generator variants
2. OR make generator smart enough to call helpers internally
3. OR reduce number of available tools (only offer relevant ones)

### Pros & Cons
- ✅ Clean architecture
- ✅ Reduces cognitive load on LLM
- ✅ Guarantees multi-step workflows when needed
- ❌ Requires code changes
- ❌ More complex to maintain

---

## Strategy 4: Query Rewriting (Advanced)

### How It Works
Intercept user queries and expand them to encourage multi-tool usage.

### Example

**Before:**
```
User: "Create a flow with error handling"
```

**After (rewritten):**
```
User: "First get error handling examples. Then create a flow with error handling"
```

### Implementation

Add a pre-processing step in `supervisor_websocket_router.py`:

```python
def expand_query_for_tools(query: str) -> str:
    """Expand user query to encourage multi-tool workflows."""

    expansion_rules = {
        "error handling": "First get error handling examples. Then ",
        "dataweave": "First get DataWeave transformation examples. Then ",
        "configuration": "First get configuration best practices. Then ",
    }

    for keyword, expansion in expansion_rules.items():
        if keyword.lower() in query.lower() and "get" not in query.lower():
            query = expansion + query

    return query
```

### Pros & Cons
- ✅ Non-invasive to LLM
- ✅ Guaranteed multi-tool workflow
- ❌ Changes user intent
- ❌ Complex to maintain rules
- ❌ Adds latency

---

## Strategy 5: Tool Calling Middleware (Most Control)

### How It Works
Force certain tools to always be called in specific sequences.

### Implementation

Create a tool orchestrator middleware:

```python
class MultiToolOrchestrator:
    """Orchestrate multiple tool calls in sequence."""

    TOOL_SEQUENCES = {
        "error_handling": [
            "mulesoft_get_error_handling_examples",
            "mulesoft_flow_generator"
        ],
        "dataweave": [
            "mulesoft_get_dataweave_examples",
            "mulesoft_flow_generator"
        ],
        "advanced": [
            "mulesoft_get_flow_examples",
            "mulesoft_get_error_handling_examples",
            "mulesoft_get_configuration_examples",
            "mulesoft_flow_generator"
        ]
    }

    def should_use_sequence(self, query: str) -> str:
        """Determine which sequence to use."""
        if "error handling" in query.lower():
            return "error_handling"
        elif "dataweave" in query.lower():
            return "dataweave"
        elif "complete" in query.lower() or "full" in query.lower():
            return "advanced"
        return None

    def execute_sequence(self, query: str, tools: Dict):
        """Execute tools in sequence."""
        sequence = self.should_use_sequence(query)
        if not sequence:
            return None  # Let LLM decide

        results = {}
        for tool_name in self.TOOL_SEQUENCES[sequence]:
            tool = tools[tool_name]
            results[tool_name] = tool.invoke(query)

        return results
```

### Pros & Cons
- ✅ Full control
- ✅ Predictable behavior
- ✅ Guaranteed sequences
- ❌ Most complex
- ❌ Removes LLM intelligence
- ❌ Requires matching user queries to sequences

---

## Strategy 6: Update System Prompt (Recommended Short-Term)

### The Fix

Add to STEP 2.5 in supervisor_prompts.py:

```python
**TOOL SELECTION STRATEGY:**

You have access to specialized tools. Here's how to use them:

**Pattern 1: Simple Generation (User only asks for one thing)**
→ Call knowledge_expert for context
→ Call 1 appropriate generation tool
→ Return result

**Pattern 2: Generation with Specific Knowledge (User mentions specific aspects)**
→ Call knowledge_expert for general context
→ IF user mentions "error handling" → Call mulesoft_get_error_handling_examples
→ IF user mentions "dataweave" → Call mulesoft_get_dataweave_examples
→ IF user mentions "configuration" → Call mulesoft_get_configuration_examples
→ Call mulesoft_flow_generator with accumulated knowledge
→ Return result

**Pattern 3: Comprehensive Generation (User asks for "complete", "production-ready", "full")**
→ Call knowledge_expert
→ Call mulesoft_get_flow_examples
→ Call mulesoft_get_error_handling_examples
→ Call mulesoft_get_configuration_examples
→ Call mulesoft_flow_generator
→ Return result

**Decision Rule:**
If specialized knowledge is requested/helpful, retrieve it BEFORE generation.
If only general generation is needed, proceed directly to generator.
```

### Implementation
Update `src/agents/common/prompts/supervisor_prompts.py` STEP 5 section

### Test Queries
```
"Create a complete HTTP listener flow with error handling and configuration"
→ Expected: All 4 helper tools + generator

"Create a flow with DataWeave transformations"
→ Expected: mulesoft_get_dataweave_examples + generator

"Create a simple flow"
→ Expected: Only generator (single tool)
```

---

## Comparison Table

| Strategy | Effort | Effectiveness | LLM Control | Recommended |
|----------|--------|----------------|-------------|-------------|
| 1. Prompt Update | Low | 70% | Yes | ⭐⭐⭐ Short-term |
| 2. Tool Descriptions | Low | 60% | Yes | ⭐⭐ Supplement |
| 3. Restructure Tools | High | 95% | No | ⭐⭐⭐⭐ Long-term |
| 4. Query Rewriting | Medium | 90% | No | ⚠️ Use carefully |
| 5. Middleware | High | 100% | No | ⭐⭐⭐⭐⭐ For workflows |
| 6. Prompt + Rules | Medium | 80% | Yes | ⭐⭐⭐ Best Balance |

---

## Quick Implementation: Strategy 6 (Recommended)

### Step 1: Update Prompt
Add the tool selection pattern above to `supervisor_prompts.py`

### Step 2: Test
```bash
Query 1: "Create a flow with error handling"
Query 2: "Generate a complete HTTP listener flow"
Query 3: "Simple flow"
```

### Step 3: Monitor
Check logs to see if tools are being called in expected sequences:
```bash
grep "Tool executing\|mulesoft_get" /Users/bassem.elsodany/workspaces/datapilotflow/backend/logs/datapilotflow.log
```

### Step 4: Refine
If LLM doesn't follow patterns:
- Add more explicit rules in prompt
- Use Strategy 5 (middleware) for guaranteed sequences
- Consider Strategy 3 (restructure) for long-term

---

## Logging to Monitor Tool Usage

Add logging to track which tools are called:

```python
# In generate_response_supervisor.py, around line 837
if event_type == "on_tool_start":
    tool_name = event_data.get("tool", {}).get("name", "")
    logger.info(f"🔧 TOOL CALL START: {tool_name}")

if event_type == "on_tool_end":
    tool_name = event_data.get("tool", {}).get("name", "")
    logger.info(f"✅ TOOL CALL END: {tool_name}")
```

Then grep logs:
```bash
grep "TOOL CALL" logs/datapilotflow.log
```

---

## Summary

**Why only one tool is called:** LLM is making intelligent decisions ✅

**To call multiple tools, you can:**
1. **Short-term**: Update system prompt (Strategy 6) ⭐⭐⭐
2. **Medium-term**: Combine strategies 1 + 2 + tool descriptions
3. **Long-term**: Restructure tools (Strategy 3) ⭐⭐⭐⭐

Start with **Strategy 6** (prompt update) - low effort, good results, preserves LLM intelligence.
