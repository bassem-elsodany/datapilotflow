# Markdown Splitter - Parent Merge Implementation

## Summary

Added **STAGE 1.5: Merge small chunks into parent** to prevent noisy low-information chunks in markdown splitting.

## Problem Solved

### Before:
```python
# STAGE 1: Split by headers
markdown_chunks = [
    Document("# Overview", 100 tokens),
    Document("## Features", 200 tokens),
    Document("### Small Feature", 50 tokens),  # ❌ TOO SMALL
    Document("## Installation", 180 tokens)
]

# STAGE 2: Handle oversized only
# Result: 4 chunks (including 1 noisy 50-token chunk)
```

### After:
```python
# STAGE 1: Split by headers
markdown_chunks = [
    Document("# Overview", 100 tokens),
    Document("## Features", 200 tokens),
    Document("### Small Feature", 50 tokens),  # ❌ TOO SMALL
    Document("## Installation", 180 tokens)
]

# STAGE 1.5: Merge small into parent
merged_chunks = [
    Document("# Overview", 100 tokens),
    Document("## Features + ### Small Feature", 250 tokens),  # ✅ MERGED
    Document("## Installation", 180 tokens)
]

# STAGE 2: Handle oversized
# Result: 3 chunks (no noisy chunks!)
```

## Implementation

### Changes to `MarkdownSplitter` class:

#### 1. Added `min_chunk_size` parameter:
```python
def __init__(
    self,
    splitter_config: DocumentSplitter,
    max_tokens: Optional[int] = None,
    model_name: Optional[str] = None,
    min_chunk_size: int = 200  # NEW: Minimum tokens to prevent noisy chunks
):
    self.min_chunk_size = min_chunk_size
```

#### 2. Added `_merge_small_into_parent()` method:
```python
def _merge_small_into_parent(
    self,
    chunks: List[Document]
) -> List[Document]:
    """
    Merge small chunks into their parent to prevent noisy low-information chunks.

    Algorithm:
    1. Build parent-child relationships from header metadata
    2. For each chunk < min_chunk_size:
       - Find its parent (one level up in header hierarchy)
       - If parent + child <= max_tokens: Merge child into parent
       - Otherwise: Keep child as separate chunk
    """
```

#### 3. Integrated into `split()` method:
```python
def split(self, text: str) -> List[Document]:
    # STAGE 1: Split by markdown headers
    markdown_chunks = self._markdown_splitter.split_text(text)

    # STAGE 1.5: Merge small chunks into parent (NEW!)
    merged_chunks = self._merge_small_into_parent(markdown_chunks)

    # STAGE 2: Enforce token limits for oversized chunks
    final_chunks = []
    for chunk in merged_chunks:
        if chunk_tokens > max_tokens:
            # Split recursively
        else:
            # Keep as-is
```

## Algorithm Details

### How Parent-Child Relationship is Determined:

LangChain's `MarkdownHeaderTextSplitter` adds header metadata to chunks:
```python
chunk.metadata = {
    "Header 1": "Installation",
    "Header 2": "Prerequisites",
    "Header 3": "Python Version"
}
```

**Hierarchy extraction:**
```python
hierarchy = ["Installation", "Prerequisites", "Python Version"]
# This chunk is at level 3 (### Python Version)

parent_hierarchy = ["Installation", "Prerequisites"]
# Parent is at level 2 (## Prerequisites)
```

**Parent matching:**
```python
# Find chunk where hierarchy == parent_hierarchy
for candidate in reversed(chunks[:current_index]):
    if candidate.hierarchy == parent_hierarchy:
        parent_found = candidate
        break
```

### Merge Logic:

```python
# Check if chunk is too small
if chunk_tokens < min_chunk_size:

    # Find parent
    parent = find_parent(chunk)

    if parent exists:
        # Check if merge would exceed max
        if (parent_tokens + chunk_tokens) <= max_tokens:
            # ✅ MERGE: Append child content to parent
            parent.page_content += "\n\n" + chunk.page_content
            mark_chunk_as_merged(chunk)
        else:
            # ❌ KEEP SEPARATE: Would exceed max_tokens
            keep_chunk(chunk)
    else:
        # ❌ KEEP SEPARATE: No parent found (top-level chunk)
        keep_chunk(chunk)
```

## Examples

### Example 1: Simple Merge

**Input:**
```markdown
## Parent Section (200 tokens)
Content here...

### Small Child (50 tokens)
Brief content
```

