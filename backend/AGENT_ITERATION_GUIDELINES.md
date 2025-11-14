# Agent Iteration Guidelines - How to Use the Iterative RAG System

## For LLM Agents Executing the Supervisor Workflow

This guide explains how the agent (LLM) should use the iterative RAG system when executing the 7-step supervisor workflow.

---

## STEP 2.5: Document Quality Assessment

### When You Receive Documents from knowledge_expert

After calling `knowledge_expert` and receiving documents, evaluate them:

#### 1. Read All Documents Carefully
```
For each retrieved document:
├─ Read the content
├─ Understand what it covers
├─ Note what it's missing
└─ Rate its quality
```

#### 2. Score Each Document on 4 Criteria

For each document, ask yourself:

**A) Relevance to Requirements** (Does it address user needs?)
- ✓✓✓ Direct match to requirement
- ✓✓ Partially relevant
- ✓ Tangentially related
- ✗ Not relevant at all

**B) Concreteness** (Does it include examples/code?)
- ✓✓✓ Concrete examples or code included
- ✓✓ Some guidance with examples
- ✓ Theoretical/conceptual only
- ✗ Too vague to use

**C) Completeness** (Is it thorough?)
- ✓✓✓ Comprehensive explanation
- ✓✓ Covers main points
- ✓ Incomplete coverage
- ✗ Insufficient information

**D) Recency** (Is it current?)
- ✓✓✓ Recent and up-to-date
- ✓✓ Generally applicable
- ✓ May be outdated
- ✗ Clearly outdated

#### 3. Calculate Overall Quality

Sum the scores:
- 10-12: **HIGH** (✓✓✓) → Keep
- 7-9: **MEDIUM** (✓✓) → Evaluate in context
- 4-6: **LOW** (✓) → Consider descoping
- 0-3: **NONE** (✗) → Descope

**Rule of Thumb**: Documents scoring ≥ 0.6 (normalized) should be kept, < 0.4 should be descoped.

#### Example Document Quality Assessment

```
Document: "Introduction to OAuth2"

Relevance: User asked "Build secure API with OAuth"
├─ Does it cover OAuth? YES ✓✓✓
└─ Is it relevant to requirement? Direct match ✓✓✓

Concreteness: Document contains...
├─ Theoretical explanation? YES
├─ Flow diagrams? YES ✓✓✓
├─ Code examples? NO ✗
└─ Best practices? YES ✓
Result: ✓✓ (has diagrams but no code examples)

Completeness: Covers...
├─ OAuth2 concepts? YES ✓✓✓
├─ Flow types? Partial (only covers authorization code) ✓
├─ Implementation patterns? NO ✗
└─ Error handling? NO ✗
Result: ✓ (incomplete for implementation)

Recency:
├─ Published date? 2023 ✓✓
├─ Still applicable? YES ✓✓
└─ Covers latest standards? YES ✓✓✓
Result: ✓✓✓ (current)

Overall Score: 3+2+1+3 = 9
Classification: MEDIUM QUALITY (✓✓)
Action: Keep but note it lacks implementation examples
```

---

## STEP 3: Coverage Verification with Iteration Awareness

### When You Verify Coverage

After receiving documents and assessing quality, verify coverage:

#### 1. Map Requirements to Documents

For each requirement from STEP 1:
```
Requirement: "Error handling with logging"
├─ Do you have documents covering error handling? YES
├─ Do you have documents covering logging? YES
├─ Are both concrete with examples?
│  ├─ Error handling: Partial (concepts only)
│  └─ Logging: YES (full implementation guide)
└─ Coverage Status: PARTIAL ✓ (not ✓✓✓)
```

#### 2. Identify Specific Gaps

When coverage is incomplete, be SPECIFIC:

❌ **WRONG**: "Need more information"
✅ **CORRECT**: "Error handling docs show concepts but no try-catch/exception patterns. Need concrete implementation examples."

❌ **WRONG**: "Missing validation"
✅ **CORRECT**: "Have basic validation overview but missing: input sanitization patterns, custom validators, async validation examples."

