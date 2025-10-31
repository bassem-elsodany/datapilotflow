# Real Markdown Splitting Scenarios - Based on Actual Code

## Current Implementation Analysis

### Your Code Flow:
```python
# In MarkdownSplitter.split():

1. STAGE 1: Split by headers using MarkdownHeaderTextSplitter
   → Creates chunks based on header hierarchy
   → Returns: List[Document] with header metadata

2. STAGE 2: Token enforcement (only if max_tokens configured)
   → For each header-based chunk:
     - Count tokens
     - If chunk_tokens <= max_tokens → Keep as-is ✅
     - If chunk_tokens > max_tokens → Apply RecursiveCharacterTextSplitter ❌
       - Uses job's chunk_size and chunk_overlap
       - Splits by: ["\n\n", "\n", " ", ""] (paragraphs, lines, words, chars)
```

### Your Identified Problems:

**Case 1: Large header sections**
- Header chunk exceeds max_tokens
- Falls back to RecursiveCharacterTextSplitter
- **Problem:** Creates small noisy fragments

**Case 2: Small header sections**
- Header chunk is very small (e.g., 20 tokens)
- **Problem:** Creates noisy low-information chunks

---

## Real Scenarios from YOUR Code

### Scenario 1: Normal Case - Small

 Sections ✅

```markdown
# Introduction (150 tokens)
This is the intro...

## Features (200 tokens)
Here are the features...

## Installation (180 tokens)
To install...
```

#### Current Behavior:
**STAGE 1 (Header Split):**
- Chunk 1: "# Introduction" (150 tokens)
- Chunk 2: "## Features" (200 tokens)
- Chunk 3: "## Installation" (180 tokens)

**STAGE 2 (Token Check):**
- All chunks <= max_tokens (assume 512)
- **Result:** 3 chunks ✅ **NO ISSUE**

---

### Scenario 2: Large Section Exceeds Max ❌ CASE 1

```markdown
# Configuration Guide (800 tokens)
This is a very long guide with multiple paragraphs...
Paragraph 1 content... (200 tokens)
Paragraph 2 content... (200 tokens)
Paragraph 3 content... (200 tokens)
Paragraph 4 content... (200 tokens)
```

Assume:
- `max_tokens = 512`
- `chunk_size = 300` (from job config)
- `chunk_overlap = 50` (from job config)

#### Current Behavior:
**STAGE 1 (Header Split):**
- Chunk 1: "# Configuration Guide" (800 tokens)

**STAGE 2 (Token Check):**
- Chunk 1: 800 > 512 → **OVERSIZED**
- Apply RecursiveCharacterTextSplitter with chunk_size=300, overlap=50
- Splits by "\n\n" (paragraphs first)

**Result (RecursiveCharacterTextSplitter):**
- Sub-chunk 1: Para 1 + Para 2 (400 tokens) → Still > 300 → Split further by "\n"
- Sub-chunk 2: Para 3 (200 tokens) ✅
- Sub-chunk 3: Para 4 (200 tokens) ✅
- **Final:** ~4-5 sub-chunks with overlap

#### ❌ Problems:
1. **Lost header context** - Sub-chunks might not include "# Configuration Guide" at the start
2. **Arbitrary splits** - May split mid-paragraph if paragraph > chunk_size
3. **Noisy small chunks** - If last paragraph is 50 tokens, creates a tiny chunk
4. **Overlap pollution** - 50-token overlap adds noise to context

