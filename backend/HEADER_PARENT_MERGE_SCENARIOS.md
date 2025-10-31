# Header-First with Parent Merging - All Scenarios

## Algorithm Summary

1. **Split by headers** (hierarchical)
2. **For each chunk:**
   - If chunk < MIN_SIZE → Try merge into parent
   - If chunk > MAX_SIZE → Split by paragraphs/sentences
   - Otherwise → Keep as-is

## Scenario Analysis

---

## Scenario 1: Small Child Under Large Parent ✅

```markdown
# Parent Header (1000 tokens total)
Parent content here... (800 tokens)

## Small Child (50 tokens)
Brief content

## Another Small Child (100 tokens)
More brief content
```

### Initial Split (by headers)
- Chunk 1: "Parent Header" (800 tokens)
- Chunk 2: "Small Child" (50 tokens) ❌ Too small
- Chunk 3: "Another Small Child" (100 tokens) ❌ Too small

### After Parent Merge
- **Chunk 1: "Parent Header"** (950 tokens) ✅
  - Merged: Parent (800) + Small Child (50) + Another Small Child (100)
- Total: 1 chunk

### ✅ Result: Perfect! Small children merged into parent.

---

## Scenario 2: Small Child + Parent Already At Max ❌ PROBLEM

```markdown
# Parent Header (800 tokens)
Parent content...

## Small Child (150 tokens)
Child content
```

### Initial Split
- Chunk 1: "Parent" (800 tokens)
- Chunk 2: "Small Child" (150 tokens) ❌ Too small

### Merge Attempt
- Parent (800) + Child (150) = **950 tokens** ✅ Under MAX (1000)
- **Merge successful**

### ✅ Result: Works! Combined = 950 tokens

---

## Scenario 3: Small Child + Parent Would Exceed Max ❌ CRITICAL PROBLEM

```markdown
# Parent Header (900 tokens)
Parent content...

## Small Child (150 tokens)
Child content
```

### Initial Split
- Chunk 1: "Parent" (900 tokens)
- Chunk 2: "Small Child" (150 tokens) ❌ Too small

### Merge Attempt
- Parent (900) + Child (150) = **1050 tokens** ❌ Exceeds MAX (1000)
- **Merge FAILED**

### ❌ Problem: Child remains too small!

### 🔧 Solution Options:
**Option A:** Keep small chunk anyway (accept noise)
**Option B:** Force merge, exceed MAX temporarily
**Option C:** Split parent first, then merge child into last part

**Recommended: Option C**
- Split parent into: Part 1 (500) + Part 2 (400)
- Merge child into Part 2: (400 + 150 = 550) ✅
- Result: 2 chunks (500, 550)

---

## Scenario 4: Multiple Levels Deep 🤔

```markdown
# Level 1 (800 tokens)
Content...

## Level 2 (700 tokens)
Content...

### Level 3 Small (50 tokens)
Brief content

### Level 3 Another Small (80 tokens)
More brief
```

### Initial Split
- Chunk 1: "Level 1" (800 tokens)
- Chunk 2: "Level 2" (700 tokens)
- Chunk 3: "Level 3 Small" (50 tokens) ❌ Too small
- Chunk 4: "Level 3 Another Small" (80 tokens) ❌ Too small

### Parent Merge Strategy
**Question:** Merge into immediate parent (Level 2) or grandparent (Level 1)?

**Answer: Immediate parent (Level 2)**

### Merge Process
1. "Level 3 Small" (50) → Merge into "Level 2"
   - Level 2: 700 + 50 = 750 ✅
2. "Level 3 Another Small" (80) → Merge into "Level 2"
   - Level 2: 750 + 80 = 830 ✅

### ✅ Result
- Chunk 1: "Level 1" (800 tokens)
- Chunk 2: "Level 2" (830 tokens) - includes both Level 3 children
- Total: 2 chunks

---

## Scenario 5: Small Child Has No Parent ❌ EDGE CASE

```markdown
## Orphan Child (50 tokens)
This is a level 2 header at the top

# Parent Comes Later (800 tokens)
Content...
```

### Initial Split
- Chunk 1: "Orphan Child" (50 tokens) ❌ Too small, NO PARENT
- Chunk 2: "Parent Comes Later" (800 tokens)

