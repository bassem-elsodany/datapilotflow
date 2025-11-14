# Dynamic Tool Instructions - Complete Implementation

## Overview

Users can now define custom instructions for how their dynamically bound tools should work together. These instructions are user-specific and conversation-specific, making the supervisor agent tool-agnostic and adaptive to any tool combination.

## Architecture

### Data Flow

```
User Setup:
1. Create conversation (Assistant mode)
2. Select tools (Step 6)
3. Provide orchestration instructions (Step 7)
4. Store in assistant_config.tool_instructions

At Runtime:
1. Supervisor loads conversation config
2. Fetches user's tool_instructions
3. Appends to STEP 5 of supervisor prompt
4. LLM reads and follows user's preferences
5. Calls tools according to user's specifications
```

## Backend Implementation

### 1. Domain Model Changes

**File:** `src/domain/conversation/models.py`

```python
@dataclass
class AssistantConfig:
    enabled: bool
    tools: Optional[List[str]] = None
    tool_instructions: Optional[str] = None  # NEW
```

### 2. Supervisor Agent Integration

**File:** `src/agents/assistant_agent/services/generate_response_supervisor.py`

The supervisor now loads and injects user instructions:

```python
# Add user-configured tool instructions if available
if (
    assistant_config
    and assistant_config.tool_instructions
    and assistant_config.tool_instructions.strip()
):
    logger.info("✅ User-configured tool instructions found - appending to prompt")
    system_prompt_parts.append(
        f"\n\n**User-Configured Tool Usage Instructions:**\n\n{assistant_config.tool_instructions}"
    )
```

**Where it's inserted:** After knowledge base context, before creating the agent

**Effect:** Instructions become part of STEP 5 (Tool Execution) guidance

### 3. Log Output

When tool instructions are detected:
```
✅ User-configured tool instructions found - appending to prompt
```

## Frontend Implementation

### 1. New Component

**File:** `dashboard/src/pages/dashboard/apps/knowledge/tool-instructions-step.tsx`

Provides:
- Textarea for custom instructions
- 4 built-in templates
- Live examples
- Guidelines for writing good instructions

### 2. Wizard Integration

**File:** `dashboard/src/pages/dashboard/apps/knowledge/conversation-create-wizard.tsx`

Changes:
- Added `tool_instructions` to form data
- Added Step 7 (Tool Instructions) for Assistant mode only
- Updated step progression logic (now 0-8 steps, assistant mode; 0-6 steps, RAG mode)
- Tool instructions included in API payload

### 3. Template Examples

#### Template 1: Sequential Execution
```
For each user query:
1. First call any relevant helper tools that provide context or examples
2. Then call the main execution tool with accumulated knowledge
3. Verify the result meets all user requirements
```

#### Template 2: Conditional Based on Query Type
```
Based on query characteristics, use different tool sequences:

For simple queries:
- Only call the main execution tool directly

For complex queries:
- Call all available helper tools first
- Accumulate knowledge
- Call main execution tool with complete context
```

#### Template 3: Parallel Execution
```
Execute tools in parallel where possible:

Phase 1 (Parallel):
- Call error handling tool
- Call configuration tool
(Wait for all to complete)

Phase 2 (Sequential):
- Call main execution tool with all accumulated context
```

#### Template 4: Custom Workflow
```
Describe your custom tool workflow with:
- When each tool should be called
- What tools work together
- How results accumulate
```

## Usage Guide

### For Users

#### Step 1: Select Tools
Choose which tools the assistant should use (Step 6)

#### Step 2: Configure Orchestration
Provide instructions in Step 7 using one of the templates or custom instructions:

**Example for MuleSoft assistant:**
```
For MuleSoft flow generation:

1. Error Handling First:
   - If user mentions "error handling", "errors", or "exceptions"
   - Call error_handler_tool to get error patterns

2. Configuration Next:
   - If user mentions "production", "configuration", or "setup"
   - Call configuration_tool to get setup patterns

3. Main Generation:
   - Call flow_generator with accumulated context
   - Use error patterns and configuration guidance

4. Simple Queries:
   - For "Create simple flow" requests
   - Skip helpers, go directly to flow_generator
```

### For Developers

#### Loading Tool Instructions

In the supervisor initialization:
```python
# Load from conversation config
assistant_config = conversation.assistant_config
if assistant_config and assistant_config.tool_instructions:
    # Instructions already appended in generate_response_supervisor.py
```

#### How Instructions Reach the LLM

1. User provides instructions in UI (Step 7)
2. Stored in database: `conversations.assistant_config.tool_instructions`
3. Loaded at runtime in `generate_response_supervisor.py`
4. Appended to system prompt before agent creation
5. LLM sees instructions as part of STEP 5 (Tool Execution)
6. LLM follows instructions when deciding which tools to call

## Examples

### Example 1: Two-Tool System

**Tools Bound:**
- `generator`: Creates artifacts
- `validator`: Validates results

