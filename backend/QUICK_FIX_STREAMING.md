# Quick Fix - Hide Internal Reasoning from Streaming Response

## The Issue (TL;DR)

User sees internal agent thinking:
```
Document Analysis: Relevant Documents:
Coverage: ✅ Covered: HTTP Listener setup...
Gaps: Detailed error handling...
[Decision]: The HTTP Listener will be configured...
```

**Should only see the final answer**, not the internal step-by-step reasoning.

---

## Quick Fix (Copy-Paste Solution)

### Step 1: Add These Helper Functions

Add to `src/agents/assistant_agent/services/generate_response_supervisor.py` (around line 1):

```python
def _is_internal_reasoning(content: str) -> bool:
    """Hide internal agent reasoning from user."""
    markers = {
        "STEP 1:", "STEP 2:", "STEP 2.5:", "STEP 3:", "STEP 4:", "STEP 5:", "STEP 6:", "STEP 7:",
        "Document Analysis:", "Coverage Status:", "[Decision]:", "[Verification]:",
        "Requirements to verify:", "Relevant Documents:", "Gaps:", "Iteration",
    }
    return any(m in content for m in markers)
```

### Step 2: Modify Lines 808-856

**Find this code** (lines 808-856):

```python
# Stream content chunks to frontend in real-time (WHILE generating)
if (
    content_chunk
    and isinstance(content_chunk, str)
    and content_chunk.strip()
):
    # ... emit events ...
    yield {
        "type": "streaming_response",
        "chunk": content_chunk,
        ...
    }
```

**Replace with**:

```python
# Stream content chunks to frontend in real-time (WHILE generating)
if (
    content_chunk
    and isinstance(content_chunk, str)
    and content_chunk.strip()
):
    # FILTER: Hide internal reasoning, only show final answer
    if not _is_internal_reasoning(content_chunk):
        # ... emit events ...
        yield {
            "type": "streaming_response",
            "chunk": content_chunk,
            "metadata": {
                "tools_used": tools_used,
                "orchestrator_type": "tool_calling_pattern",
            },
            "execution_time_ms": (time.time() - start_time) * 1000,
        }
    else:
        logger.debug(f"[FILTERED] Hiding internal reasoning: {content_chunk[:80]}...")
```

---

## Result

**Before Fix**:
```
Document Analysis: Relevant Documents:
Document 1: Covers HTTP Listener...
Coverage: ✅ Covered...
Gaps: Detailed error...
[Decision]: The HTTP Listener will be...
✅ Final Answer
```

**After Fix**:
```
✅ Final Answer
```

---

## Testing

Send a query and verify:
- ✅ No "Document Analysis:" in response
- ✅ No "Coverage:" or "Gaps:" visible
- ✅ No "[Decision]:" markers
- ✅ Only final answer shows up

---

## File to Edit

**File**: `src/agents/assistant_agent/services/generate_response_supervisor.py`

**Lines**: 808-856 (the streaming section)

**Add**: `_is_internal_reasoning()` function at the top

---

## That's It!

This quick filter prevents internal agent thinking from leaking into user responses. The agent still thinks through all steps (STEP 1-7), but users only see the final result.