#### 3. Check Iteration Count

```python
# Pseudocode for agent decision logic

current_iteration = track_your_iterations()  # You're on iteration 1, 2, or 3

if all_requirements_covered:
    proceed_to_step_4()
else:
    if current_iteration < 3:
        # Gaps found AND can iterate
        identify_specific_gaps()
        generate_targeted_variants()
        call_knowledge_expert_again()
        loop_back_to_step_2_5()
    else:
        # Max iterations reached
        document_gaps()
        proceed_to_step_4_with_best_available()
```

#### 4. Make the Iteration Decision

**Decision Tree**:

```
Do you have coverage for ALL requirements?
│
├─ YES → ✓ PROCEED TO STEP 4
│        └─ You have sufficient knowledge to proceed
│
└─ NO → Are you on iteration 1 or 2?
        │
        ├─ YES (iteration 1 or 2) → ITERATE AGAIN
        │   ├─ Identify specific gaps
        │   ├─ Descope weak documents (keep only quality > 0.6)
        │   ├─ Generate NEW, more specific variants
        │   └─ Call knowledge_expert again
        │
        └─ NO (iteration 3 - MAX REACHED) → PROCEED ANYWAY
            ├─ Document what gaps remain
            ├─ Select strongest docs from all iterations
            └─ Proceed to Step 4 (may need to work around gaps)
```

#### 5. Document Your Decision

Be explicit in your reasoning:

**Example 1: Coverage Complete**
```
STEP 3 VERIFICATION RESULT:
Iteration: 1/3
Requirements to verify:
├─ Authentication: ✓✓✓ (comprehensive OAuth guide + examples)
├─ Database setup: ✓✓✓ (schema design + migration examples)
├─ Error handling: ✓✓ (concepts + logging patterns)
└─ Security: ✓✓ (best practices + validation patterns)

Coverage Status: ALL REQUIREMENTS COVERED ✅
Action: PROCEED TO STEP 4
```

**Example 2: Gaps Detected - Iterate**
```
STEP 3 VERIFICATION RESULT:
Iteration: 1/3
Requirements to verify:
├─ Authentication: ✓✓✓ (comprehensive)
├─ API rate limiting: ✗ (NO DOCUMENTS FOUND)
├─ Caching strategy: ✓ (overview only, no implementation)
└─ Monitoring: ✓✓ (has examples but incomplete)

Coverage Status: GAPS DETECTED ❌
Specific gaps:
1. Rate limiting: MISSING completely
2. Caching: Needs implementation examples
3. Monitoring: Needs operational patterns

Action: ITERATE TO ITERATION 2
New variants for knowledge_expert:
- "API rate limiting implementation"
- "request throttling and backoff strategies"
- "cache invalidation patterns"
- "monitoring and observability setup"
- "metrics collection and alerting"
```

**Example 3: Max Iterations Reached**
```
STEP 3 VERIFICATION RESULT:
Iteration: 3/3 (MAX)
Requirements to verify:
├─ Authentication: ✓✓✓ (comprehensive)
├─ Rate limiting: ✓✓ (strategies from Iter 2)
├─ Caching: ✓ (basic patterns, not ideal)
├─ Monitoring: ✓✓ (improved from Iter 2)
└─ Cost optimization: ✗ (NOT IN KNOWLEDGE BASE)

Coverage Status: GAPS EXIST BUT MAX ITERATIONS REACHED
Gaps that remain:
- Cost optimization: No knowledge base resources found after 3 iterations

Action: PROCEED TO STEP 4
Note for Step 5: Cost optimization may require using training data or noting as limitation to user
```

---

## Between Iterations: Document Descoping

### When Moving from Iteration 1 → 2 or 2 → 3

Before calling knowledge_expert again:

#### 1. Identify Weak Documents

