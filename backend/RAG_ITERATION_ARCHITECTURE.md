# Iterative RAG Evaluation - Architecture & Data Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER QUERY                              │
└────────────────────────────┬──────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  STEP 1: Task   │
                    │  Analysis &     │
                    │  Requirements   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  STEP 2:        │
                    │  knowledge_     │
         ┌──────────┤  expert call    │
         │          │  (Iteration 1/3)│
         │          └────────┬────────┘
         │                   │
         │          ┌────────▼──────────────┐
         │          │  STEP 2.5: Document  │
         │          │  Quality Assessment   │
         │          │  - Score each doc     │
         │          │  - Identify gaps      │
         │          └────────┬──────────────┘
         │                   │
         │          ┌────────▼──────────────────┐
         │          │  STEP 3: Coverage       │
         │          │  Verification           │
         │          │  - Check requirements   │
         │          │  - Identify gaps        │
         │          └────┬─────────────────┬───┘
         │               │                 │
         │         [GAP FOUND]        [ALL COVERED]
         │               │                 │
         │        ┌──────▼──────┐    ┌─────▼──────┐
         │        │ Iteration < 3? │    │ STEP 4:   │
         │        └──────┬──────┘    │ Analyze &  │
         │          YES │            │ Determine  │
         │               │            │ Action    │
         │        ┌──────▼──────────┐ └─────┬─────┘
         │        │ Descope Weak    │       │
         │        │ Documents       │       │
         │        └──────┬──────────┘       │
         │               │                  │
         └───────────────┘                  │
                  │                         │
         ┌────────▼────────┐                │
         │ Generate New    │                │
         │ Targeted        │                │
         │ Variants        │                │
         └────────┬────────┘                │
                  │                         │
                  └──────────────┬──────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  STEP 5: Use Tools      │
                    │  (with accumulated      │
                    │   knowledge from all    │
                    │   iterations)           │
                    └────────┬────────────────┘
                             │
                    ┌────────▼────────┐
                    │  STEP 6: Result │
                    │  Verification   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  STEP 7: Final  │
                    │  Response       │
                    └─────────────────┘
```

## State Management Data Flow

```
┌─────────────────────────────────────────────────────────┐
│           SupervisorAgentState (NEW FIELDS)             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  rag_iteration_count: int (0-3)                        │
│      └─ Tracks current iteration                       │
│                                                         │
│  rag_iterations_history: List[Dict]                    │
│      ├─ Iteration 1 record                             │
│      │  ├─ doc_count: 15                               │
│      │  ├─ quality_scores: {high: 8, med: 5, low: 2}  │
│      │  ├─ targeted_variants: [...]                    │
│      │  └─ timestamp: "..."                            │
│      │                                                  │
│      ├─ Iteration 2 record                             │
│      │  └─ [same structure]                            │
│      │                                                  │
│      └─ Iteration 3 record                             │
│         └─ [same structure]                            │
│                                                         │
│  coverage_verification_results: List[Dict]             │
│      ├─ Verification 1                                 │
│      │  ├─ iteration: 1                                │
│      │  ├─ requirements: [...]                         │
│      │  ├─ coverage_status: {...}                      │
│      │  ├─ gaps_found: [...]                           │
│      │  ├─ action: "iterate"|"proceed"|"max_reached"  │
│      │  └─ timestamp: "..."                            │
│      │                                                  │
│      └─ [Additional verifications...]                  │
│                                                         │
│  rag_descoped_documents: List[Dict]                    │
│      ├─ Weak doc 1 (from Iter 1)                       │
│      ├─ Weak doc 2 (from Iter 1)                       │
│      └─ [Additional descoped docs...]                  │
│                                                         │
│  rag_documents: List[Dict] (KEPT HIGH-QUALITY)        │
│      ├─ High-quality doc 1 (Iter 1)                    │
│      ├─ High-quality doc 2 (Iter 1)                    │
│      ├─ New doc 1 (Iter 2)                             │
│      └─ New doc 2 (Iter 2)                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Iteration Loop Sequence

