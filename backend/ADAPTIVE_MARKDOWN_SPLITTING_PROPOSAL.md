# Adaptive Markdown Splitting Strategy - Proposal

## Problem Statement

Current markdown splitting by headers has two critical issues:

### Case 1: Large Sections
- Header-based chunks exceed embedding model token limits
- Forced fallback to chunk_size splits creates noisy small fragments
- Loss of semantic coherence

### Case 2: Small Sections
- Some header sections contain minimal content (1-2 sentences)
- Creates noisy, low-information chunks
- Inefficient storage and retrieval

## Root Causes

1. **Binary splitting decision** - Either split by header OR by size, no middle ground
2. **No minimum chunk size enforcement** - Allows tiny chunks
3. **No content merging** - Adjacent small sections remain separate
4. **Rigid token limit handling** - No smart subsection splitting

## Proposed Solution: Adaptive Hybrid Strategy

### Core Principles

1. **Semantic preservation** - Keep related content together
2. **Size optimization** - Enforce both MIN and MAX chunk sizes
3. **Smart merging** - Combine small adjacent sections
4. **Hierarchical splitting** - Respect header hierarchy when subdividing

### Algorithm

```python
class AdaptiveMarkdownSplitter:
    def __init__(
        self,
        min_chunk_size: int = 200,      # Minimum tokens (prevent noise)
        target_chunk_size: int = 500,   # Target tokens (optimal)
        max_chunk_size: int = 800,      # Maximum tokens (hard limit)
        chunk_overlap: int = 50,        # Overlap for context
    ):
        self.min_chunk_size = min_chunk_size
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, markdown_text: str) -> List[Document]:
        """
        Adaptive splitting with 4-step process:
        1. Split by headers (hierarchical)
        2. Merge small sections
        3. Subdivide large sections
        4. Apply overlap
        """

        # Step 1: Split by headers hierarchically
        sections = self._split_by_headers(markdown_text)

        # Step 2: Merge small adjacent sections
        merged_sections = self._merge_small_sections(sections)

        # Step 3: Subdivide large sections intelligently
        final_chunks = []
        for section in merged_sections:
            if self._get_token_count(section.content) > self.max_chunk_size:
                # Smart subdivision
                sub_chunks = self._subdivide_section(section)
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(section)

        # Step 4: Apply overlap between chunks
        overlapped_chunks = self._apply_overlap(final_chunks)

        return overlapped_chunks

    def _split_by_headers(self, text: str) -> List[Section]:
        """
        Split by headers with hierarchy tracking
        Headers: # > ## > ### > #### > #####
        """
        sections = []
        lines = text.split('\n')
        current_section = None
        current_hierarchy = []

        for line in lines:
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if header_match:
                # Save previous section
                if current_section:
                    sections.append(current_section)

                # Start new section
                level = len(header_match.group(1))
                title = header_match.group(2)

                # Update hierarchy
                current_hierarchy = current_hierarchy[:level-1] + [title]

                current_section = Section(
                    title=title,
                    level=level,
                    hierarchy=current_hierarchy.copy(),
                    content=line + '\n'
                )
            else:
                if current_section:
                    current_section.content += line + '\n'
                else:
                    # Content before first header
                    sections.append(Section(
                        title='',
                        level=0,
                        hierarchy=[],
                        content=line + '\n'
                    ))

        if current_section:
            sections.append(current_section)

        return sections

    def _merge_small_sections(self, sections: List[Section]) -> List[Section]:
        """
        Merge adjacent small sections intelligently

        Rules:
        1. If section < min_chunk_size, try to merge with next
        2. Only merge if same parent hierarchy
        3. Don't merge if result > max_chunk_size
        4. Preserve hierarchy in merged section
        """
        merged = []
        i = 0

        while i < len(sections):
            current = sections[i]
            current_tokens = self._get_token_count(current.content)

            # If current is too small, try merging with next
            if current_tokens < self.min_chunk_size and i < len(sections) - 1:
                next_section = sections[i + 1]
                next_tokens = self._get_token_count(next_section.content)
                combined_tokens = current_tokens + next_tokens

                # Check merge conditions
                can_merge = (
                    combined_tokens <= self.max_chunk_size and
                    self._same_parent_hierarchy(current, next_section)
                )

                if can_merge:
                    # Merge sections
                    merged_section = Section(
                        title=f"{current.title} + {next_section.title}",
                        level=min(current.level, next_section.level),
                        hierarchy=current.hierarchy,
                        content=current.content + '\n' + next_section.content,
                        is_merged=True
                    )
                    merged.append(merged_section)
                    i += 2  # Skip next since we merged it
                    continue

            merged.append(current)
            i += 1

        return merged

    def _subdivide_section(self, section: Section) -> List[Section]:
        """
        Intelligently subdivide large sections

        Strategy:
        1. Try splitting by sub-headers (lower level)
        2. If no sub-headers, split by paragraphs
        3. If paragraphs too large, split by sentences
        4. Last resort: split by chunk_size with overlap

        Goal: Keep chunks between target_chunk_size and max_chunk_size
        """
        content = section.content
        tokens = self._get_token_count(content)

        # Strategy 1: Split by sub-headers
        if section.level < 5:  # Can go deeper
            sub_sections = self._split_by_lower_headers(content, section.level + 1)
            if len(sub_sections) > 1:
                return [
                    Section(
                        title=f"{section.title} - Part {i+1}",
                        level=section.level,
                        hierarchy=section.hierarchy,
                        content=sub_content
                    )
                    for i, sub_content in enumerate(sub_sections)
                ]

        # Strategy 2: Split by paragraphs
        paragraphs = self._split_by_paragraphs(content)
        if len(paragraphs) > 1:
            return self._group_paragraphs_optimally(
                paragraphs,
                section,
                self.target_chunk_size
            )

        # Strategy 3: Split by sentences
        sentences = self._split_by_sentences(content)
        if len(sentences) > 1:
            return self._group_sentences_optimally(
                sentences,
                section,
                self.target_chunk_size
            )

        # Strategy 4: Last resort - force split by tokens
        return self._force_split_by_tokens(content, section)

    def _split_by_lower_headers(self, content: str, target_level: int) -> List[str]:
        """
        Split content by headers of a specific lower level
        Example: If section is ##, split by ###
        """
        header_pattern = f"^{'#' * target_level}\\s+.+$"
        chunks = []
        current_chunk = []

        for line in content.split('\n'):
            if re.match(header_pattern, line):
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
            else:
                current_chunk.append(line)

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def _split_by_paragraphs(self, content: str) -> List[str]:
        """Split by double newlines (paragraphs)"""
        paragraphs = re.split(r'\n\s*\n', content)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_by_sentences(self, content: str) -> List[str]:
        """Split by sentence boundaries"""
        # Simple sentence splitter (can use nltk for better results)
        sentences = re.split(r'(?<=[.!?])\s+', content)
        return [s.strip() for s in sentences if s.strip()]

    def _group_paragraphs_optimally(
        self,
        paragraphs: List[str],
        parent_section: Section,
        target_size: int
    ) -> List[Section]:
        """
        Group paragraphs into optimally-sized chunks
        Goal: Get as close to target_size as possible
        """
        chunks = []
        current_chunk = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self._get_token_count(para)

            # If adding this paragraph keeps us under max, add it
            if current_tokens + para_tokens <= self.max_chunk_size:
                current_chunk.append(para)
                current_tokens += para_tokens
            else:
                # Save current chunk if it's above minimum
                if current_tokens >= self.min_chunk_size:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = [para]
                    current_tokens = para_tokens
                else:
                    # Current chunk too small, add paragraph anyway
                    current_chunk.append(para)
                    current_tokens += para_tokens
                    # Save and reset
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

        # Add remaining
        if current_chunk:
            if current_tokens >= self.min_chunk_size or not chunks:
                chunks.append('\n\n'.join(current_chunk))
            else:
                # Merge with last chunk if too small
                if chunks:
                    chunks[-1] += '\n\n' + '\n\n'.join(current_chunk)

        return [
            Section(
                title=f"{parent_section.title} - Part {i+1}",
                level=parent_section.level,
                hierarchy=parent_section.hierarchy,
                content=chunk
            )
            for i, chunk in enumerate(chunks)
        ]

    def _group_sentences_optimally(
        self,
        sentences: List[str],
        parent_section: Section,
        target_size: int
    ) -> List[Section]:
        """Similar to _group_paragraphs_optimally but for sentences"""
        # Same logic as paragraphs but with sentences
        return self._group_paragraphs_optimally(sentences, parent_section, target_size)

    def _force_split_by_tokens(
        self,
        content: str,
        parent_section: Section
    ) -> List[Section]:
        """
        Last resort: force split by token count
        Used when no semantic boundaries available
        """
        words = content.split()
        chunks = []
        current_chunk = []
        current_tokens = 0

        for word in words:
            word_tokens = self._get_token_count(word)

            if current_tokens + word_tokens > self.target_chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_tokens = word_tokens
            else:
                current_chunk.append(word)
                current_tokens += word_tokens

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return [
            Section(
                title=f"{parent_section.title} - Part {i+1}",
                level=parent_section.level,
                hierarchy=parent_section.hierarchy,
                content=chunk
            )
            for i, chunk in enumerate(chunks)
        ]

    def _apply_overlap(self, sections: List[Section]) -> List[Section]:
        """
        Apply overlap between adjacent chunks for context continuity
        """
        if len(sections) <= 1:
            return sections

        overlapped = []

        for i, section in enumerate(sections):
            content = section.content

            # Add overlap from previous chunk
            if i > 0 and self.chunk_overlap > 0:
                prev_content = sections[i-1].content
                prev_words = prev_content.split()[-self.chunk_overlap:]
                overlap_text = ' '.join(prev_words)
                content = f"[...{overlap_text}]\n\n{content}"

            overlapped.append(Section(
                title=section.title,
                level=section.level,
                hierarchy=section.hierarchy,
                content=content
            ))

        return overlapped

    def _same_parent_hierarchy(self, section1: Section, section2: Section) -> bool:
        """Check if two sections share the same parent in hierarchy"""
        if not section1.hierarchy or not section2.hierarchy:
            return True

        # Compare all but last element (parent hierarchy)
        return section1.hierarchy[:-1] == section2.hierarchy[:-1]

    def _get_token_count(self, text: str) -> int:
        """
        Estimate token count
        Use actual tokenizer for accurate count
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4

@dataclass
class Section:
    title: str
    level: int
    hierarchy: List[str]
    content: str
    is_merged: bool = False
```