```
Review all current documents:

Doc 1: "Introduction to OAuth2"
├─ Relevance to requirement: YES
├─ Quality score: 0.7 (above threshold ≥ 0.6)
└─ Action: KEEP

Doc 2: "OAuth2 History and Evolution"
├─ Relevance to requirement: TANGENTIAL
├─ Quality score: 0.3 (below threshold)
└─ Action: DESCOPE

Doc 3: "Basic error handling concepts"
├─ Relevance to requirement: YES but vague
├─ Quality score: 0.35 (below threshold)
└─ Action: DESCOPE

Doc 4: "Error handling patterns and examples"
├─ Relevance to requirement: YES
├─ Quality score: 0.8 (above threshold)
└─ Action: KEEP
```

#### 2. Explicitly Remove Low-Quality Documents

```python
# In your reasoning, identify which documents to filter:

Documents to DESCOPE (quality < 0.6):
├─ "OAuth2 History and Evolution" (tangential, historical)
├─ "Basic error handling concepts" (too vague for implementation)
├─ "Legacy validation approaches" (outdated patterns)
└─ [Any duplicative content]

Documents to KEEP (quality ≥ 0.6):
├─ "OAuth2 implementation guide" (concrete, current)
├─ "Error handling patterns" (specific examples)
└─ [Other high-quality documents]

New active document count: 15 (from 18)
Descoped: 3 documents
```

#### 3. Generate New Targeted Variants

For Iteration 2, your variants should be:
- **Different** from Iteration 1 (not repeating)
- **More specific** (targeting identified gaps)
- **Targeted** at weak areas

```
Iteration 1 Variants (broad):
├─ "OAuth2 implementation"
├─ "API authentication setup"
├─ "error handling patterns"
├─ "exception handling best practices"
└─ "security practices for APIs"

Iteration 2 Variants (specific to gaps):
├─ "OAuth2 token management and refresh strategies"
├─ "OAuth2 scope and permissions implementation"
├─ "error response patterns and HTTP status codes"
├─ "exception logging and monitoring"
└─ "API error handling middleware"

Note: Completely different variants, targeting specific gaps!
```

---

## Task-Specific Iteration Patterns

### Pattern A: Simple Information Query

```
User: "What is OAuth2?"

STEP 1: Identify requirements
└─ User wants conceptual understanding of OAuth2

STEP 2: Call knowledge_expert
└─ variants: ["OAuth2 overview", "OAuth2 flow", "OAuth2 vs OAuth1", ...]

STEP 2.5: Assess documents
├─ Found: Comprehensive OAuth2 guide ✓✓✓
├─ Found: Flow diagrams ✓✓✓
├─ Found: Comparison with OAuth1 ✓✓✓
└─ Quality: All high quality

STEP 3: Verify coverage
└─ All conceptual requirements covered ✓

ACTION: PROCEED TO STEP 4 (1 iteration, no gaps)
```

### Pattern B: Implementation with Gaps

```
User: "Build REST API with authentication, validation, and logging"

STEP 1: Identify requirements
├─ Authentication implementation
├─ Input validation
├─ Logging infrastructure
└─ Error handling (implied)

STEP 2: Call knowledge_expert (Iteration 1)
└─ variants: ["REST API setup", "API authentication", "validation", "logging", ...]

STEP 2.5: Assess documents (Iteration 1)
├─ REST API: ✓✓✓ (comprehensive)
├─ Authentication: ✓✓✓ (good examples)
├─ Validation: ✓ (overview only)
├─ Logging: ✗ (no documents)
└─ Quality distribution: 50% high, 25% medium, 25% low

STEP 3: Verify coverage (Iteration 1)
├─ Requirements covered: 60%
├─ Gaps found: ["validation examples", "logging setup"]
├─ Iteration 1/3: CAN ITERATE
└─ ACTION: DESCOPE weak validation docs, iterate

--- Descope weak documents ---
├─ Documents descoped: 3 (low quality validation docs)
├─ Documents kept: 12 (high quality)

STEP 2: Call knowledge_expert (Iteration 2)
└─ New variants: ["input validation patterns", "validation middleware", "application logging", "logging setup", "error logging"]

STEP 2.5: Assess documents (Iteration 2)
├─ Validation patterns: ✓✓✓ (implementation examples)
├─ Logging setup: ✓✓✓ (comprehensive guide)
└─ Quality: All new docs are high quality

STEP 3: Verify coverage (Iteration 2)
├─ Requirements covered: 100%
├─ All gaps resolved
└─ ACTION: PROCEED TO STEP 4 (2 iterations used)

STEP 4-7: Proceed with task execution
└─ Use knowledge from both iterations (15 high-quality documents)
```

