# Pipeline Node Linking Guide

## How Node Connections Work

The Pipeline Builder allows you to create visual workflows by **dragging nodes** and **connecting them with edges**. The backend intelligently **follows these connections** to combine configurations.

## Key Principle: **Connected Nodes Matter**

⚠️ **IMPORTANT**: The backend only uses configurations from nodes that are **actually connected** in your pipeline!

If you have a Domain Filter node on the canvas but it's **not connected** to your source, it will be **ignored**.

## Visual Pipeline Flow

### Example 1: Simple Pipeline (No Filters)

```
[Website Source] → [Text Splitter] → [Embedding] → [Vector DB]
```

**What the backend extracts:**
- URL + Crawl Depth from Website Source
- No filters applied (none connected!)
- Default output format: Markdown

### Example 2: Pipeline with Filters

```
[Website Source] → [Domain Filter] → [Content Filter] → [Text Splitter] → [Embedding] → [Vector DB]
```

**What the backend extracts:**
- URL + Crawl Depth from Website Source
- Allowed/Blocked subdomains from Domain Filter ✅ (connected!)
- CSS selectors from Content Filter ✅ (connected!)
- Default output format: Markdown

### Example 3: Disconnected Filter (Common Mistake!)

```
[Website Source] → [Text Splitter] → [Embedding] → [Vector DB]

[Domain Filter]  ← NOT CONNECTED!
```

**What the backend extracts:**
- URL + Crawl Depth from Website Source
- **Domain Filter is IGNORED** ❌ (not connected!)
- No filters applied

## How the Backend Follows Connections

### Algorithm: Breadth-First Search (BFS)

1. **Start at the source node** (Website/Links/Single Page)
2. **Follow all outgoing edges** from the source
3. **Recursively follow edges** from each connected node
4. **Collect all reachable nodes** in the path

### Code Implementation

```python
def _get_connected_nodes(start_node_id, edges, nodes):
    """
    Get all node IDs reachable from start node by following edges.
    Uses BFS to traverse the pipeline graph.
    """
    visited = set()
    queue = [start_node_id]

    while queue:
        current_id = queue.pop(0)
        if current_id in visited:
            continue

        visited.add(current_id)

        # Find edges where current node is the source
        for edge in edges:
            if edge.source == current_id:
                queue.append(edge.target)

    return visited
```

### Then Extract Configs from Connected Nodes

```python
# Find CONNECTED filter nodes
connected_node_ids = _get_connected_nodes(source_node.id, pipeline.edges, pipeline.nodes)

# Only use filters that are in the connected path
domain_filter = next((n for n in nodes if n.type == 'domainFilter' and n.id in connected_node_ids), None)
content_filter = next((n for n in nodes if n.type == 'contentFilter' and n.id in connected_node_ids), None)
output_format = next((n for n in nodes if n.type == 'outputFormat' and n.id in connected_node_ids), None)
```

## Valid Connection Patterns

### Pattern 1: Direct to Splitter (Skip Filters)

```
[Source] → [Splitter] → [Embedding] → [VectorDB]
```
✅ Valid - Filters are optional

### Pattern 2: All Filters in Order

```
[Source] → [Domain Filter] → [Content Filter] → [Output Format] → [Splitter] → ...
```
✅ Valid - All filters applied

### Pattern 3: Partial Filters

```
[Source] → [Content Filter] → [Splitter] → ...
```
✅ Valid - Only content filter applied, domain filtering skipped

### Pattern 4: Filters in Different Order

```
[Source] → [Output Format] → [Domain Filter] → [Splitter] → ...
```
✅ Valid - Order doesn't matter, all connected filters are applied

### Pattern 5: Branching (NOT SUPPORTED YET)

```
[Source] → [Domain Filter] → [Splitter A]
        ↘ [Content Filter] → [Splitter B]
```
❌ Currently not supported - Only one path is followed

## Node Configuration Extraction Logic

### Step 1: Find Source Node

```python
source_node = next((n for n in pipeline.nodes if n.type in ['website', 'multiple_pages', 'single_page']), None)
```

### Step 2: Get All Connected Nodes

