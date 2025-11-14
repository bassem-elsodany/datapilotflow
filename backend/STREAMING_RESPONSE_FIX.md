# Streaming Response Content - Issue Analysis & Fix

## Problem Description

The LLM's internal reasoning/thinking process is being exposed in the streaming response sent to users:

```
Document Analysis: Relevant Documents:
Document 1: Covers HTTP Listener configurations and APIkit integration.
Document 10: Covers APIkit usage for creating Mule applications from API specifications.
Coverage: ✅ Covered: HTTP Listener setup (Document 1, Document 2), APIkit usage (Document 10). ❌ Gaps: Detailed error handling configurations specifically for APIkit flows...
...
[Decision]: The HTTP Listener will be configured...
...
it must be the last llm response
```

This content should NOT be visible to users - it's the agent's internal step-by-step thinking from the 7-step workflow (STEP 1, 2.5, 3, etc.).

---

## Root Cause

**File**: `src/agents/assistant_agent/services/generate_response_supervisor.py` (Lines 782-856)

**Issue**: The code streams ALL content chunks from the LLM's response without filtering:

```python
if event_type == "on_chat_model_stream":
    chunk = event_data.get("chunk", {})

    # Extract content (ANY content)
    content_chunk = chunk.content if hasattr(chunk, "content") else chunk.get("content", "")

    # Stream it directly without filtering
    if content_chunk and content_chunk.strip():
        yield {
            "type": "streaming_response",
            "chunk": content_chunk,  # <-- THIS INCLUDES THINKING/REASONING
            ...
        }
```

**Why it happens**: The LLM processes multiple steps:
1. **STEP 1** - Task analysis (thinking: "Requirements are...")
2. **STEP 2** - Knowledge retrieval (thinking: "Retrieved documents...")
3. **STEP 2.5** - Document quality assessment (thinking: "Document Analysis: ...")
4. **STEP 3** - Coverage verification (thinking: "Coverage: ...")
5. **STEP 4** - Determine action (thinking: "[Decision]:...")
6. **STEP 5** - Use tools (thinking: "Calling tool...")
7. **STEP 6** - Verify result (thinking: "Verification: ...")
8. **STEP 7** - Final response (actual answer for user)

**The streaming code captures ALL of these** and sends them to the client, when it should only send **STEP 7 content** (the final response).

---

## Solution: Filter Streaming Content

### Approach 1: Stream Only Final Response (RECOMMENDED)

**Strategy**: Only stream content AFTER the agent has completed its reasoning and is providing the final answer.

**Implementation**:

```python
# Location: src/agents/assistant_agent/services/generate_response_supervisor.py
# Lines: 782-856

# Option A: Track when we should start streaming
if event_type == "on_chat_model_stream":
    chunk = event_data.get("chunk", {})
    content_chunk = chunk.content if hasattr(chunk, "content") else chunk.get("content", "")

    # FILTER: Only stream if this is the FINAL response phase
    # The agent completes reasoning, then provides final response
    # Indicators of final response:
    # - Contains "Final Response:", "Here's the answer:", "Based on the retrieved...",
    #   actual code blocks, formatted answers (NOT thinking markers)
    # - Comes after RAG tool has been called and results processed

    is_thinking = _is_thinking_content(content_chunk)
    is_final_answer = _is_final_answer_content(content_chunk)

    if is_final_answer and not is_thinking:
        # Stream ONLY final answer content
        yield {
            "type": "streaming_response",
            "chunk": content_chunk,
            ...
        }
    elif is_thinking:
        # Log thinking but don't stream to user
        logger.debug(f"[FILTERING OUT THINKING] {content_chunk[:100]}...")
```

Helper functions:

```python
def _is_thinking_content(content: str) -> bool:
    """
    Detect if content is agent's internal thinking/reasoning.
    Returns True if this should NOT be sent to user.
    """
    thinking_markers = [
        "Document Analysis:",
        "Coverage:",
        "Gaps:",
        "STEP 1:",
        "STEP 2:",
        "STEP 2.5:",
        "STEP 3:",
        "STEP 4:",
        "STEP 5:",
        "STEP 6:",
        "STEP 7:",
        "[Decision]:",
        "[Verification]:",
        "Requirements to verify:",
        "Coverage Status:",
        "Iteration",
        "Action:",
        "Descope",
        "Relevant Documents:",
        "Document Analysis",
    ]

    return any(marker in content for marker in thinking_markers)

def _is_final_answer_content(content: str) -> bool:
    """
    Detect if content is the final answer to send to user.
    Returns True if this SHOULD be sent to user.
    """
    final_answer_indicators = [
        "```",  # Code blocks
        "Based on",  # Explanation phrasing
        "Here's",
        "Here are",
        "The answer",
        "According to",
        "Implementation:",
        "Solution:",
        "Step 1:",  # But NOT "STEP 1:" (agent thinking)
        "To",  # "To implement...", "To solve..."
        "This",  # "This is how..."
        "You can",
        "You should",
    ]

    return any(indicator in content for indicator in final_answer_indicators)