#### ✅ Your Proposed Fix:
**Instead:** Keep header structure, merge small children into parent
- If section > max_tokens → Split by sub-headers first (## level)
- Only if no sub-headers → Split by paragraphs with larger size
- Ensure each chunk >=  min_size

---

### Scenario 3: Tiny Section ❌ CASE 2

```markdown
# Prerequisites (30 tokens)
Python 3.8+

## Installation (50 tokens)
pip install package

## Usage (40 tokens)
Import and use
```

Assume:
- `max_tokens = 512`
- `min_chunk_size = 200` (your desired threshold)

#### Current Behavior:
**STAGE 1 (Header Split):**
- Chunk 1: "# Prerequisites" (30 tokens)
- Chunk 2: "## Installation" (50 tokens)
- Chunk 3: "## Usage" (40 tokens)

**STAGE 2 (Token Check):**
- All chunks <= 512 → Keep as-is
- **Result:** 3 tiny chunks (30, 50, 40 tokens) ❌ **NOISY!**

#### ❌ Problem:
- No minimum size enforcement in current code
- Creates low-information chunks
- Poor retrieval quality

#### ✅ Your Proposed Fix:
**Merge children into parent:**
- Prerequisites (30) + Installation (50) + Usage (40) = 120 tokens
- Still < min_size (200), but better than 3 tiny chunks
- Or: Merge with next sibling section if available

---

### Scenario 4: Mixed Sizes (Real World) ❌ BOTH CASES

```markdown
# Overview (100 tokens)
Brief intro

## Architecture (600 tokens)
Detailed architecture with multiple sub-sections...

### Component A (250 tokens)
Details about A

### Component B (300 tokens)
Details about B

### Component C (50 tokens)
Brief C

## API Reference (1200 tokens)
Very long API docs with no sub-headers...

### Endpoint 1 (400 tokens)
Details

### Endpoint 2 (400 tokens)
Details

### Endpoint 3 (400 tokens)
Details

## Quick Start (80 tokens)
Get started quickly
```

Assume:
- `max_tokens = 512`
- `chunk_size = 300`
- `chunk_overlap = 50`
- `min_chunk_size = 200` (desired)

#### Current Behavior:
**STAGE 1 (Header Split):**
LangChain's MarkdownHeaderTextSplitter splits at EACH header level:
- Chunk 1: "# Overview" (100 tokens)
- Chunk 2: "## Architecture" (600 tokens - includes all ### children)
- Chunk 3: "### Component A" (250 tokens)
- Chunk 4: "### Component B" (300 tokens)
- Chunk 5: "### Component C" (50 tokens)
- Chunk 6: "## API Reference" (1200 tokens - includes all ### children)
- Chunk 7: "### Endpoint 1" (400 tokens)
- Chunk 8: "### Endpoint 2" (400 tokens)
- Chunk 9: "### Endpoint 3" (400 tokens)
- Chunk 10: "## Quick Start" (80 tokens)

**STAGE 2 (Token Check):**
- Chunk 1 (100) ✅ Keep - but TINY!
- Chunk 2 (600) ❌ > 512 → RecursiveCharacterTextSplitter → ~2 sub-chunks
- Chunk 3 (250) ✅ Keep
- Chunk 4 (300) ✅ Keep
- Chunk 5 (50) ✅ Keep - but TINY!
- Chunk 6 (1200) ❌ > 512 → RecursiveCharacterTextSplitter → ~4 sub-chunks
- Chunk 7 (400) ✅ Keep
- Chunk 8 (400) ✅ Keep
- Chunk 9 (400) ✅ Keep
- Chunk 10 (80) ✅ Keep - but TINY!

**Result:** ~16 chunks total
- 3 tiny chunks (100, 50, 80 tokens) ❌
- 2 large chunks split arbitrarily ❌

#### ✅ Your Proposed Fix:
1. **Merge small children into parent:**
   - Component C (50) → Merge into Architecture
   - Quick Start (80) → Merge with previous or keep if isolated

2. **Split large sections by hierarchy:**
   - API Reference (1200) is already split by ### Endpoints
   - But if no sub-headers exist, split by paragraphs manually

---

### Scenario 5: Deep Nesting

```markdown
# Level 1 (500 tokens)
Content...

## Level 2 (400 tokens)
Content...

### Level 3 (300 tokens)
Content...

#### Level 4 (50 tokens)
Tiny content

##### Level 5 (30 tokens)
Very tiny
```

#### Current Behavior:
**STAGE 1 (Header Split):**
- Chunk 1: "# Level 1" (500 tokens)
- Chunk 2: "## Level 2" (400 tokens)
- Chunk 3: "### Level 3" (300 tokens)
- Chunk 4: "#### Level 4" (50 tokens)
- Chunk 5: "##### Level 5" (30 tokens)

**STAGE 2:**
- All <= max_tokens → Keep as-is
- **Result:** 2 tiny chunks (50, 30 tokens) ❌

#### ✅ Your Proposed Fix:
**Bottom-up merge:**
- Level 5 (30) → Merge into Level 4 → 80 tokens
- Level 4 (80) → Merge into Level 3 → 380 tokens ✅
- **Result:** 3 chunks (500, 400, 380)

---

## Your Proposal: Header-First with Parent Merging

### Algorithm:
```python
def adaptive_split(text, max_tokens=512, min_tokens=200, chunk_size=300, chunk_overlap=50):
    # STAGE 1: Split by headers (existing MarkdownHeaderTextSplitter)
    header_chunks = markdown_splitter.split_text(text)

    # STAGE 2: Build parent-child tree from header metadata
    tree = build_hierarchy_tree(header_chunks)

    # STAGE 3: Process bottom-up (children before parents)
    for node in tree.traverse_bottom_up():
        # Check if node is too small
        if node.token_count < min_tokens:
            if node.parent:
                # Try to merge into parent
                if node.parent.token_count + node.token_count <= max_tokens:
                    node.parent.merge_child(node)
                else:
                    # Parent too full - keep as-is for now
                    pass
            else:
                # No parent (top-level) - try merge with sibling
                try_merge_with_sibling(node)

        # Check if node is too large
        elif node.token_count > max_tokens:
            # Try to split by sub-headers first
            if node.has_children():
                # Already has children - keep structure
                pass
            else:
                # No sub-headers - split by paragraphs
                split_by_paragraphs_intelligently(node, max_tokens, chunk_size, chunk_overlap)

    # STAGE 4: Collect final chunks
    return tree.get_leaf_chunks()
```

---

## Critical Questions Based on YOUR Code

### Question 1: MarkdownHeaderTextSplitter Behavior
**Does LangChain's MarkdownHeaderTextSplitter create SEPARATE chunks for parent AND children?**

Example:
```markdown
## Parent
Parent content

### Child
Child content
```

**Does it create:**
- A) 1 chunk: "## Parent + parent content + ### Child + child content"
- B) 2 chunks: "## Parent + parent content" AND "### Child + child content"

**Answer:** **B** - It creates separate chunks for each header level.

**Implication:** Your parent-merging strategy needs to:
1. Identify parent-child relationships from metadata
2. Merge child chunks back into parent
3. Handle cases where parent is missing (only child exists)

### Question 2: What's in chunk.metadata?
LangChain's MarkdownHeaderTextSplitter adds header metadata like:
```python
{
    "Header 1": "Parent Title",
    "Header 2": "Child Title",
    ...
}
```

**Can you use this to rebuild the tree?** → YES!

### Question 3: When to merge vs. keep separate?
```markdown
## Parent (480 tokens)
### Child (50 tokens)
```

**If you merge:**
- Parent + Child = 530 tokens > max_tokens (512) ❌

**Options:**
A) Keep child separate (tiny chunk)
B) Split parent first, merge child into last part
C) Force merge, exceed max_tokens temporarily