```
ITERATION 1
├─ knowledge_expert() call
│  └─ Returns: 15 documents
├─ Document scoring:
│  ├─ High quality: 8 docs (keep)
│  ├─ Medium quality: 5 docs (maybe keep)
│  └─ Low quality: 2 docs (descope)
├─ Coverage verification:
│  ├─ Requirement A: ✓✓✓ (well covered)
│  ├─ Requirement B: ✓✓ (partial)
│  ├─ Requirement C: ✗ (missing)
│  └─ Decision: GAPS FOUND → Continue iteration loop
├─ state.record_coverage_verification(iter=1, gaps=[C], action="iterate")
├─ state.record_iteration_knowledge(iter=1, docs=15, scores={high:8,...})
└─ state.descope_weak_documents([weak_doc_1, weak_doc_2])
   └─ rag_documents now has: 13 high/medium quality docs

ITERATION 2
├─ Generate targeted variants for Requirement C
├─ knowledge_expert() call with new variants
│  └─ Returns: 8 new documents
├─ Document scoring:
│  ├─ High quality: 6 docs (keep)
│  └─ Low quality: 2 docs (descope)
├─ Merged rag_documents: 13 (from Iter 1) + 6 (from Iter 2) = 19 docs
├─ Coverage verification:
│  ├─ Requirement A: ✓✓✓ (from Iter 1)
│  ├─ Requirement B: ✓✓✓ (upgraded with Iter 2)
│  ├─ Requirement C: ✓✓ (now from Iter 2)
│  └─ Decision: ALL COVERED → Exit iteration loop
├─ state.record_coverage_verification(iter=2, gaps=[], action="proceed")
└─ state.record_iteration_knowledge(iter=2, docs=8, scores={high:6,...})

PROCEED TO STEP 4+
└─ Use accumulated knowledge: 19 high-quality documents from Iterations 1-2
```

## Document Quality Evaluation Flow

```
┌─ Document Retrieved ─┐
└─────────┬────────────┘
          │
    ┌─────▼─────────────────────────────────┐
    │  Evaluate 4 Criteria                   │
    ├────────────────────────────────────────┤
    │ 1. Relevance to Requirements           │
    │    • Direct match (✓✓✓)                │
    │    • Partially relevant (✓✓)           │
    │    • Tangential (✓)                    │
    │    • Not relevant (✗)                  │
    │                                        │
    │ 2. Concreteness (examples/code)        │
    │    • Concrete examples (✓✓✓)           │
    │    • Some guidance (✓✓)                │
    │    • Theoretical only (✓)              │
    │    • Vague (✗)                         │
    │                                        │
    │ 3. Completeness (comprehensive)        │
    │    • Comprehensive (✓✓✓)               │
    │    • Covers main points (✓✓)           │
    │    • Incomplete (✓)                    │
    │    • Insufficient (✗)                  │
    │                                        │
    │ 4. Recency (current/applicable)        │
    │    • Recent/current (✓✓✓)              │
    │    • Generally applicable (✓✓)         │
    │    • May be outdated (✓)               │
    │    • Clearly outdated (✗)              │
    └──────┬──────────────────────────────────┘
           │
    ┌──────▼──────────────────┐
    │ Calculate Overall Score  │
    │ Σ(criteria scores)       │
    └──────┬──────────────────┘
           │
    ┌──────▼──────────────────────────────┐
    │ Classification                       │
    ├──────────────────────────────────────┤
    │ Score ≥ 0.6: HIGH (keep)            │
    │ Score 0.4-0.6: MEDIUM (evaluate)    │
    │ Score < 0.4: LOW (descope)          │
    └──────┬──────────────────────────────┘
           │
    ┌──────▴──────────────┐
    │   Action            │
    ├─────────────────────┤
    │ HIGH → Keep in      │
    │        active docs  │
    │                     │
    │ MEDIUM → Evaluate   │
    │          in context │
    │                     │
    │ LOW → Move to       │
    │       descoped_docs │
    └─────────────────────┘
```

## Gap Detection Decision Tree

```
For EACH requirement/component:

    Does documentation exist covering this?
    │
    ├─ YES → Is it concrete with examples?
    │        │
    │        ├─ YES → Is it sufficient to build/implement?
    │        │        │
    │        │        ├─ YES → ✓✓✓ WELL COVERED
    │        │        │        └─ Action: KEEP in knowledge
    │        │        │
    │        │        └─ NO → ✗? NEEDS MORE
    │        │               └─ Action: Target in next iteration
    │        │
    │        └─ NO → ✗ OVERVIEW ONLY
    │               └─ Action: DESCOPE weak doc, target in next iteration
    │
    └─ NO → ✗ GAP EXISTS
           └─ Action: Create variants to target this gap
```

## Method Call Flow During Iteration

