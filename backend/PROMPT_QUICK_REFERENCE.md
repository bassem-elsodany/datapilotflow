# Supervisor Agent Prompt - Quick Reference

## The 5-Step Workflow

```
┌──────────────────────────────────────────────────────┐
│ STEP 1: ANALYZE USER INTENT & PLAN                   │
│ └─ Understand request type (Q&A vs task)             │
│ └─ Identify components & requirements                │
│ └─ Generate 5 knowledge variants                     │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│ STEP 2: CALL knowledge_expert (ALL 5 VARIANTS)       │
│ └─ search_query=["v1", "v2", "v3", "v4", "v5"]      │
│ └─ No preamble text, just call                      │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│ STEP 3: EVALUATE & ITERATE (IF NEEDED)               │
│                                                       │
│ For each requirement:                                │
│   Coverage? [YES/NO]                                │
│   Quality?  [YES/NO] (concrete examples)            │
│   Complete? [YES/NO] (sufficient to proceed)        │
│                                                       │
│ ✅ All YES → Proceed to STEP 4                       │
│ ⚠️  Any NO → Iterate (new variants)                  │
│ 🛑 After 3 calls → Proceed to STEP 4                │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│ STEP 4: DECIDE IF TOOLS NEEDED                       │
│ └─ Q&A/explain → No tools, answer from knowledge    │
│ └─ Generate/build → Use tools next                  │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│ STEP 5: EXECUTE TOOLS + VERIFY                       │
│ └─ Call tool with COMPLETE RAG context              │
│ └─ Verify result meets all requirements             │
│ └─ If incomplete → Loop back to RAG                 │
│ └─ If complete → Proceed to STEP 6                  │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│ STEP 6: FINAL RESPONSE TO USER                       │
│ └─ Output result (no internal analysis)              │
│ └─ Add citations naturally                           │
│ └─ Mark satisfied requirements (optional)            │
└──────────────────────────────────────────────────────┘
```

## Iteration Decision Logic

```
After knowledge_expert call:

For each component/requirement:
  ├─ Coverage: Do I have docs? [YES/NO]
  ├─ Quality: Concrete examples? [YES/NO]
  └─ Complete: Sufficient info? [YES/NO]

Decision:
  ├─ All YES/YES/YES? → Proceed (stop evaluating)
  ├─ Any NO? → Iterate (call again with NEW variants)
  └─ Called 3 times? → Proceed (max reached)
```

## When to Iterate

**DO iterate when:**
- Specific gap identified: "Error handling docs exist but no code examples"
- Gap is critical: "User explicitly asked for error handling"
- Haven't reached limit: "This is only iteration 2 of 3"

**DON'T iterate when:**
- All requirements covered: "All components have concrete examples"
- Uncertain if needed: "Maybe I'll iterate just in case" ← NO
- Already called 3 times: "Max reached, proceed regardless"

## Iteration Variant Creation

**First call (STEP 2):**
```
["exact user request",
 "alternative phrasing",
 "technical version",
 "foundational concepts",
 "integration aspects"]
```

**Second call (if gap on error handling):**
```
["error handler implementation code",
 "try-catch exception patterns",
 "error response examples",
 "fault tolerance patterns",
 "exception recovery strategies"]
```

**Key:** Each iteration uses COMPLETELY DIFFERENT variants targeting the specific gap.

## Tool Context Passing

❌ **WRONG:**
```python
tool_call(
  input="Generate flow",
  context="Based on doc1 and doc2, error handling patterns typically..."
)
```

✅ **CORRECT:**
```python
tool_call(
  input="Generate flow",
  rag_context={
    "documents": [doc1, doc2, doc3, ...all retrieved documents],
    "metadata": {...},
    "sources": [...]
  }
)
```

## Critical Constraints

| Constraint | Why |
|-----------|-----|
| knowledge_expert FIRST | Ensures knowledge-based reasoning |
| 5 variants per call | RRF fusion for comprehensive coverage |
| Max 3 calls | Prevents infinite loops, sets clear boundary |
| NEW variants on iterate | Avoids redundant searches |
| FULL context to tools | Tools need complete picture |
| Verify before output | Ensures result meets requirements |

## Output Format

❌ **Don't include:**
- Internal analysis
- Coverage checklists
- Iteration details
- Reasoning process
- "I evaluated documents as..."

✅ **Do include:**
- Final result
- Helpful context
- Source citations
- Requirement satisfaction (optional brief ✅)

## Common Patterns

### Pattern 1: Simple Q&A
```
Step 1: Analyze question
Step 2: Call knowledge_expert with 5 Q&A variants
Step 3: Evaluate (should be sufficient)
Step 4: No tools needed
Step 5: Skip tools
Step 6: Output answer with citations
```

### Pattern 2: Generation with Iteration
```
Step 1: Decompose requirements (e.g., component + error handling)
Step 2: Call knowledge_expert with 5 variants
Step 3: Evaluate → Find gap in error handling
Step 2 (again): Call with NEW error-handling-focused variants
Step 3 (again): Evaluate → Now complete
Step 4: Tools needed
Step 5: Execute tool with complete context
Step 6: Output generated artifact
```

### Pattern 3: Incomplete Result Verification
```
Step 1-5: Generate result
Step 5: Verify → Missing error handling ❌
Step 2 (again): Call knowledge_expert with error handling variants
Step 3 (again): Evaluate → Get more docs
Step 5 (again): Call tool again with enriched context
Step 5: Verify → Now complete ✅
Step 6: Output refined result
```

## Key Differences from Original Prompt

| Aspect | Original | New |
|--------|----------|-----|
| Length | 732 lines | 273 lines |
| "Work silently" | Claimed impossible | Removed claim |
| Step 2.5 | 202 lines of detail | Integrated into STEP 3 |
| Evaluation | Complex examples | Simple YES/NO checklist |
| Examples | 5 detailed scenarios | 2 focused scenarios |
| Iteration logic | Vague guidance | Clear decision rules |
| Constraints | Scattered throughout | Single table |

## Remember

✅ The LLM reasons about requirements
✅ Variants are created by LLM based on understanding
✅ Evaluation of sufficiency is LLM's judgment call
✅ Iteration is intelligent, not automatic
✅ 3 calls is max, not goal
✅ Tools get complete context
✅ User sees final result only