```python
connected_ids = _get_connected_nodes(source_node.id, pipeline.edges, pipeline.nodes)
```

### Step 3: Extract Filter Configs (If Connected)

```python
# Start with defaults from source node
allowed_subdomains = source_config.get("allowed_subdomains", [])
target_elements = source_config.get("target_elements", [])
output_format = source_config.get("output_format", "markdown")

# Override with filter node configs IF CONNECTED
if domain_filter_node and domain_filter_node.id in connected_ids:
    allowed_subdomains = domain_filter_node.config.get("allowed_subdomains", [])
    blocked_subdomains = domain_filter_node.config.get("blocked_subdomains", [])

if content_filter_node and content_filter_node.id in connected_ids:
    target_elements = content_filter_node.config.get("target_elements", [])

if output_format_node and output_format_node.id in connected_ids:
    output_format = output_format_node.config.get("output_format", "markdown")
```

### Step 4: Create Combined KnowledgeSourceConfig

```python
KnowledgeSourceConfigCreate(
    url=source_config["url"],
    crawl_depth=source_config["crawl_depth"],
    allowed_subdomains=allowed_subdomains,  # From domain filter OR default
    blocked_subdomains=blocked_subdomains,  # From domain filter OR default
    target_elements=target_elements,        # From content filter OR default
    output_format=output_format,            # From output format OR default
)
```

## Frontend Connection Validation

The frontend validates connections BEFORE saving to prevent invalid pipelines:

### Valid Connections (from pipelineRules.ts)

```typescript
// Data sources can connect to filters
{ from: 'website', to: 'domainFilter', allowed: true }
{ from: 'website', to: 'contentFilter', allowed: true }
{ from: 'website', to: 'outputFormat', allowed: true }

// Data sources can skip filters and go direct to splitter
{ from: 'website', to: 'textSplitter', allowed: true }

// Filters can chain to each other
{ from: 'domainFilter', to: 'contentFilter', allowed: true }
{ from: 'contentFilter', to: 'outputFormat', allowed: true }

// Filters must eventually connect to splitter
{ from: 'domainFilter', to: 'textSplitter', allowed: true }
{ from: 'contentFilter', to: 'textSplitter', allowed: true }
{ from: 'outputFormat', to: 'textSplitter', allowed: true }
```

### Invalid Connections (Will Be Rejected)

```typescript
// Can't connect filter to source (wrong direction)
{ from: 'domainFilter', to: 'website', allowed: false }

// Can't connect splitter to filter (wrong order)
{ from: 'textSplitter', to: 'domainFilter', allowed: false }

// Can't skip splitter and go direct to embedding
{ from: 'website', to: 'embeddingGenerator', allowed: false }
```

## Testing Your Pipeline

### Test Case 1: No Filters