### Pattern C: Complex Multi-Component with Max Iterations

```
User: "Build system with: auth, validation, logging, caching, monitoring, rate limiting"

ITERATION 1:
├─ Call knowledge_expert with broad variants
├─ Retrieve: auth ✓, validation ✓, logging ✗
├─ Coverage: 33% (3/6 components)
├─ ACTION: Iterate

ITERATION 2:
├─ Descope weak validation docs
├─ Call knowledge_expert with: "logging", "system monitoring", "observability"
├─ Retrieve: logging ✓✓, monitoring ✓, caching ✓
├─ Coverage: 83% (5/6 components)
├─ Missing: rate limiting
├─ ACTION: Iterate (on iteration 2/3)

ITERATION 3 (MAX):
├─ Descope weak docs from iterations 1-2
├─ Call knowledge_expert with: "API rate limiting", "request throttling", "backoff strategies"
├─ Retrieve: rate limiting ✓✓
├─ Coverage: 100% (6/6 components)
├─ Iteration 3/3: MAX REACHED
├─ ACTION: PROCEED to Step 4

RESULT:
├─ All components covered
├─ 3 iterations used
├─ 20+ high-quality documents accumulated
└─ Ready for task execution
```

### Pattern D: Unfulfillable Requirement

```
User: "Build system with: auth, validation, logging, AI-powered recommendations"

ITERATION 1:
├─ Get: auth, validation, logging
├─ Missing: AI recommendations
├─ ACTION: Iterate

ITERATION 2:
├─ Try: "AI recommendations", "machine learning API", "recommendation engine"
├─ Result: No relevant documents in KB
├─ Still missing: AI recommendations
├─ ACTION: Iterate (attempt once more)

ITERATION 3 (MAX):
├─ Try: "recommendation systems", "AI services", "predictive features"
├─ Result: Still no relevant documents
├─ MAX ITERATIONS REACHED
├─ Final status:
│  ├─ auth: ✓✓✓
│  ├─ validation: ✓✓✓
│  ├─ logging: ✓✓✓
│  └─ AI recommendations: ✗ (NOT IN KNOWLEDGE BASE)
└─ ACTION: PROCEED to Step 4, note limitation

STEP 7 (Final Response):
└─ "Built system with auth, validation, logging as requested.
    Note: AI-powered recommendations not available in knowledge base.
    Recommend: using external AI service or noting as future enhancement."
```

---

## Decision Flowchart for Agents

```
START: You have documents from knowledge_expert

1. Assess document quality
   ├─ Score each document (1-4 on 4 criteria)
   └─ Classify: HIGH (≥0.6), MEDIUM (0.4-0.6), LOW (<0.4)

2. Verify coverage against requirements
   ├─ For each requirement, do you have documents?
   ├─ Do those documents answer the requirement?
   └─ Are they of sufficient quality?

3. Determine coverage status
   ├─ NO gaps found → ✓ PROCEED TO STEP 4
   └─ YES gaps found → Check iteration count

4. Check iteration count
   ├─ Iteration 1 or 2?
   │  ├─ YES → Descope weak docs
   │  ├─ Generate targeted variants
   │  ├─ Call knowledge_expert again
   │  └─ Loop back to step 1
   └─ Iteration 3?
      ├─ YES → You're at MAX
      ├─ Document remaining gaps
      ├─ Select best available docs
      └─ PROCEED TO STEP 4

END: Either proceed to Step 4 or iterate again
```

---

## Prompting Tips for Better Iterations

