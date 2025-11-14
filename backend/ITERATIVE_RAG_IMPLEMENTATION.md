# Iterative RAG Evaluation Implementation Guide

## Overview

This document describes the iterative RAG evaluation system implemented in the DataPilotFlow supervisor agent. The system ensures that knowledge retrieved from the knowledge base is sufficient to move forward with task execution. If gaps are found, the system performs targeted re-retrievals (up to 3 iterations maximum) while progressively filtering out weak documents.

## Architecture

### Core Components

#### 1. Supervisor Prompt (Updated)
**File**: `src/agents/common/prompts/supervisor_prompts.py`

**New Step 2.5**: Document Quality & Iteration Tracking
- Introduced iterative RAG enrichment (max 3 iterations)
- Added document evaluation criteria (relevance, concreteness, completeness, recency)
- Implemented gap detection decision tree
- Defined document descoping strategy

**Updated Step 3**: Coverage Verification with Iteration Tracking
- Iteration-specific verification process
- Document scoring system (high/medium/low quality)
- Iteration limits enforcement (proceed after 3 iterations regardless)
- Gap handling with targeted variants

#### 2. Agent State Management (Enhanced)
**File**: `src/agents/assistant_agent/services/agent_state.py`

**New Fields in SupervisorAgentState**:
```python
rag_iteration_count: int  # Tracks current iteration (0=none, 1-3)
rag_iterations_history: List[Dict]  # History of each iteration
rag_descoped_documents: List[Dict]  # Weak/irrelevant documents filtered out
coverage_verification_results: List[Dict]  # Coverage check results
```

**New Methods**:
- `start_rag_iteration()`: Increment iteration counter (max 3)
- `is_max_iterations_reached()`: Check if limit reached
- `record_coverage_verification()`: Log coverage verification results
- `record_iteration_knowledge()`: Track knowledge quality per iteration
- `descope_weak_documents()`: Remove weak documents from active context
- `get_iteration_summary()`: Get detailed iteration metrics

### Workflow Flow

```
USER QUERY
    ↓
STEP 1: Task Analysis & Requirements
    ├─ Identify requirements
    ├─ Plan knowledge retrieval strategy
    └─ Generate success criteria
    ↓
STEP 2: Call knowledge_expert (Iteration 1/3)
    ├─ Pass 5 query variants
    └─ Receive documents
    ↓
STEP 2.5: Document Quality Assessment
    ├─ Score document quality
    └─ Identify gaps
    ↓
STEP 3: Coverage Verification (with iteration tracking)
    ├─ Check Iteration 1/3?
    ├─ All requirements covered?
    │   ├─ YES → Proceed to Step 4
    │   └─ NO → Is this iteration 1 or 2?
    │       ├─ YES → Descope weak docs, call knowledge_expert again
    │       └─ NO (iteration 3) → Use best docs from all iterations, proceed to Step 4
    └─ Loop back to Step 2.5 if iterating
    ↓
STEP 4-7: Generate and Verify Result
```

## Implementation Details

### Document Quality Scoring

Documents are evaluated on 4 criteria:

1. **Relevance to Requirements**: Does it directly address a user requirement?
   - High (✓✓✓): Direct match
   - Medium (✓✓): Partially relevant
   - Low (✓): Tangentially related
   - None (✗): Not relevant

2. **Concreteness**: Does it include examples, code, patterns?
   - High (✓✓✓): Concrete examples/code included
   - Medium (✓✓): Some guidance with few examples
   - Low (✓): Theoretical/overview only
   - None (✗): Vague

3. **Completeness**: Thoroughly explained or overview?
   - High (✓✓✓): Comprehensive explanation
   - Medium (✓✓): Covers main points
   - Low (✓): Incomplete coverage
   - None (✗): Insufficient

4. **Recency**: Is it current and applicable?
   - High (✓✓✓): Recent and up-to-date
   - Medium (✓✓): Generally applicable
   - Low (✓): Possibly outdated
   - None (✗): Clearly outdated

### Gap Detection Decision Tree

```
For EACH requirement/component:

├─ Is there documentation covering this?
│  ├─ YES → Is it concrete with examples?
│  │  ├─ YES → Is it sufficient to build/implement?
│  │  │  ├─ YES → ✓✓✓ (Well covered - KEEP)
│  │  │  └─ NO → ✗? (Need more - target in next iteration)
│  │  └─ NO → ✗ (Overview only - descope)
│  └─ NO → ✗ (Gap exists - target in next iteration)
```

### Document Descoping Strategy

Between iterations, weak documents are identified and descoped:

**Descope if**:
- Relevance score < 0.4
- Mostly duplicative (already have similar content)
- Too vague when specificity is needed
- Superseded by newer, more relevant documents

**Keep if**:
- Relevance score ≥ 0.6
- Contains concrete examples and patterns
- Directly answers user requirements
- Recent/applicable information

### Iteration Limits

**Iteration 1**: Initial retrieval with broad variants
- If gaps detected → Plan Iteration 2