**Setup:**
1. Drag Website Source → Configure (URL: https://example.com, Depth: 2)
2. Drag Text Splitter → Connect from Website Source
3. Drag Embedding Generator → Connect from Text Splitter
4. Drag Vector Database → Connect from Embedding Generator
5. Save & Execute

**Expected Result:**
- Website crawled with depth 2
- No domain filtering
- No CSS filtering
- Output: Markdown (default)

### Test Case 2: With Domain Filter

**Setup:**
1. Website Source (URL: https://example.com, Depth: 2)
2. Domain Filter (Allowed: ["docs", "help"]) → Connect from Website Source
3. Text Splitter → Connect from Domain Filter
4. Embedding Generator → Connect from Text Splitter
5. Vector Database → Connect from Embedding Generator
6. Save & Execute

**Expected Result:**
- Website crawled with depth 2
- ✅ Only docs.example.com and help.example.com are crawled
- No CSS filtering
- Output: Markdown (default)

### Test Case 3: All Filters

**Setup:**
1. Website Source (URL: https://example.com, Depth: 2)
2. Domain Filter (Allowed: ["docs"]) → Connect from Website Source
3. Content Filter (Target: [".main-content", "article"]) → Connect from Domain Filter
4. Output Format (Format: "llm_markdown") → Connect from Content Filter
5. Text Splitter → Connect from Output Format
6. ... rest of pipeline
7. Save & Execute

**Expected Result:**
- Website crawled with depth 2
- ✅ Only docs.example.com crawled
- ✅ Only .main-content and article elements extracted
- ✅ Output: LLM Markdown (AI-powered)

## Debugging Connection Issues

### Issue 1: Filter Not Being Applied

**Symptom:** You added a Domain Filter but all pages are still being crawled

**Check:**
1. Is the Domain Filter node **connected** to the source?
2. Check the connections: Source → Domain Filter → Splitter
3. Verify the edge exists in the saved pipeline JSON
4. Check backend logs for "connected_node_ids" to see what was found

**Fix:** Make sure you **dragged an edge** from Source to Domain Filter!

### Issue 2: Pipeline Won't Save

**Symptom:** "Invalid connection" error when saving

**Check:**
1. Review connection rules in pipelineRules.ts
2. Ensure data flows in correct direction: Source → Filters → Splitter → Embedding → Storage
3. No backwards connections (Filter → Source)
4. No skipping required nodes (Source → Embedding directly)

**Fix:** Reconnect nodes in valid order

### Issue 3: Wrong Filter Applied

**Symptom:** Expected Content Filter but Domain Filter was applied instead

**Check:**
1. Are BOTH filters connected in the pipeline?
2. Check edge order: Source → Filter1 → Filter2 → Splitter
3. Verify each filter node has its config saved (check configured: true)

**Fix:** Ensure ALL filters in your visual pipeline are connected AND configured

## Summary

### ✅ Key Takeaways

1. **Connections matter!** Only connected nodes are used
2. **Order is flexible** - Filters can be chained in any order
3. **Filters are optional** - Can skip directly to Text Splitter
4. **BFS algorithm** follows edges to find reachable nodes
5. **Visual = Actual** - What you see in the canvas is what gets executed

### 🎯 Best Practices

1. **Always connect your filters** if you want them applied
2. **Test incrementally** - Add one filter at a time
3. **Check the graph** - Verify edges are visible before saving
4. **Use validation** - Fix errors before executing
5. **Review extracted config** - Check backend logs to see combined config

### 📊 Pipeline Validation Checklist

Before executing, verify:
- [ ] Source node configured (URL + depth)
- [ ] All filters you want are **connected** (edges visible)
- [ ] Each filter node is configured (not just placed on canvas)
- [ ] Path exists: Source → ... → Splitter → Embedding → VectorDB
- [ ] No disconnected nodes (unless intentionally unused)
- [ ] Pipeline saves without validation errors

## Example: Complete Pipeline

```
┌──────────────────────────────────────────────────────────┐
│                     PIPELINE GRAPH                       │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [Website Source]                                        │
│  URL: https://docs.company.com                           │
│  Depth: 3                                                │
│         │                                                │
│         ↓                                                │
│  [Domain Filter] ← CONNECTED! Will be applied           │
│  Allowed: ["docs", "api", "guides"]                      │
│         │                                                │
│         ↓                                                │
│  [Content Filter] ← CONNECTED! Will be applied          │
│  Target: [".documentation", "article", ".content"]       │
│         │                                                │
│         ↓                                                │
│  [Output Format] ← CONNECTED! Will be applied           │
│  Format: LLM Markdown                                    │
│         │                                                │
│         ↓                                                │
│  [Text Splitter]                                         │
│  Chunk: 512, Overlap: 64                                 │
│         │                                                │
│         ↓                                                │
│  [Embedding Generator]                                   │
│  OpenAI text-embedding-3-small                           │
│         │                                                │
│         ↓                                                │
│  [Vector Database]                                       │
│  Collection: company_docs                                │
│                                                          │
└──────────────────────────────────────────────────────────┘

RESULT:
✅ Crawls docs.company.com, api.company.com, guides.company.com
✅ Extracts only .documentation, article, .content elements
✅ Converts to LLM Markdown format
✅ Splits into 512-token chunks
✅ Generates embeddings
✅ Stores in company_docs collection
```

Your visual pipeline IS your execution logic!