### Iteration 1: Broad Coverage
```
"I need comprehensive information about [topic]. Please retrieve:
- Overview and concepts
- Implementation approaches
- Best practices
- Common patterns
- Practical examples"
```

### Iteration 2: Targeted Enrichment
```
"I have [what you found] but need more detail on: [specific gaps].
Please retrieve:
- [Gap 1] implementation examples
- [Gap 2] code patterns
- [Gap 3] best practices
- Concrete use cases"
```

### Iteration 3: Final Deep Dive
```
"Final iteration to address remaining gaps. I need:
- [Most specific gap] with real-world examples
- [Edge case handling] patterns
- [Performance considerations]
- [Security aspects] for [specific domain]"
```

---

## Key Reminders

1. **Be Specific About Gaps**: "Validation examples missing" not "Need more info"
2. **Quality Over Quantity**: One high-quality doc beats three weak ones
3. **Targeted Variants**: Each iteration should use completely different query angles
4. **Respect Max Iterations**: After 3 iterations, you MUST proceed (don't loop endlessly)
5. **Document Decisions**: Explain why you're iterating or proceeding
6. **Track Quality**: Use the 4-criteria scoring system consistently
7. **Descope Progressively**: Each iteration should improve document quality
8. **Note Gaps**: If max iterations reached, explicitly document what couldn't be covered

---

## Examples of Good vs Poor Agent Behavior

### ❌ POOR - Skipping Quality Assessment

```
"I retrieved 20 documents. I'll just use all of them.
[Proceeds to tool with 20 docs of mixed quality]"

Problem: Weak documents dilute quality and confuse task execution
```

### ✅ GOOD - Quality Assessment

```
"I retrieved 20 documents. Quality assessment:
- 12 high quality (concrete examples, recent)
- 5 medium quality (useful but incomplete)
- 3 low quality (vague, outdated, tangential)

I'll use the 12 high-quality documents and note that
authentication examples are weak. Moving to Iteration 2."
```

---

### ❌ POOR - Vague Gap Identification

```
"Coverage is incomplete. Need more information."
[Calls knowledge_expert with same variants as before]

Problem: Same queries return same results
```

### ✅ GOOD - Specific Gap Identification

```
"Coverage assessment:
- Authentication: ✓ (comprehensive)
- Input validation: ✓ (overview only, MISSING: regex patterns, custom validators)
- Error logging: ✗ (NO DOCUMENTS FOUND)

Gap analysis:
1. Validation needs: regex pattern examples, async validator patterns
2. Error logging needs: logging configuration, error serialization

Iteration 2 variants will target these specific gaps with new angles."
```

---

### ❌ POOR - Ignoring Iteration Limits

```
"Coverage still incomplete after 3 iterations.
[Calls knowledge_expert for 4th iteration]"

Problem: Violates max iteration rule
```

### ✅ GOOD - Respecting Iteration Limits

```
"After 3 iterations:
- Component A: ✓✓✓ (complete)
- Component B: ✓✓ (good coverage)
- Component C: ✓ (partial - not in KB)
- Component D: ✗ (gap - not in KB)

Max iterations (3) reached. Proceeding to Step 4 with best available knowledge.
Gaps: Components C and D incomplete. Will generate with training data and note limitations."
```

---

## Summary for Agents

**The Iterative RAG System allows you to**:
1. ✅ Retrieve knowledge up to 3 times
2. ✅ Progressively filter weak documents
3. ✅ Verify coverage against user requirements
4. ✅ Generate targeted variants for identified gaps
5. ✅ Know when to proceed (all covered or max iterations reached)

**Use this to**:
- Ensure comprehensive knowledge before proceeding
- Quality-filter documents automatically
- Identify specific gaps and target them
- Stop after 3 iterations to avoid infinite loops
- Deliver higher-quality results with complete knowledge

---

**Remember**: The goal is COMPREHENSIVE COVERAGE by max 3 iterations, with HIGH-QUALITY documents, before proceeding to task execution.
