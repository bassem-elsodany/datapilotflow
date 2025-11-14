# Test Multi-Tool Behavior - Updated Prompt

## What Changed

**Supervisor Prompt UPDATED** to force LLM to check and use multiple tools.

**Location:** `src/agents/common/prompts/supervisor_prompts.py` STEP 5

**Key Changes:**
- ✅ Added mandatory tool selection logic
- ✅ LLM MUST check for helper tools before execution
- ✅ LLM MUST call helper tools if they match user's request
- ✅ LLM MUST accumulate knowledge from multiple tools
- ✅ Explicit examples showing multi-tool execution patterns

---

## Test Queries to Trigger Multi-Tool Behavior

### Test 1: Error Handling Request (Should call error handling tool + generator)

```
Query: "Create HTTP listener flow with error handling"

Expected Behavior:
  1. knowledge_expert called (RAG retrieval) ✅
  2. mulesoft_get_error_handling_examples called ✅
  3. mulesoft_flow_generator called ✅

Verify in Logs:
  grep "Tool.*executing\|mulesoft_" logs/datapilotflow.log | tail -20

Should see:
  - Tool 'mulesoft_get_error_handling_examples' executing
  - Tool 'mulesoft_flow_generator' executing
```

### Test 2: Configuration Request (Should call configuration tool + generator)

```
Query: "Generate flow with proper configuration and security settings"

Expected Behavior:
  1. knowledge_expert called ✅
  2. mulesoft_get_configuration_examples called ✅
  3. mulesoft_flow_generator called ✅

Verify in Logs:
  grep "mulesoft_" logs/datapilotflow.log | grep -E "(configuration|flow_generator)" | tail -5
```

### Test 3: DataWeave Request (Should call dataweave tool + generator)

```
Query: "Create flow that transforms data using DataWeave"

Expected Behavior:
  1. knowledge_expert called ✅
  2. mulesoft_get_dataweave_examples called ✅
  3. mulesoft_flow_generator called ✅

Verify in Logs:
  grep "dataweave\|flow_generator" logs/datapilotflow.log
```

### Test 4: Production-Ready Request (Should call ALL helper tools + generator)

```
Query: "Generate a production-ready flow with error handling, validation, and configuration"

Expected Behavior:
  1. knowledge_expert called ✅
  2. mulesoft_get_error_handling_examples called ✅
  3. mulesoft_get_configuration_examples called ✅
  4. mulesoft_get_flow_examples called ✅
  5. mulesoft_flow_generator called ✅

Verify in Logs:
  grep "Tool.*executing" logs/datapilotflow.log | tail -10

Should see all 4 helper tools + generator
```

### Test 5: Simple Request (Should call only generator - efficient)

```
Query: "Create simple HTTP listener flow"

Expected Behavior:
  1. knowledge_expert called ✅
  2. mulesoft_flow_generator called ✅
  (No helper tools needed for simple task)

Verify in Logs:
  grep "Tool.*executing" logs/datapilotflow.log | wc -l
  Should be 2 tools (RAG + generator)
```

---

## How to Run Tests

### Option 1: Via WebSocket (Real-time Testing)

1. Open WebSocket connection to your supervisor agent
2. Send test queries one by one
3. Monitor logs in real-time:

```bash
tail -f /Users/bassem.elsodany/workspaces/datapilotflow/backend/logs/datapilotflow.log | \
  grep -E "Tool.*executing|mulesoft_"
```

### Option 2: Via API with Curl

```bash
# Test 1: Error Handling
curl -X POST http://localhost:8000/ws/agent/query/supervisor \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Create HTTP listener flow with error handling",
    "conversation_id": "test-123"
  }'

# Monitor logs
grep "Tool.*executing" logs/datapilotflow.log | tail -5
```

### Option 3: Check Logs After Query

```bash
# After each query, check which tools were executed:
tail -200 /Users/bassem.elsodany/workspaces/datapilotflow/backend/logs/datapilotflow.log | \
  grep -E "Tool.*executing|mulesoft_" | \
  grep -v "\[RAG INJECTION\]"
```

---

## Verification Checklist

After running tests, verify:

### For Multi-Tool Queries:
- [ ] RAG tool (knowledge_expert) was called first
- [ ] Helper tool(s) called matching user's request
- [ ] Main generator tool called with accumulated context
- [ ] Multiple tools visible in logs

Example log output:
```
Tool 'knowledge_expert' executing
Tool 'mulesoft_get_error_handling_examples' executing
Tool 'mulesoft_flow_generator' executing
```

### For Simple Queries:
- [ ] Only relevant tools called (no unnecessary helpers)
- [ ] Execution efficient (fewer tool calls)
- [ ] Result still high quality

### Context Verification:
- [ ] Each tool received RAG context (18,000+ chars)
- [ ] Helper tools accumulated knowledge
- [ ] Generator received complete context

---

## Log Grep Commands

### See All Tool Calls:
```bash
grep "Tool.*executing" logs/datapilotflow.log
```

### See Specific Tool Execution:
```bash
grep "mulesoft_" logs/datapilotflow.log | grep -v "\[RAG INJECTION\]"
```

### See Tool Execution Timeline:
```bash
grep "Tool.*executing\|Tool.*completed" logs/datapilotflow.log | tail -20
```