```

### Approach 2: Use Tool Message Boundary

**Strategy**: Only start streaming AFTER the tool (knowledge_expert/task tools) has completed and the LLM is generating the final summary.

```python
# Track tool execution state
tool_execution_complete = False

for event in event_stream:
    event_type = event.get("event")

    # Start streaming only after first tool completes
    if event_type == "on_tool_end":
        tool_execution_complete = True

    # Only stream content after tools have executed
    if event_type == "on_chat_model_stream" and tool_execution_complete:
        # Stream content here
        pass
```

### Approach 3: Message Role-Based Filtering

**Strategy**: Track the message role and only stream content from "assistant" role final message.

```python
# Better approach: Hook into the agent's final message
if event_type == "on_chain_end" and event_name == "LangGraph":
    # Extract final message from agent
    if hasattr(event_data, "output") and "messages" in event_data.output:
        messages = event_data.output["messages"]

        # Get the LAST assistant message (this is the final response)
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                final_response = msg.get("content", "")

                # Stream this as final response (not chunks, just whole)
                yield {
                    "type": "streaming_response",
                    "chunk": final_response,
                    "metadata": {"is_final": True},
                }
                break
```

---

## Implementation Steps

### Step 1: Add Filtering Helper Functions

Add these to `generate_response_supervisor.py`:

```python
def _is_internal_reasoning(content: str) -> bool:
    """
    Detect if content is internal agent reasoning that should be hidden.

    Returns:
        True if content is internal thinking (should NOT stream to user)
        False if content is final answer (should stream)
    """
    # Markers that indicate internal step-by-step thinking
    internal_markers = {
        "STEP 1:", "STEP 2:", "STEP 2.5:", "STEP 3:", "STEP 4:", "STEP 5:", "STEP 6:", "STEP 7:",
        "Document Analysis:", "Coverage Status:", "Requirements to verify:",
        "[Decision]:", "[Verification]:", "[Action]:",
        "Gaps found:", "Iteration", "Descope", "Documents retrieved:",
        "Relevant Documents:", "Quality", "Relevance", "Concreteness",
    }

    return any(marker in content for marker in internal_markers)

def _is_final_response(content: str, has_executed_tools: bool) -> bool:
    """
    Detect if content is the final response to send to user.

    Only return True if:
    1. Tools have been executed (indicating thinking is complete)
    2. Content contains actual answer (code, explanation, etc.)

    Returns:
        True if content is final answer (should stream)
        False if content is incomplete
    """
    if not has_executed_tools:
        return False

    # Indicators of final answer content
    final_indicators = {
        "```",  # Code/markdown blocks
        "Here's the",
        "Based on the",
        "Here are the",
        "According to",
        "The answer",
        "I recommend",
        "You can",
        "You should",
        "Implementation:",
        "Solution:",
    }

    return any(indicator in content for indicator in final_indicators)
```

### Step 2: Modify Streaming Logic

Replace lines 782-856 in `generate_response_supervisor.py`:

**BEFORE**:
```python
if event_type == "on_chat_model_stream":
    chunk = event_data.get("chunk", {})
    content_chunk = chunk.content if hasattr(chunk, "content") else ""

    if content_chunk and content_chunk.strip():
        # PROBLEM: Streams ALL content including thinking
        yield {
            "type": "streaming_response",
            "chunk": content_chunk,
            ...
        }
```

**AFTER**:
```python
if event_type == "on_chat_model_stream":
    chunk = event_data.get("chunk", {})
    content_chunk = chunk.content if hasattr(chunk, "content") else ""

    if content_chunk and content_chunk.strip():
        # FILTER: Only stream if NOT internal reasoning
        if _is_internal_reasoning(content_chunk):
            logger.debug(f"[FILTERING] Internal reasoning hidden from user: {content_chunk[:80]}...")
        else:
            # This is final answer content - stream it
            logger.info(f"[STREAMING FINAL] Yielding final answer chunk: {content_chunk[:50]}...")
            yield {
                "type": "streaming_response",
                "chunk": content_chunk,
                "metadata": {
                    "tools_used": tools_used,
                    "orchestrator_type": "tool_calling_pattern",
                },
                "execution_time_ms": (time.time() - start_time) * 1000,
            }