**Processing:**
```
STAGE 1: Split by headers
  - Chunk 1: "## Parent Section" (200 tokens)
  - Chunk 2: "### Small Child" (50 tokens)

STAGE 1.5: Merge small chunks
  - Chunk 2 is 50 < 200 (min_chunk_size)
  - Parent found: Chunk 1
  - Total: 200 + 50 = 250 <= 512 (max_tokens) ✅
  - MERGE: Chunk 2 → Chunk 1

Output:
  - Chunk 1: "## Parent Section + ### Small Child" (250 tokens)
```

### Example 2: Cannot Merge (Would Exceed Max)

**Input:**
```markdown
## Parent Section (480 tokens)
Lots of content...

### Small Child (50 tokens)
Brief content
```

**Assume max_tokens = 512:**
```
STAGE 1: Split by headers
  - Chunk 1: "## Parent Section" (480 tokens)
  - Chunk 2: "### Small Child" (50 tokens)

STAGE 1.5: Merge small chunks
  - Chunk 2 is 50 < 200 (min_chunk_size)
  - Parent found: Chunk 1
  - Total: 480 + 50 = 530 > 512 (max_tokens) ❌
  - KEEP SEPARATE: Chunk 2 remains small

Output:
  - Chunk 1: "## Parent Section" (480 tokens)
  - Chunk 2: "### Small Child" (50 tokens) ❌ Still noisy but unavoidable
```

### Example 3: Multiple Small Children

**Input:**
```markdown
## Parent Section (300 tokens)
Content...

### Small Child 1 (40 tokens)
Brief

### Small Child 2 (60 tokens)
More brief

### Small Child 3 (80 tokens)
Even more
```

**Processing:**
```
STAGE 1: Split by headers
  - Chunk 1: "## Parent Section" (300 tokens)
  - Chunk 2: "### Small Child 1" (40 tokens)
  - Chunk 3: "### Small Child 2" (60 tokens)
  - Chunk 4: "### Small Child 3" (80 tokens)

STAGE 1.5: Merge small chunks (process in order)
  - Chunk 2: 40 < 200, parent = Chunk 1, total = 340 ✅ MERGE
  - Chunk 3: 60 < 200, parent = Chunk 1 (now 340), total = 400 ✅ MERGE
  - Chunk 4: 80 < 200, parent = Chunk 1 (now 400), total = 480 ✅ MERGE

Output:
  - Chunk 1: "## Parent + ### Child 1 + ### Child 2 + ### Child 3" (480 tokens)
```

### Example 4: No Parent (Top-Level Small Chunk)

**Input:**
```markdown
# Small Section (80 tokens)
Brief intro

# Another Section (300 tokens)
More content
```

**Processing:**
```
STAGE 1: Split by headers
  - Chunk 1: "# Small Section" (80 tokens)
  - Chunk 2: "# Another Section" (300 tokens)

STAGE 1.5: Merge small chunks
  - Chunk 1: 80 < 200, but no parent (level 1 has no parent)
  - KEEP AS-IS

Output:
  - Chunk 1: "# Small Section" (80 tokens) ❌ Still noisy but unavoidable
  - Chunk 2: "# Another Section" (300 tokens)
```

## Configuration

### Default Values:
```python
min_chunk_size = 200  # Minimum tokens per chunk
max_tokens = 512      # Maximum tokens (from embedding model)
```

### Tuning Recommendations:

**For aggressive noise reduction:**
```python
min_chunk_size = 300  # Higher threshold, more merging
```

**For preserving structure:**
```python
min_chunk_size = 100  # Lower threshold, less merging
```

**Relationship to max_tokens:**
- `min_chunk_size` should be < `max_tokens / 2`
- Ensures parent + child can usually fit together

## Logging

### Debug Logs:
```
Stage 1 (Markdown headers): Created 10 chunks
Stage 1.5 (Merge small chunks): Processing 10 chunks with min_chunk_size=200
  Merged chunk 3 (50 tokens) into parent 2 (new total: 250 tokens)
  Merged chunk 5 (80 tokens) into parent 4 (new total: 320 tokens)
  Cannot merge chunk 7 (150 tokens) into parent 6 (480 tokens) - would exceed max_tokens (630 > 512)
  Chunk 9 is small (100 tokens) but has no parent - keeping as-is
Stage 1.5 (Merge small chunks): 10 → 7 chunks (3 small chunks merged into parents)
Stage 2 (Token enforcement): 7 → 9 chunks (1 chunks required secondary splitting)
```