### 🔧 Solution Options:
**Option A:** Merge with next sibling (same level)
**Option B:** Merge with first parent-like chunk below
**Option C:** Keep as-is (accept noise)

**Recommended: Option B**
- Merge "Orphan Child" into "Parent Comes Later"
- Result: 1 chunk (850 tokens)

---

## Scenario 6: All Children Small, Parent Also Small

```markdown
# Small Parent (100 tokens)
Brief intro

## Small Child 1 (80 tokens)
Brief content

## Small Child 2 (90 tokens)
More brief
```

### Initial Split
- Chunk 1: "Parent" (100 tokens) ❌ Too small
- Chunk 2: "Child 1" (80 tokens) ❌ Too small
- Chunk 3: "Child 2" (90 tokens) ❌ Too small

### Merge Process
1. "Child 1" (80) → Merge into "Parent"
   - Parent: 100 + 80 = 180 ✅ Still small but improving
2. "Child 2" (90) → Merge into "Parent"
   - Parent: 180 + 90 = 270 ✅ Above MIN (200)

### ✅ Result
- Chunk 1: "Small Parent" (270 tokens) ✅
- Total: 1 chunk

---

## Scenario 7: Large Section That Needs Splitting

```markdown
# Huge Parent (2000 tokens)
Lots of content with no sub-headers...
Just paragraphs and paragraphs...

## Small Child (100 tokens)
Brief
```

### Initial Split
- Chunk 1: "Huge Parent" (2000 tokens) ❌ Too large
- Chunk 2: "Small Child" (100 tokens) ❌ Too small

### Processing Order Matters!

#### ❌ Wrong Order: Merge first, then split
1. Merge child into parent: 2000 + 100 = 2100
2. Split 2100 tokens → Loses structure, child content scattered

#### ✅ Correct Order: Split first, then merge
1. Split parent by paragraphs:
   - Parent Part 1: 500 tokens
   - Parent Part 2: 500 tokens
   - Parent Part 3: 500 tokens
   - Parent Part 4: 500 tokens
2. Merge child into last part:
   - Parent Part 4: 500 + 100 = 600 tokens

### ✅ Result
- Chunk 1: "Huge Parent - Part 1" (500 tokens)
- Chunk 2: "Huge Parent - Part 2" (500 tokens)
- Chunk 3: "Huge Parent - Part 3" (500 tokens)
- Chunk 4: "Huge Parent - Part 4" (600 tokens) - includes child
- Total: 4 chunks

---

## Scenario 8: Chain of Small Sections

```markdown
# Parent (800 tokens)
Content...

## Child A (50 tokens)
Brief

### Grandchild A1 (40 tokens)
Very brief

### Grandchild A2 (60 tokens)
Brief too
```

### Initial Split
- Chunk 1: "Parent" (800 tokens)
- Chunk 2: "Child A" (50 tokens) ❌ Too small
- Chunk 3: "Grandchild A1" (40 tokens) ❌ Too small
- Chunk 4: "Grandchild A2" (60 tokens) ❌ Too small

### Merge Strategy: Bottom-Up

**Step 1:** Merge grandchildren into parent (Child A)
- Child A: 50 + 40 + 60 = 150 tokens (still small but better)

**Step 2:** Merge Child A into Parent
- Parent: 800 + 150 = 950 tokens ✅

### ✅ Result
- Chunk 1: "Parent" (950 tokens) - includes all descendants
- Total: 1 chunk

---

## Scenario 9: Sibling Without Common Parent

```markdown
# Section A (800 tokens)
Content A

# Section B (100 tokens)
Brief content B

# Section C (800 tokens)
Content C
```

### Initial Split
- Chunk 1: "Section A" (800 tokens)
- Chunk 2: "Section B" (100 tokens) ❌ Too small, NO PARENT (top-level)
- Chunk 3: "Section C" (800 tokens)

### 🔧 Solution for Top-Level Small Chunks:
**Option A:** Merge with previous sibling
- Section A: 800 + 100 = 900 ✅

**Option B:** Merge with next sibling
- Section C: 100 + 800 = 900 ✅

**Option C:** Keep as-is

**Recommended: Option A (merge with previous)**
- More natural reading flow
- Preserves order