**Iteration 2**: Targeted enrichment for specific gaps
- Descope weak docs from Iteration 1
- Create more specific variants
- If gaps still exist → Plan Iteration 3

**Iteration 3**: Final enrichment attempt
- Most specific variants targeting remaining gaps
- Maximum knowledge accumulation
- After Iteration 3, proceed regardless of gaps

**Max Reached (3 iterations)**:
- Document what gaps remain
- Select strongest documents from all iterations
- Proceed to Step 4
- Note: May need to work around incomplete knowledge

## Usage Examples

### Example 1: Single Iteration (All Requirements Covered)

**User Query**: "Create a React component with error handling"

**Iteration 1**:
```
STEP 2: knowledge_expert([
  "create React component",
  "React component setup",
  "error handling in React",
  "exception handling patterns",
  "React error boundaries"
])
```

**STEP 3 Verification**:
- React component: ✓✓✓ (high quality, concrete examples)
- Error handling: ✓✓✓ (concrete error boundary examples)
- Decision: **All covered** → Proceed to Step 4

**Iterations Used**: 1/3

### Example 2: Two Iterations with Descoping

**User Query**: "Create REST API with validation and logging"

**Iteration 1**:
```
STEP 2: knowledge_expert([
  "REST API setup",
  "API validation",
  "request validation",
  "API logging",
  "logging configuration"
])
```

**STEP 3 Verification**:
- REST API: ✓✓✓ (comprehensive)
- Validation: ✓ (overview only, no concrete examples)
- Logging: ✗ (no relevant documents)
- Decision: **Gaps detected** → Iteration 2 needed

**Descope Decision**:
- Descope: Low-quality validation docs (overview only)
- Keep: REST API docs (high quality)

**Iteration 2**:
```
STEP 2: knowledge_expert([
  "input validation patterns",
  "validation middleware implementation",
  "request validation examples",
  "logging implementation",
  "structured logging setup"
])
```

**STEP 3 Verification**:
- REST API: ✓✓✓ (from Iteration 1, kept)
- Validation: ✓✓✓ (concrete patterns from Iteration 2)
- Logging: ✓✓✓ (setup examples from Iteration 2)
- Decision: **All covered** → Proceed to Step 4

**Iterations Used**: 2/3

### Example 3: Three Full Iterations

**User Query**: "System with component A, validation, error handling, logging, and caching"

**Iteration 1**:
```
STEP 2: knowledge_expert([
  "component A setup",
  "component A configuration",
  "component A implementation",
  "validation patterns",
  "error handling"
])
```

**STEP 3**: Coverage check
- Component A: ✓✓✓
- Validation: ✓✓
- Error handling: ✓✓
- Logging: ✗
- Caching: ✗
- Decision: **Gaps** → Iteration 2

**Iteration 2**:
```
STEP 2: knowledge_expert([
  "logging implementation",
  "application logging setup",
  "event logging patterns",
  "logging best practices",
  "structured logging"
])
```

**STEP 3**: Coverage check
- Component A: ✓✓✓ (kept from Iter 1)
- Validation: ✓✓ (kept from Iter 1)
- Error handling: ✓✓ (kept from Iter 1)
- Logging: ✓✓✓ (from Iteration 2)
- Caching: ✗
- Decision: **Gaps** → Iteration 3

**Iteration 3**:
```
STEP 2: knowledge_expert([
  "caching strategies",
  "cache implementation",
  "in-memory caching",
  "cache invalidation",
  "caching patterns"
])
```

**STEP 3**: Coverage check
- All from previous iterations ✓✓✓
- Caching: ✓✓✓ (from Iteration 3)
- Decision: **All covered** → Proceed to Step 4

**Iterations Used**: 3/3

### Example 4: Max Iterations Reached with Remaining Gaps

**User Query**: "System with 5 complex features"

**After Iteration 3**:
- Feature 1: ✓✓✓ (well covered)
- Feature 2: ✓✓✓ (well covered)
- Feature 3: ✓✓ (covered but not ideal)
- Feature 4: ✓ (overview only)
- Feature 5: ✗ (gap - knowledge not in KB)
- **MAX ITERATIONS REACHED**

**Decision**:
- Document gap: "Feature 5 knowledge not available in knowledge base"
- Use strongest docs from all 3 iterations for Features 1-4
- Proceed to Step 4
- When generating, may use training data for Feature 5 or note limitation

## State Tracking

### SupervisorAgentState Fields

```python
# Iteration tracking
rag_iteration_count: int  # Current iteration (0-3)
rag_iterations_history: List[Dict]  # History with timestamps

# History entry structure:
{
  "iteration": 1,
  "doc_count": 15,
  "quality_scores": {"high": 8, "medium": 5, "low": 2},
  "targeted_variants": ["variant1", "variant2", ...],
  "timestamp": "2024-11-13T10:30:00"
}

# Coverage verification tracking
coverage_verification_results: List[Dict]

# Verification entry structure:
{
  "iteration": 1,
  "requirements": ["auth", "validation", "logging"],
  "coverage_status": {"auth": "covered", "validation": "gap", "logging": "covered"},
  "gaps_found": ["validation"],
  "action": "iterate",
  "timestamp": "2024-11-13T10:30:05"
}

# Descoped documents
rag_descoped_documents: List[Dict]  # Weak/irrelevant documents
```