**Recommendation:** **B** - Split parent into 2 chunks (240, 240), then merge child into last (240 + 50 = 290)

---

## Recommended Implementation for YOUR Code

### Step 1: Detect Parent-Child Relationships
```python
def build_hierarchy_from_metadata(chunks: List[Document]) -> Tree:
    """
    Build tree from LangChain metadata.

    Example metadata:
    chunk.metadata = {"Header 1": "Installation", "Header 2": "Prerequisites"}

    This means: chunk belongs to "Installation > Prerequisites"
    """
    tree = Tree()

    for chunk in chunks:
        # Extract header hierarchy from metadata
        hierarchy = []
        for level in ["Header 1", "Header 2", "Header 3", "Header 4", "Header 5"]:
            if level in chunk.metadata:
                hierarchy.append(chunk.metadata[level])

        # Add to tree
        tree.add_node(chunk, hierarchy)

    return tree
```

### Step 2: Merge Small Children into Parent
```python
def merge_small_chunks(tree: Tree, min_tokens: int, max_tokens: int):
    """
    Bottom-up merge: merge small children into parents.
    """
    for node in tree.traverse_bottom_up():
        if node.token_count < min_tokens and node.parent:
            if node.parent.token_count + node.token_count <= max_tokens:
                # Safe to merge
                node.parent.content += "\n\n" + node.content
                node.parent.token_count += node.token_count
                node.mark_merged()
            else:
                # Parent too full - need to split parent first
                split_parent_intelligently(node.parent, max_tokens)
                # Retry merge
                if node.parent.parts[-1].token_count + node.token_count <= max_tokens:
                    node.parent.parts[-1].merge(node)
```

### Step 3: Split Large Chunks Intelligently
```python
def split_large_chunks(node: Node, max_tokens: int, chunk_size: int):
    """
    Split large chunks by paragraphs, not arbitrary characters.
    """
    if node.token_count <= max_tokens:
        return

    # Strategy 1: Check for sub-headers (if children exist, use them)
    if node.has_children():
        # Already split - children will be separate chunks
        return

    # Strategy 2: Split by paragraphs
    paragraphs = node.content.split("\n\n")
    current_chunk = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        if current_tokens + para_tokens <= max_tokens:
            current_chunk.append(para)
            current_tokens += para_tokens
        else:
            # Save current chunk
            if current_chunk:
                node.add_sub_chunk("\n\n".join(current_chunk))
            # Start new chunk
            current_chunk = [para]
            current_tokens = para_tokens

    # Add remaining
    if current_chunk:
        node.add_sub_chunk("\n\n".join(current_chunk))
```

---

## Answers to My Questions (Based on YOUR Code):

1. **When merge exceeds max:** YES - Split parent first, then merge child into last part
2. **Top-level small sections:** MERGE with previous sibling
3. **Multiple small children:** MERGE ALL into parent (if fits)
4. **Processing order:** BOTTOM-UP (children before parents)
5. **Large section splitting:** PARAGRAPHS first, preserve semantic boundaries

---

## Implementation Plan for YOUR Codebase

### Modify `MarkdownSplitter.split()`:
```python
def split(self, text: str) -> List[Document]:
    # STAGE 1: Split by headers (existing code)
    markdown_chunks = self._markdown_splitter.split_text(text)

    if not self.max_tokens:
        return markdown_chunks

    # NEW STAGE 1.5: Build hierarchy and merge small chunks
    tree = self._build_hierarchy_tree(markdown_chunks)
    tree = self._merge_small_chunks(tree, min_tokens=200)

    # STAGE 2: Enforce token limits (existing code, but improved)
    final_chunks = []
    for node in tree.get_all_nodes():
        if node.token_count <= self.max_tokens:
            final_chunks.append(node.to_document())
        else:
            # Split by paragraphs, not RecursiveCharacterTextSplitter
            sub_chunks = self._split_by_paragraphs(node, self.max_tokens)
            final_chunks.extend(sub_chunks)

    return final_chunks
```

---

Should I implement this for your codebase?
