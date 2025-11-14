# RAG Iteration System - Quick Reference

## TL;DR

The supervisor agent now iteratively retrieves knowledge (max 3 times) until all user requirements are covered or iterations are exhausted. Weak documents are filtered out between iterations.

## Key Additions

### 1. Updated Supervisor Prompt
- **File**: `src/agents/common/prompts/supervisor_prompts.py`
- **New Step 2.5**: Document Quality & Iteration Tracking
- **Updated Step 3**: Coverage Verification with Iteration Limits

### 2. Enhanced Agent State
- **File**: `src/agents/assistant_agent/services/agent_state.py`
- **New Fields**: `rag_iteration_count`, `rag_iterations_history`, `rag_descoped_documents`, `coverage_verification_results`
- **New Methods**:
  - `start_rag_iteration()` - Increment iteration (max 3)
  - `is_max_iterations_reached()` - Check if at limit
  - `record_coverage_verification()` - Log coverage checks
  - `record_iteration_knowledge()` - Track iteration quality
  - `descope_weak_documents()` - Filter weak docs
  - `get_iteration_summary()` - Get iteration metrics

## How It Works

```
Iteration 1
├─ Call knowledge_expert with 5 broad variants
├─ Evaluate document quality
├─ Check coverage against requirements
└─ If gaps found and iteration < 3 → Iteration 2

Iteration 2
├─ Descope weak documents from Iteration 1
├─ Call knowledge_expert with targeted variants for gaps
├─ Evaluate new documents
├─ Check coverage again
└─ If gaps still found and iteration < 3 → Iteration 3

Iteration 3
├─ Descope weak documents from Iteration 2
├─ Call knowledge_expert with highly specific variants
├─ Evaluate new documents
├─ Check coverage one final time
└─ Proceed to Step 4 regardless (max reached)

Step 4+: Proceed with task execution using accumulated knowledge
```

## Document Quality Criteria

### Scoring Tiers

| Quality | Relevance | Examples | Completeness | Recency |
|---------|-----------|----------|--------------|---------|
| High ✓✓✓ | Direct | Concrete | Comprehensive | Current |
| Medium ✓✓ | Related | Some | Partial | Mostly OK |
| Low ✓ | Tangential | Few | Overview | May be old |
| None ✗ | Not related | None | Vague | Outdated |

### Descoping Rules

**Descope documents if**:
- Relevance score < 0.4
- Vague/overview only when specificity needed
- Duplicative of better content
- Superseded by newer docs

**Keep documents if**:
- Relevance score ≥ 0.6
- Concrete examples/patterns included
- Directly address user requirements
- Recent/applicable

## Common Patterns

### Pattern 1: Query Fully Satisfied in Iteration 1

```python
User: "What is OAuth?"

Iteration 1:
├─ Retrieved: OAuth overview ✓, Flow diagrams ✓, Examples ✓
├─ Coverage: 100% ✓
└─ Proceed to Step 4 (no more iterations needed)

Iterations Used: 1/3
```

### Pattern 2: Partial Coverage → Iterate

```python
User: "Build REST API with validation"

Iteration 1:
├─ Retrieved: REST API basics ✓, Validation overview ✓ (vague)
├─ Quality: API high, Validation low
├─ Coverage: 80% (missing validation examples)
└─ Decision: Descope weak validation docs, iterate

Iteration 2:
├─ Descoped: Weak validation overview docs
├─ Retrieved: Validation patterns ✓✓, Examples ✓✓
├─ Coverage: 100% ✓
└─ Proceed to Step 4

Iterations Used: 2/3
```

### Pattern 3: Multiple Gaps → Progressive Enrichment

```python
User: "System with A, B, C, D, E"

Iteration 1:
├─ Have: A ✓, B ✓
├─ Missing: C, D, E
└─ Decision: Get C

Iteration 2:
├─ Have: A ✓, B ✓, C ✓
├─ Missing: D, E
└─ Decision: Get D

Iteration 3:
├─ Have: A ✓, B ✓, C ✓, D ✓
├─ Missing: E (but max iterations reached)
└─ Proceed with best docs for A-D, note E gap

Iterations Used: 3/3 (max)
```

## State Management Quick Commands