```

### Step 3: Alternative - Stream After Tool Execution

Track when tools complete:

```python
# At top of stream processing
tools_execution_started = False
tools_execution_completed = False

for event in event_stream:
    event_type = event.get("event")

    # Track tool execution
    if event_type == "on_tool_start":
        tools_execution_started = True
        logger.info("[TOOL START] Tools executing, hiding intermediate responses")

    elif event_type == "on_tool_end":
        tools_execution_completed = True
        logger.info("[TOOL END] Tools completed, now showing final response")

    # Only stream AFTER tools complete
    if event_type == "on_chat_model_stream" and tools_execution_completed:
        chunk = event_data.get("chunk", {})
        content_chunk = chunk.content if hasattr(chunk, "content") else ""

        if content_chunk and content_chunk.strip():
            yield {
                "type": "streaming_response",
                "chunk": content_chunk,
                ...
            }
```

---

## Testing the Fix

### Test Case 1: Filter Internal Reasoning

```python
# Before fix:
User sees: "STEP 1: Task Analysis: The user asked for..."

# After fix:
User doesn't see internal reasoning, only sees final answer
```

### Test Case 2: Stream Final Answer

```python
# Before fix:
Streaming chunks: "Document Analysis", "Coverage", "[Decision]", "Final answer"

# After fix:
Streaming chunks: Only "Final answer"
```

### Test Case 3: Code Generation

```python
# Before fix:
Shows reasoning + code

# After fix:
Shows only code without the thinking process
```

---

## Configuration Options

You can make this configurable:

```python
STREAM_INTERNAL_REASONING = False  # Set True for debugging agent behavior
STREAM_AFTER_TOOL_EXECUTION_ONLY = True  # Only stream after tools complete

if STREAM_INTERNAL_REASONING or not tools_execution_completed:
    # Stream everything
    yield {"type": "streaming_response", "chunk": content_chunk, ...}
else:
    # Filter internal reasoning
    if not _is_internal_reasoning(content_chunk):
        yield {"type": "streaming_response", "chunk": content_chunk, ...}
```

---

## Recommended Implementation

**Use hybrid approach**:

1. **Primary filter**: Check if content is internal reasoning using `_is_internal_reasoning()`
2. **Secondary filter**: Only stream if tools have executed
3. **Fallback**: Stream final message completely

```python
# Recommended hybrid implementation
if event_type == "on_chat_model_stream":
    chunk = event_data.get("chunk", {})
    content_chunk = chunk.content if hasattr(chunk, "content") else ""

    if content_chunk and content_chunk.strip():
        # Check if this is internal thinking
        is_thinking = _is_internal_reasoning(content_chunk)
        is_after_tools = tools_execution_completed

        # Stream if: (NOT thinking) AND (tools completed OR has final indicators)
        should_stream = (not is_thinking) and (is_after_tools or _has_final_indicators(content_chunk))

        if should_stream:
            logger.info(f"[STREAM OK] Sending to user: {content_chunk[:50]}...")
            yield {
                "type": "streaming_response",
                "chunk": content_chunk,
                "metadata": {"tools_used": tools_used},
                "execution_time_ms": (time.time() - start_time) * 1000,
            }
        else:
            logger.debug(f"[FILTERED] Hidden from user (thinking={is_thinking}, after_tools={is_after_tools})")
```

---

## Benefits of Fix

✅ **Cleaner UI**: Users only see final answers, not reasoning
✅ **Professional**: No internal agent steps exposed
✅ **Faster**: Less content to stream
✅ **Clear**: No confusion from mixed reasoning + answers
✅ **Better UX**: Clean, polished responses

---

## File to Modify

**Path**: `src/agents/assistant_agent/services/generate_response_supervisor.py`

**Lines to modify**: 782-856

**Functions to add**:
- `_is_internal_reasoning(content: str) -> bool`
- `_is_final_response(content: str, has_executed_tools: bool) -> bool`

**Variables to track**:
- `tools_execution_completed: bool`

---

## Summary

The issue is that **streaming captures ALL LLM output** (thinking + answer), when it should only stream the **final answer**.

**Fix**: Add filtering functions to detect and hide internal reasoning, only streaming final response content to users.

This ensures users only see polished, final responses without the agent's step-by-step thinking process.