```
Agent Step 3 Verification
│
├─ Evaluates documents for quality
│  └─ Identifies: 8 high, 5 medium, 2 low quality
│
├─ Assesses coverage
│  └─ Maps docs to requirements
│
├─ Detects gaps
│  └─ "Error handling only overview, no concrete examples"
│
├─ Checks iteration status
│  └─ state.rag_iteration_count = 1 (not at max)
│
├─ Records coverage verification
│  └─ state.record_coverage_verification(
│       iteration=1,
│       requirements=["auth", "validation", "error_handling"],
│       coverage_status={
│         "auth": "covered",
│         "validation": "covered",
│         "error_handling": "gap"
│       },
│       gaps_found=["error_handling"],
│       action="iterate"
│     )
│
├─ Records iteration knowledge
│  └─ state.record_iteration_knowledge(
│       iteration=1,
│       retrieved_docs=[...15 docs...],
│       quality_scores={
│         "high": 8,
│         "medium": 5,
│         "low": 2
│       },
│       targeted_variants=[...]
│     )
│
├─ Descopes weak documents
│  └─ state.descope_weak_documents(
│       ["weak_doc_1_id", "weak_doc_2_id"]
│     )
│       Moves 2 docs to rag_descoped_documents
│       Keeps 13 strong docs in rag_documents
│
├─ Generates targeted variants
│  └─ ["error handling patterns",
│       "exception handling examples",
│       "error recovery strategies",
│       "error logging",
│       "fault tolerance"]
│
├─ Starts next iteration
│  └─ Increments state.rag_iteration_count to 2
│
└─ Loops back to knowledge_expert() call with new variants
```

## Document Accumulation Across Iterations

```
ITERATION 1 RETRIEVED DOCUMENTS
┌─────────────────────────┐
│ Doc 1: Auth ✓✓✓         │
│ Doc 2: Auth ✓✓✓         │
│ Doc 3: Validation ✓✓    │
│ Doc 4: Validation ✓     │  ← To be descoped
│ Doc 5: Error handling ✓ │  ← To be descoped
│ Doc 6-15: Other...      │
└──────────┬──────────────┘
           │ Descope low quality
           │
         ┌─▼───────────────┐
         │ KEPT (13 docs)  │
         │                 │
         │ Iteration 1     │
         │ High Quality    │
         └─┬───────────────┘
           │
┌──────────┼─────────────────────────────────┐
│          │                                 │
│  ITERATION 2 RETRIEVED DOCUMENTS           │
│  ┌────────────────────────┐                │
│  │ Doc 16: Error patterns ✓✓✓              │  New
│  │ Doc 17: Examples ✓✓✓                    │  New
│  │ Doc 18: Frameworks ✓                    │  ← To descope
│  │ Doc 19-23: Other...                     │
│  └────────┬───────────────┘                │
│           │ Descope low quality            │
│           │                                │
│         ┌─▼────────────────┐               │
│         │ KEPT (5 new)     │               │
│         │                  │               │
│         │ Iteration 2      │               │
│         │ Quality Add      │               │
│         └─┬────────────────┘               │
│           │                                │
│  ┌────────▼────────────────────────────┐   │
│  │ ACCUMULATED KNOWLEDGE               │   │
│  │                                     │   │
│  │ Total: 13 (Iter 1) + 5 (Iter 2)    │   │
│  │      = 18 documents                 │   │
│  │                                     │   │
│  │ All high quality, well-organized   │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  Ready for Step 4+ (Task Execution)        │
└─────────────────────────────────────────────┘
```

## State Getter Methods

```
SupervisorAgentState Methods for Iteration Status

├─ state.rag_iteration_count
│  └─ Returns: int (0-3)
│
├─ state.is_max_iterations_reached()
│  └─ Returns: bool (True if count >= 3)
│
├─ state.get_iteration_summary()
│  └─ Returns: {
│       "current_iteration": 2,
│       "max_iterations": 3,
│       "is_max_reached": False,
│       "iterations_history": [...],
│       "coverage_verifications": [...],
│       "active_documents": 18,
│       "descoped_documents": 3
│     }
│
├─ state.coverage_verification_results
│  └─ Returns: List[{
│       "iteration": 1,
│       "requirements": [...],
│       "coverage_status": {...},
│       "gaps_found": [...],
│       "action": "iterate",
│       "timestamp": "..."
│     }]
│
├─ state.rag_iterations_history
│  └─ Returns: List[{
│       "iteration": 1,
│       "doc_count": 15,
│       "quality_scores": {...},
│       "targeted_variants": [...],
│       "timestamp": "..."
│     }]
│
├─ state.rag_documents
│  └─ Returns: List[Dict] (only HIGH quality docs)
│
├─ state.rag_descoped_documents
│  └─ Returns: List[Dict] (filtered out WEAK docs)
│
└─ state.get_execution_summary()
   └─ Returns: {
        ...,
        "rag_iterations": {
          "current_iteration": 2,
          "max_iterations": 3,
          ...
        }
      }
```

---

**Diagram Version**: 1.0
**Last Updated**: 2024-11-13