### Info Logs:
```
MarkdownSplitter initialized with HYBRID strategy: headers=6, min_chunk_size=200, max_tokens=512, secondary_chunk_size=300, secondary_overlap=50
```

## Edge Cases Handled

### 1. Chunk with no parent (top-level)
- **Behavior:** Keep as-is (cannot merge)
- **Log:** "Chunk X is small (Y tokens) but has no parent - keeping as-is"

### 2. Merging would exceed max_tokens
- **Behavior:** Keep both parent and child separate
- **Log:** "Cannot merge chunk X (Y tokens) into parent Z (W tokens) - would exceed max_tokens"

### 3. All children merged into parent
- **Behavior:** Parent contains all child content
- **Result:** Single merged chunk

### 4. Empty hierarchy (no headers)
- **Behavior:** No merging occurs (no parent-child relationships)
- **Result:** Returns chunks as-is from STAGE 1

## Testing

### Test Case 1: Normal Merge
```python
text = """
## Parent (200 tokens)
Content...

### Child (50 tokens)
Brief
"""

chunks = splitter.split(text)
assert len(chunks) == 1  # Merged
assert chunks[0].token_count == 250
```

### Test Case 2: Prevented Merge (Exceeds Max)
```python
text = """
## Parent (480 tokens)
Content...

### Child (50 tokens)
Brief
"""

splitter.max_tokens = 512
chunks = splitter.split(text)
assert len(chunks) == 2  # NOT merged (would exceed 512)
```

### Test Case 3: Multiple Children
```python
text = """
## Parent (200 tokens)
Content...

### Child 1 (40 tokens)
### Child 2 (60 tokens)
### Child 3 (80 tokens)
"""

chunks = splitter.split(text)
assert len(chunks) == 1  # All merged
assert chunks[0].token_count == 380
```

## Benefits

### ✅ Solves Case 2: Small Sections
- Prevents noisy low-information chunks
- Merges small children into semantic parent context
- Improves retrieval quality

### ✅ Preserves Case 1 Handling: Large Sections
- Existing recursive splitting still works for oversized chunks
- No regression

### ✅ Simple Implementation
- Single method added
- Minimal changes to existing code
- Easy to understand and maintain

### ✅ Configurable
- `min_chunk_size` parameter allows tuning
- Can be adjusted per use case

## Future Enhancements (Optional)

### 1. Merge Siblings (Top-Level Small Chunks)
Currently, top-level small chunks without parents are kept as-is.

**Enhancement:** Merge with previous sibling
```python
if not parent_found and is_top_level:
    # Try to merge with previous sibling
    previous_sibling = find_previous_sibling(chunk)
    if previous_sibling and can_merge(previous_sibling, chunk):
        merge(previous_sibling, chunk)
```

### 2. Configurable min_chunk_size per Job
Add to `DocumentSplitter` config:
```python
class DocumentSplitter:
    min_chunk_size: Optional[int] = None  # If None, use default (200)
```

### 3. Bottom-Up Merging (Grandchildren → Children → Parents)
Current implementation processes linearly.

**Enhancement:** Process leaf nodes first, then parents
```python
# Build tree structure
tree = build_tree(chunks)

# Process bottom-up (leaves first)
for node in tree.traverse_bottom_up():
    if node.is_small():
        merge_into_parent(node)
```

## Files Modified

### `src/processors/splitters/markdown_splitter.py`
- Added `min_chunk_size` parameter to `__init__` (default: 200)
- Added `_merge_small_into_parent()` method
- Integrated merging into `split()` method (STAGE 1.5)
- Updated docstrings and logging

**Lines changed:** ~130 lines added

## Backward Compatibility

✅ **Fully backward compatible**
- New parameter has default value (200)
- Existing code continues to work
- Only affects behavior when `max_tokens` is configured

## Summary

**What we did:**
- ✅ Added STAGE 1.5: Merge small chunks into parent
- ✅ Prevents noisy low-information chunks
- ✅ Simple, maintainable implementation
- ✅ Configurable via `min_chunk_size`
- ✅ Handles edge cases gracefully

**What we kept:**
- ✅ STAGE 1: Split by headers (unchanged)
- ✅ STAGE 2: Recursive splitting for oversized chunks (unchanged)
- ✅ All existing functionality preserved

**Result:**
- Better chunk quality
- Reduced noise
- Improved RAG retrieval
- No breaking changes