## Configuration Recommendations

### Small Documents (< 5000 tokens)
```python
splitter = AdaptiveMarkdownSplitter(
    min_chunk_size=100,    # Allow smaller chunks
    target_chunk_size=300, # Keep chunks small
    max_chunk_size=500,    # Lower maximum
    chunk_overlap=20,      # Less overlap
)
```

### Medium Documents (5000 - 20000 tokens)
```python
splitter = AdaptiveMarkdownSplitter(
    min_chunk_size=200,    # Prevent noise
    target_chunk_size=500, # Balanced
    max_chunk_size=800,    # Standard limit
    chunk_overlap=50,      # Good context
)
```

### Large Documents (> 20000 tokens)
```python
splitter = AdaptiveMarkdownSplitter(
    min_chunk_size=300,     # Larger minimum
    target_chunk_size=600,  # Larger target
    max_chunk_size=1000,    # Higher limit
    chunk_overlap=100,      # More overlap
)
```

## Benefits

### ✅ Solves Case 1: Large Sections
- Hierarchical subdivision respects semantic structure
- Paragraph/sentence-based splitting preserves meaning
- Chunks stay within optimal size range

### ✅ Solves Case 2: Small Sections
- Automatic merging of small adjacent sections
- Respects hierarchy (only merges siblings)
- Enforces minimum chunk size