### ✅ Result
- Chunk 1: "Section A + Section B" (900 tokens)
- Chunk 2: "Section C" (800 tokens)
- Total: 2 chunks

---

## Scenario 10: Deeply Nested Small Sections

```markdown
# L1 (500 tokens)
## L2 (400 tokens)
### L3 (300 tokens)
#### L4 Small (50 tokens)
##### L5 Tiny (30 tokens)
```

### Initial Split
- Chunk 1: "L1" (500 tokens)
- Chunk 2: "L2" (400 tokens)
- Chunk 3: "L3" (300 tokens)
- Chunk 4: "L4 Small" (50 tokens) ❌ Too small
- Chunk 5: "L5 Tiny" (30 tokens) ❌ Too small

### Bottom-Up Merge
1. L5 (30) → Merge into L4: 50 + 30 = 80 (still small)
2. L4 (80) → Merge into L3: 300 + 80 = 380 ✅

### ✅ Result
- Chunk 1: "L1" (500 tokens)
- Chunk 2: "L2" (400 tokens)
- Chunk 3: "L3" (380 tokens) - includes L4 and L5
- Total: 3 chunks

---

## Edge Cases Summary

| Scenario | Issue | Solution |
|----------|-------|----------|
| **Small child + parent at max** | Merge exceeds max | Split parent first, merge child into last part |
| **Small orphan (no parent)** | No parent to merge into | Merge with previous/next sibling |
| **Top-level small section** | No parent (level 1) | Merge with previous sibling |
| **Large section to split** | Contains small children | Split parent first, THEN merge children |
| **Chain of small nested** | Multiple levels small | Bottom-up merge (grandchild→child→parent) |

---

## Algorithm Refinement

Based on all scenarios, here's the refined algorithm:

```python
def adaptive_header_split(markdown_text, min_size=200, max_size=1000):
    # Step 1: Split by headers (preserve hierarchy)
    sections = split_by_headers_hierarchical(markdown_text)

    # Step 2: Build parent-child tree
    tree = build_hierarchy_tree(sections)

    # Step 3: Process tree BOTTOM-UP (leaves to root)
    process_bottom_up(tree):
        for node in reversed(tree.traverse()):  # Reverse = bottom-up

            # If node too large, split it first
            if node.size > max_size:
                node.split_by_paragraphs()

            # If node too small, merge into parent
            if node.size < min_size:
                if node.parent:
                    # Check if merge fits
                    if node.parent.size + node.size <= max_size:
                        node.parent.merge_child(node)
                    else:
                        # Parent too full, split parent first
                        node.parent.split_smartly()
                        # Retry merge into last part
                        node.parent.parts[-1].merge_child(node)
                else:
                    # No parent (top-level), merge with sibling
                    merge_with_previous_sibling(node)

    # Step 4: Collect final chunks
    return tree.get_leaf_chunks()
```

---

## Critical Decision Points

### 1. Processing Order
**✅ MUST process bottom-up (children before parents)**
- Ensures children are merged before parent size decisions

### 2. When Parent + Child > Max
**✅ Split parent first, then merge child into last part**
- Preserves semantic structure
- Avoids orphaning small chunks

### 3. Top-Level Small Sections
**✅ Merge with previous sibling**
- Maintains reading flow
- Natural grouping

### 4. Large Section with Children
**✅ Split parent BEFORE merging children**
- Prevents scattering child content
- Keeps children with relevant parent section

---

## Recommended Parameters

```python
MIN_CHUNK_SIZE = 200   # Prevent noisy chunks
TARGET_CHUNK_SIZE = 500  # Ideal size (not enforced, just guidance)
MAX_CHUNK_SIZE = 1000    # Hard limit for embedding models
CHUNK_OVERLAP = 50       # For context continuity
```

---

## Questions for You

1. **When merge exceeds max:** Split parent first then merge child? (Recommended: YES)

2. **Top-level small sections:** Merge with sibling or keep as-is? (Recommended: MERGE)

3. **Multiple small children:** Merge all into parent or keep separate? (Recommended: MERGE ALL)

4. **Processing order:** Bottom-up or top-down? (Recommended: BOTTOM-UP)

5. **Large section splitting:** By paragraphs or by target size? (Recommended: PARAGRAPHS first, then size if needed)

Let me know which scenarios need different handling!