```python
# Get current iteration
state.rag_iteration_count  # 0, 1, 2, or 3

# Check if at max
if state.is_max_iterations_reached():
    # Proceed with available knowledge

# Start new iteration
state.start_rag_iteration()  # Increments counter (max 3)

# Record coverage check
state.record_coverage_verification(
    iteration=1,
    requirements=["auth", "validation"],
    coverage_status={"auth": "covered", "validation": "gap"},
    gaps_found=["validation"],
    action="iterate"  # or "proceed" or "max_reached"
)

# Track iteration knowledge
state.record_iteration_knowledge(
    iteration=1,
    retrieved_docs=[...],
    quality_scores={"doc1": "high", "doc2": "low"},
    targeted_variants=[...]
)

# Remove weak documents
count = state.descope_weak_documents(["weak_doc_id1", "weak_doc_id2"])

# Get metrics
summary = state.get_iteration_summary()
# Returns: current_iteration, max_iterations, is_max_reached,
#          iterations_history, coverage_verifications,
#          active_documents, descoped_documents
```

## Integration Checklist

- [x] Supervisor prompt updated with Step 2.5 and enhanced Step 3
- [x] Agent state has iteration tracking fields
- [x] Agent state has iteration management methods
- [x] Descoping logic implemented
- [x] Coverage verification with limits implemented
- [x] Documentation complete

## What Happens in Each Iteration

### Iteration 1: Broad Discovery
- **Variants**: 5 broad, comprehensive variants covering all aspects
- **Goal**: Get initial understanding across all requirement areas
- **Quality Check**: Identify weak/vague documents
- **Decision**: Proceed or iterate

### Iteration 2: Targeted Enrichment
- **Variants**: More specific, targeting identified gaps
- **Goal**: Fill knowledge gaps from Iteration 1
- **Quality Check**: Ensure new docs are concrete/specific
- **Descoping**: Remove low-quality docs from Iteration 1
- **Decision**: Proceed or iterate

### Iteration 3: Final Deep Dive
- **Variants**: Highly specific variants for remaining gaps
- **Goal**: Last attempt to cover everything
- **Quality Check**: Prioritize strongest documents from all iterations
- **Descoping**: Further filter to highest-quality documents only
- **Decision**: Must proceed (max iterations reached)

## Key Design Principles

1. **Iteration Limit**: Max 3 iterations prevents infinite loops
2. **Progressive Filtering**: Descope weak docs between iterations
3. **Targeted Variants**: Each iteration uses completely different variants
4. **Quality Over Quantity**: Prefer fewer high-quality docs
5. **Graceful Degradation**: Proceed after 3 iterations even with gaps
6. **Full History**: Track all iterations for analysis/debugging

## Prompt Sections to Review

In `supervisor_prompts.py`:

- **Lines 112-221**: Step 2.5 (Document Quality & Iteration Tracking)
- **Lines 224-274**: Step 3 (Coverage Verification with Iteration Limits)
- **Lines 276-334**: Examples with iteration tracking

## State Code to Review

In `agent_state.py`:

- **Lines 56-60**: New iteration tracking fields
- **Lines 191-204**: Iteration management methods (`start_rag_iteration`, `is_max_iterations_reached`)
- **Lines 206-238**: Coverage verification recording
- **Lines 240-269**: Iteration knowledge recording
- **Lines 271-304**: Document descoping logic
- **Lines 306-321**: Iteration summary generation
- **Lines 323-344**: Updated execution summary with iterations

## Common Questions

**Q: How do I trigger an iteration?**
A: The agent automatically decides based on coverage verification in Step 3.

**Q: Can I manually control iterations?**
A: The state provides `start_rag_iteration()` and `is_max_iterations_reached()` for external control if needed.

**Q: What happens if all requirements can't be covered?**
A: After 3 iterations, the agent proceeds with the best available knowledge and documents the gaps.

**Q: How are weak documents identified?**
A: By evaluating: relevance score, concreteness, completeness, recency.

**Q: Can I change the max iterations?**
A: Yes, modify `is_max_iterations_reached()` to check against a different limit, but 3 is recommended to avoid infinite loops.

## Testing the Implementation

```bash
# Run with a simple query (1 iteration expected)
# Run with a multi-component query (2-3 iterations expected)
# Check state.get_execution_summary() for iteration metrics
```

## Performance Impact

- **Knowledge Retrieval**: Up to 3x knowledge_expert calls (vs 1 previously)
- **LLM Reasoning**: Added Step 2.5 and enhanced Step 3 reasoning
- **Overall**: Slightly slower but higher quality results due to knowledge completeness

## Future Enhancements

- [ ] Adaptive iteration limits based on query complexity
- [ ] ML-based quality scoring instead of hardcoded thresholds
- [ ] Parallel variant processing in iterations
- [ ] Knowledge base gap detection and recommendations
- [ ] Iteration metrics dashboard

---

**Last Updated**: 2024-11-13
**Version**: 1.0