### Accessing Iteration Data

```python
# Check iteration status
state.is_max_iterations_reached()  # bool

# Get iteration summary
summary = state.get_iteration_summary()
# Returns:
{
  "current_iteration": 2,
  "max_iterations": 3,
  "is_max_reached": False,
  "iterations_history": [...],
  "coverage_verifications": [...],
  "active_documents": 20,
  "descoped_documents": 5
}

# Get full execution summary
summary = state.get_execution_summary()
# Includes rag_iterations if iterations were used
```

## Integration Points

### 1. Supervisor Prompt Usage

The agent uses the enhanced prompt to:
- Generate task analysis and requirements in STEP 1
- Call knowledge_expert with initial variants in STEP 2
- Evaluate documents and track iterations in STEP 2.5
- Verify coverage with iteration awareness in STEP 3
- Manage descoping of weak documents between iterations

### 2. Agent State Usage

When the LLM executes the workflow, it can:
- Track current iteration automatically
- Access iteration history for context
- Record coverage verification results
- Know when max iterations is reached
- Adjust behavior accordingly

### 3. Tool Integration

When calling other tools (generation, analysis, etc.):
- Pass complete knowledge from all iterations
- Include metadata about which iteration provided each document
- Reference coverage verification results if needed

## Best Practices

### For Agent Implementation

1. **Always respect iteration limits**: After 3 iterations, proceed regardless of gaps

2. **Descope progressively**: Remove weak documents between iterations to improve signal

3. **Target gaps specifically**: Each iteration's variants should target missing knowledge

4. **Accumulate intelligently**: Keep high-quality docs, descope low-quality ones

5. **Document gaps**: When max iterations reached, explicitly note what couldn't be covered

### For Prompt Engineering

1. **First iteration**: Use broad, comprehensive variants covering all aspects

2. **Second iteration**: More specific, targeted variants for identified gaps

3. **Third iteration**: Highly specific variants targeting remaining gaps

4. **Variant generation**: Never repeat exact same queries across iterations

5. **Quality threshold**: Use ≥0.6 relevance as quality threshold for keeping documents

### For Knowledge Base

1. **Rich documentation**: Ensure examples, not just overviews

2. **Comprehensive coverage**: Cover common use cases and edge cases

3. **Clear organization**: Group related topics for better retrieval

4. **Metadata quality**: Ensure accurate relevance scoring

## Monitoring and Debugging

### Key Metrics

- `rag_iteration_count`: How many iterations were used
- `active_documents`: How many high-quality docs retained
- `descoped_documents`: How many weak docs filtered
- `coverage_verification_results`: Success/failure of each verification

### Common Issues

**Issue**: Many iterations needed for simple query
- **Cause**: Initial query variants too narrow
- **Solution**: Improve variant generation in STEP 1

**Issue**: Still gaps after 3 iterations
- **Cause**: Knowledge not in KB or poorly indexed
- **Solution**: Enhance knowledge base or accept limitation

**Issue**: Too many documents descoped
- **Cause**: Relevance scoring too strict
- **Solution**: Adjust relevance threshold or improve KB indexing

## Testing the Implementation

### Manual Testing

1. **Single iteration case**: Query that requires only initial retrieval
2. **Two iteration case**: Query with one gap that needs enrichment
3. **Three iteration case**: Query with multiple gaps
4. **Max iteration case**: Query with knowledge gaps in KB

### Automated Testing

```python
# Test iteration tracking
state = SupervisorAgentState()
assert state.rag_iteration_count == 0

state.start_rag_iteration()
assert state.rag_iteration_count == 1

# Test coverage recording
state.record_coverage_verification(
  iteration=1,
  requirements=["auth", "validation"],
  coverage_status={"auth": "covered", "validation": "gap"},
  gaps_found=["validation"],
  action="iterate"
)
assert len(state.coverage_verification_results) == 1

# Test descoping
descoped = state.descope_weak_documents(["doc1", "doc2"])
assert descoped == 2
```

## Summary

The iterative RAG evaluation system provides:

✅ **Intelligent knowledge retrieval**: Up to 3 focused retrieval iterations
✅ **Quality filtering**: Progressive removal of weak documents
✅ **Gap detection**: Systematic identification of missing knowledge
✅ **Iteration limits**: Enforced max 3 iterations to prevent infinite loops
✅ **State tracking**: Complete history and metrics for debugging
✅ **Scalability**: Handles complex multi-component requirements

The system ensures that only when comprehensive knowledge is available (or max iterations reached) does the agent proceed to task execution, resulting in higher quality outputs grounded in retrieved knowledge.
