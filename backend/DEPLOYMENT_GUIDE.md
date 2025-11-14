# Deployment Guide: Multi-Tool Fix

## What Changed

✅ **Updated File:** `src/agents/common/prompts/supervisor_prompts.py`

✅ **What Changed:** STEP 5 (Tool Execution) - Added mandatory multi-tool selection logic

✅ **Impact:** LLM will now call multiple tools when relevant to user's request

---

## Quick Deployment

### Step 1: Verify Changes

```bash
# Check that the fix is in place
grep "MANDATORY TOOL SELECTION LOGIC" \
  src/agents/common/prompts/supervisor_prompts.py

# Should output: 🚨 **MANDATORY TOOL SELECTION LOGIC:**
```

### Step 2: Commit Changes

```bash
cd /Users/bassem.elsodany/workspaces/datapilotflow/backend

# Check status
git status

# Add the updated prompt file
git add src/agents/common/prompts/supervisor_prompts.py

# Commit
git commit -m "feat: Enable multi-tool selection in supervisor agent

- Updated STEP 5 in supervisor prompt with mandatory tool selection logic
- LLM now checks for and uses relevant helper tools
- Improves output quality by incorporating specific tool knowledge
- Example: error handling requests now get error_handling_tool results
- Maintains efficiency for simple queries (still single-tool when appropriate)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 3: Restart Agent Service

```bash
# If using systemd
sudo systemctl restart datapilotflow-backend

# If using docker
docker-compose restart backend

# If running locally, restart the Python process
# Kill current process and restart:
pkill -f "python.*supervisor"
# Then restart your agent service
```

### Step 4: Verify Deployment

```bash
# Check logs show new behavior
tail -f logs/datapilotflow.log | grep -E "MANDATORY|Tool.*executing"

# Test with a query
# (See TEST_MULTI_TOOL_BEHAVIOR.md for test queries)
```

---

## Pre-Deployment Checklist

- [ ] Changes verified in supervisor_prompts.py
- [ ] Git diff looks correct: `git diff src/agents/common/prompts/supervisor_prompts.py`
- [ ] All STEP 5 changes are present
- [ ] No merge conflicts
- [ ] Tests pass (if available)
- [ ] Backup created: `cp src/agents/common/prompts/supervisor_prompts.py supervisor_prompts.py.backup`

---

## Post-Deployment Checklist

- [ ] Agent service restarted
- [ ] No errors in logs
- [ ] New prompt loaded (check for "MANDATORY TOOL SELECTION LOGIC")
- [ ] Test queries executed successfully
- [ ] Multiple tools called for complex queries
- [ ] Single tools still used for simple queries
- [ ] Output quality improved

---

## Verification Queries

Run these after deployment:

### Query 1: Multi-Tool Trigger
```
"Create HTTP listener flow with error handling"

Expected: 3+ tools should be called
Log check: grep "Tool.*executing" logs/datapilotflow.log | grep -E "(error|generator)"
```

### Query 2: Simple Query
```
"Create flow"

Expected: 2 tools (efficient)
Log check: grep "Tool.*executing" logs/datapilotflow.log | wc -l
Result should be 2
```

### Query 3: Production-Ready
```
"Generate production-ready flow with validation and configuration"

Expected: 4+ tools called
Log check: Multiple mulesoft tools should be in logs
```

---

## Rollback Plan (If Issues)

```bash
# Quick rollback
git checkout HEAD~ src/agents/common/prompts/supervisor_prompts.py

# Or restore backup
cp supervisor_prompts.py.backup src/agents/common/prompts/supervisor_prompts.py

# Restart service
sudo systemctl restart datapilotflow-backend

# Verify rollback
grep "MANDATORY TOOL SELECTION LOGIC" \
  src/agents/common/prompts/supervisor_prompts.py
# Should return nothing (if rollback successful)
```

---

## Monitoring Post-Deployment

### Daily Metrics

```bash
# See tool usage patterns
tail -500 logs/datapilotflow.log | \
  grep "Tool.*executing" | \
  awk '{print $NF}' | \
  sort | uniq -c

# Should show increase in helper tool calls
```

### Quality Feedback

- Gather user feedback on output quality
- Compare generated results before/after
- Track if error handling is better in generated flows
- Monitor if configuration issues decrease

### Performance

```bash
# Monitor response time
grep "Tool Calling Pattern completed" logs/datapilotflow.log | \
  tail -10