**User Instructions:**
```
Sequential workflow:
1. Always call validator AFTER generator
2. If validation fails, call generator again with validation feedback
3. Repeat until validation passes
```

**LLM Behavior:**
- Calls generator
- Calls validator
- If invalid, re-calls generator with feedback
- Repeats until valid

### Example 2: Multi-Step Analysis

**Tools Bound:**
- `analyzer`: Analyzes code
- `optimizer`: Optimizes based on analysis
- `generator`: Generates optimized code

**User Instructions:**
```
Three-step pipeline:
1. First call analyzer to understand current code
2. Then call optimizer with analysis results
3. Finally call generator with optimization suggestions

Never skip analysis - always run in this order.
```

**LLM Behavior:**
- Calls in strict sequence
- Passes context between tools
- Maintains data flow

### Example 3: Context-Aware Selection

**Tools Bound:**
- `quick_generator`: Fast simple generation
- `full_generator`: Comprehensive generation
- `documentation_generator`: Creates docs

**User Instructions:**
```
Smart tool selection:

For requests with "quick" or "fast":
- Only call quick_generator

For requests with "complete" or "comprehensive":
- Call full_generator
- Then call documentation_generator
- Combine outputs

Default:
- Call full_generator
```

**LLM Behavior:**
- Analyzes query keywords
- Selects appropriate tools
- Follows specified workflow

## Best Practices

### 1. Be Specific
```
✅ GOOD: "If user mentions error handling, call error_handler_tool first"
❌ BAD: "Consider calling helper tools"
```

### 2. Include Conditions
```
✅ GOOD: "For complex queries, call all helpers. For simple queries, skip helpers."
❌ BAD: "Call helpers sometimes"
```

### 3. Describe Context Flow
```
✅ GOOD: "Pass analysis results to optimizer, then to generator"
❌ BAD: "Use all tools"
```

### 4. Be Realistic
```
✅ GOOD: "Max 3 tool calls total to keep response time reasonable"
❌ BAD: "Call every tool for every query"
```

## Integration Points

### Database Layer
- `assistant_config.tool_instructions` stored in MongoDB
- Persisted with conversation metadata
- Can be edited/updated like other config

### API Layer
- Included in conversation creation payload
- Included in conversation update payload
- Returned when fetching conversation details

### Supervisor Layer
- Loaded during initialization
- Appended to system prompt
- Available to LLM for decision-making

## Validation

**Frontend Validation:**
- No validation - instructions are optional
- Accept any natural language

**Backend Validation:**
- No validation - treated as plain text
- LLM determines if instructions are useful

**Runtime Behavior:**
- If instructions are missing: LLM uses default multi-tool logic
- If instructions exist: LLM follows user's preferences
- If instructions are unclear: LLM does best interpretation

## Backward Compatibility

✅ **Fully backward compatible:**
- `tool_instructions` is optional (can be null)
- Existing conversations without instructions work normally
- No migration needed
- Can add instructions to existing conversations

## Testing Scenarios

### Scenario 1: Sequential Execution
```
Setup: 2 tools (helper, generator)
Instructions: "Call helper first, then generator"
Test: Verify order in logs
```

### Scenario 2: Conditional Logic
```
Setup: 3 tools (quick, full, docs)
Instructions: Complex conditional logic
Test: Verify tool selection based on different queries
```

### Scenario 3: No Instructions
```
Setup: Tools without instructions
Test: Verify tools still work with default behavior
```

### Scenario 4: Update Instructions
```
Setup: Conversation with instructions
Update: Modify instructions
Test: Verify new instructions take effect
```

## Monitoring

### Logs to Check

```bash
# Tool instructions were appended
grep "User-configured tool instructions found" logs/datapilotflow.log

# Tool execution order
grep "Tool.*executing" logs/datapilotflow.log

# Verify instructions in prompt
grep "User-Configured Tool Usage Instructions" logs/datapilotflow.log
```

### Metrics to Track

- Percentage of conversations using tool instructions
- Average length of instructions
- Tool execution patterns with vs. without instructions
- User satisfaction with results

## Future Enhancements

Potential improvements:
1. Instruction templates per tool type
2. Instruction validation/linting
3. Tool execution history visualization
4. Analytics on instruction effectiveness
5. AI-suggested instructions based on tools
6. Version history for instructions
7. Instruction recommendations

## Summary

**What Changed:**
- Added `tool_instructions` field to conversation config
- UI step to configure tool orchestration
- Supervisor loads and appends instructions to prompt
- LLM follows user's preferences

**Benefits:**
- Tool-agnostic system
- User-controlled workflows
- Scales with new tools
- Flexible per-conversation configuration

**Key Files:**
- Backend: `generate_response_supervisor.py`, `models.py`
- Frontend: `tool-instructions-step.tsx`, `conversation-create-wizard.tsx`

**Status:** ✅ Complete and ready for production