### Count Tools Called:
```bash
grep "Tool.*executing" logs/datapilotflow.log | wc -l
```

### See Context Injection:
```bash
grep "Injected.*chars of RAG context" logs/datapilotflow.log
```

---

## Expected Results

### BEFORE (Old Prompt):
```
Query: "Create flow with error handling"

Tool Calls:
  1. knowledge_expert ✅
  2. mulesoft_flow_generator ✅

Total: 2 tools (efficient but missing error handling examples)
```

### AFTER (New Prompt - This Fix):
```
Query: "Create flow with error handling"

Tool Calls:
  1. knowledge_expert ✅
  2. mulesoft_get_error_handling_examples ✅ (NEW!)
  3. mulesoft_flow_generator ✅

Total: 3 tools (comprehensive with specific error handling patterns)

Result Quality: BETTER (error handling specifically addressed)
```

---

## Troubleshooting

### Issue: Still only 1 tool called

**Possible Causes:**
1. Prompt not reloaded (agent cached old prompt)
2. Query too simple (no matching helper tools)
3. LLM not following new instructions

**Solutions:**
1. Restart agent/server to force prompt reload
2. Use complex query: "Create production-ready flow with error handling"
3. Check if LLM model is strong enough to follow complex instructions
4. Verify prompt file was actually saved

**Verify Prompt Updated:**
```bash
grep "MANDATORY TOOL SELECTION LOGIC" src/agents/common/prompts/supervisor_prompts.py
```

Should see: Yes (if it returns the text, prompt is updated)

### Issue: Too many tools called for simple query

**Expected Behavior:**
Simple queries should still use only 1-2 tools efficiently.

**This is CORRECT** - LLM is making intelligent decisions:
- Simple query → 1 tool
- Complex query → Multiple tools
- Production query → All available tools

### Issue: Error in tool execution

**Check:**
1. Are all tools available?
   ```bash
   grep "Loaded active tool\|Added MCP remote tool" logs/datapilotflow.log | wc -l
   ```
   Should be 5 (or more)

2. Do tools have valid descriptions?
   Check tool database

3. Are tools receiving context?
   ```bash
   grep "Injected.*chars" logs/datapilotflow.log
   ```

---

## Success Criteria

✅ **You'll know it's working when:**

1. **Query with "error handling"** → Calls error_handling tool
2. **Query with "configuration"** → Calls configuration tool
3. **Query with "complete/production"** → Calls multiple tools
4. **Query "simple"** → Still efficient with minimal tools
5. **Logs show multiple "Tool executing"** entries
6. **Each tool receives 18,000+ chars context**
7. **Final result is higher quality** with specific knowledge

---

## Next Steps After Testing

### If Multi-Tool Behavior Works ✅:
1. Verify results are higher quality
2. Compare with old single-tool behavior
3. Measure performance impact
4. Consider if trade-offs are worth it

### If Multi-Tool Behavior Doesn't Work ⚠️:
1. Try restarting the agent
2. Check if prompt was actually updated
3. Try more explicit keywords in queries
4. Consider implementing middleware solution (Strategy 5)

### Fine-Tuning:
1. Add more specific tool recommendations in prompt
2. Enhance tool descriptions to be more compelling
3. Add tool aliases (e.g., "error patterns" → error_handling_tool)
4. Consider tool dependency rules

---

## Real-World Example

### User Query:
```
"Generate a MuleSoft flow that:
1. Receives HTTP requests
2. Validates the input
3. Handles errors properly
4. Transforms data with DataWeave
5. Is production-ready"
```

### Expected Behavior With Updated Prompt:

```
Step 1: RAG Agent
  → Called with 5 variants
  → Retrieved 10 documents
  → Injected 18,742 chars context

Step 2: Tool Analysis
  → User mentions: "HTTP" (basic), "validation", "errors", "DataWeave", "production"
  → Relevant tools: error_handling, dataweave, configuration, generator

Step 3: Multi-Tool Execution
  → Call mulesoft_get_error_handling_examples (error patterns)
  → Call mulesoft_get_dataweave_examples (transformation patterns)
  → Call mulesoft_get_configuration_examples (production config)
  → Accumulate knowledge
  → Call mulesoft_flow_generator with ALL context

Result: Production-ready flow with proper error handling + validation + DataWeave
```

---

## Performance Notes

**Trade-offs:**

| Aspect | Single Tool | Multi-Tool |
|--------|------------|-----------|
| Speed | Faster | Slower (multiple calls) |
| Quality | Good | Better |
| Context | RAG only | RAG + tools |
| Coverage | Basic | Comprehensive |

**Conclusion:** For important queries, multi-tool is worth the extra time.

---

## Revert If Needed

If multi-tool behavior causes issues:

```bash
# Revert to simple tool selection by commenting out the new STEP 5
# in supervisor_prompts.py

# Or restore from git:
git checkout src/agents/common/prompts/supervisor_prompts.py
```

---

## Questions?

Check these files:
- TOOL_SELECTION_ANALYSIS.md - Why single tool before
- MULTI_TOOL_USAGE_GUIDE.md - Various implementation strategies
- supervisor_prompts.py - See actual prompt changes