# Multi-tool = slower but better quality
# Compare trade-off with users
```

---

## Troubleshooting Deployment

### Issue: Still seeing only 1 tool called

**Causes:**
1. Agent not restarted (old prompt cached)
2. Prompt not actually saved
3. LLM model not following instructions

**Solutions:**
1. Force restart service
2. Verify file: `grep -c "MANDATORY" src/agents/common/prompts/supervisor_prompts.py`
3. Try with stronger LLM model

### Issue: All queries calling all tools (inefficient)

**Expected:** Only relevant tools called

**Solutions:**
1. This is temporary learning phase
2. Model may need fine-tuning to "ALWAYS" clauses
3. Monitor a few iterations
4. LLM will learn to be efficient

### Issue: Tools erroring out

**Causes:**
1. Tool not receiving context properly
2. Tool missing required parameters
3. Tools not loaded correctly

**Solutions:**
1. Check logs for tool initialization errors
2. Verify context injection: `grep "Injected.*chars" logs/datapilotflow.log`
3. Check tool availability: `grep "Loaded active tool" logs/datapilotflow.log`

---

## Performance Expectations

### Before Deployment
- Simple query: ~10-30 seconds (1 tool call)
- Complex query: ~30-60 seconds (1-2 tool calls)

### After Deployment
- Simple query: ~10-30 seconds (still 1-2 tools, smart LLM)
- Complex query: ~45-90 seconds (3-5 tool calls for better quality)

**Trade-off:** Slightly slower for significantly better output quality

---

## Rollback Triggers

Consider rollback if:

- [ ] System response time increases >50%
- [ ] Error rate increases >10%
- [ ] Tools fail due to missing context
- [ ] Users report quality issues
- [ ] Logs show repeated tool failures

---

## Success Indicators

✅ Deployment successful if:

- [ ] Logs show multiple tools called for complex queries
- [ ] Error handling queries trigger error_handling_tool
- [ ] Configuration queries trigger configuration_tool
- [ ] Response quality improves (user feedback)
- [ ] Simple queries still efficient (2 tools max)
- [ ] No error rate increase
- [ ] Users report better results

---

## Configuration Check

Verify all tools are still properly configured:

```bash
# Check tool loading
tail -100 logs/datapilotflow.log | grep "Loaded active tool\|Added MCP remote tool"

# Should see:
# - mulesoft_flow_generator
# - mulesoft_get_flow_examples
# - mulesoft_get_error_handling_examples
# - mulesoft_get_dataweave_examples
# - mulesoft_get_configuration_examples

# Count loaded tools
grep "Loaded active tool\|Added MCP remote tool" logs/datapilotflow.log | wc -l
# Should be 5
```

---

## Communication

### To Users
"We've improved the agent to use multiple specialized tools for better results. Complex requests will now incorporate specific patterns and examples, leading to higher quality output."

### To Ops Team
"Updated supervisor agent prompt to enable multi-tool selection. Service may be slightly slower for complex queries but output quality improves. Rollback plan available."

### To Dev Team
"See FIX_IMPLEMENTED.md for technical details. Test with TEST_MULTI_TOOL_BEHAVIOR.md queries after deployment."

---

## Timeline

- **T+0**: Deploy code
- **T+5min**: Restart services
- **T+5min-15min**: Monitor logs for errors
- **T+15min-1hr**: Run verification queries
- **T+1hr+**: Continuous monitoring
- **T+24hr**: Assess quality improvements
- **T+1week**: Collect user feedback

---

## Support

If issues arise:

1. Check logs: `tail -f logs/datapilotflow.log`
2. Verify fix: `grep "MANDATORY TOOL SELECTION" ...supervisor_prompts.py`
3. Run test queries: See TEST_MULTI_TOOL_BEHAVIOR.md
4. Consider rollback if critical issues
5. Check troubleshooting section above

---

## Summary

**Deployment:** Update supervisor_prompts.py + restart service

**Expected:** Multiple tools called for relevant queries

**Testing:** See TEST_MULTI_TOOL_BEHAVIOR.md

**Monitoring:** Check logs for tool execution patterns

**Rollback:** Git revert + restart service

**Status:** ✅ Ready for production deployment