### ✅ Additional Benefits
1. **Better retrieval** - Semantic chunks improve relevance
2. **Less noise** - No tiny fragments
3. **Efficient storage** - Optimal chunk sizes
4. **Context preservation** - Overlap maintains continuity
5. **Flexible** - Adapts to document structure

## Example Scenarios

### Scenario 1: Large Header Section
```markdown
## Installation (2000 tokens)

Lorem ipsum... [long content]
```

**Result:**
1. Check for sub-headers (###)
2. If found, split by sub-headers
3. If not, split by paragraphs
4. Group paragraphs into 500-token chunks
5. Apply overlap

**Output:**
- Chunk 1: "Installation - Part 1" (500 tokens)
- Chunk 2: "Installation - Part 2" (500 tokens) [with overlap from Part 1]
- Chunk 3: "Installation - Part 3" (remaining tokens)

### Scenario 2: Small Adjacent Sections
```markdown
## Prerequisites (50 tokens)
Python 3.8+

## Installation (50 tokens)
pip install package

## Configuration (50 tokens)
Set API key
```

**Result:**
1. All sections < min_chunk_size (200)
2. Same parent hierarchy
3. Merge all three

**Output:**
- Chunk 1: "Prerequisites + Installation + Configuration" (150 tokens)

### Scenario 3: Mixed Sizes
```markdown
## Introduction (100 tokens)
Brief intro

## Features (1500 tokens)
### Feature A (500 tokens)
### Feature B (500 tokens)
### Feature C (500 tokens)

## Conclusion (100 tokens)
Summary
```

**Result:**
1. "Introduction" (100) → too small, merge with next
2. "Features" (1500) → too large, split by sub-headers
3. Sub-headers already optimal → keep as-is
4. "Conclusion" (100) → too small, merge with previous

**Output:**
- Chunk 1: "Introduction + Features Intro" (~200 tokens)
- Chunk 2: "Feature A" (500 tokens)
- Chunk 3: "Feature B" (500 tokens)
- Chunk 4: "Feature C + Conclusion" (~600 tokens)

## Implementation in DataPilotFlow

### Integration Points

1. **File Extraction Step**
   - `src/processors/knowledge_job/pipeline/steps/file_extraction_step.py`
   - Replace `MarkdownHeaderTextSplitter` with `AdaptiveMarkdownSplitter`

2. **Configuration**
   - Add to `KnowledgeSourceConfig`:
     ```python
     min_chunk_size: int = 200
     target_chunk_size: int = 500
     max_chunk_size: int = 800
     ```

3. **UI Configuration**
   - Add sliders in Knowledge Source form:
     - Min Chunk Size
     - Target Chunk Size
     - Max Chunk Size

### Migration Strategy

1. **Phase 1: Implement** (1-2 days)
   - Create `AdaptiveMarkdownSplitter` class
   - Add unit tests
   - Integrate into pipeline

2. **Phase 2: Test** (1 day)
   - Test with various document sizes
   - Compare retrieval quality
   - Measure storage impact

3. **Phase 3: Deploy** (1 day)
   - Add UI configuration
   - Update documentation
   - Re-index existing documents (optional)

## Alternative: Simpler Solution

If the full adaptive solution is too complex, here's a **simpler hybrid approach**:

```python
class SimpleHybridSplitter:
    def split(self, markdown_text: str) -> List[str]:
        # 1. Split by headers
        sections = split_by_headers(markdown_text)

        # 2. For each section:
        chunks = []
        for section in sections:
            tokens = count_tokens(section)

            if tokens < MIN_SIZE:
                # Accumulate small sections
                buffer.append(section)
            elif tokens > MAX_SIZE:
                # Split large sections by paragraphs
                paras = split_by_paragraphs(section)
                chunks.extend(group_paragraphs(paras, TARGET_SIZE))
            else:
                # Perfect size, keep as-is
                chunks.append(section)

        return chunks
```

**Pros:** Simple, easy to implement
**Cons:** Less sophisticated merging/splitting logic

## Recommendation

I recommend implementing the **full Adaptive Hybrid Strategy** because:

1. ✅ **Solves both problems completely**
2. ✅ **Improves retrieval quality significantly**
3. ✅ **Flexible configuration for different use cases**
4. ✅ **Production-ready solution**

The initial implementation effort (~2-3 days) is worth the long-term benefits of higher quality RAG retrieval.

Would you like me to:
1. Implement the full `AdaptiveMarkdownSplitter` class?
2. Integrate it into your pipeline?
3. Add UI configuration for the new parameters?
