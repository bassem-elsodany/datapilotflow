# Pipeline Builder UX Improvement Proposal

## Executive Summary

Transform the pipeline builder from a complex single-node configuration system into an **attractive, step-by-step journey** that mirrors your existing wizard UX patterns. Instead of cramming all configurations into one node, we'll break it down into **bite-sized, beautiful steps** with visual feedback and intelligent guidance.

---

## 🎯 Core Philosophy

### Current Problem
- **All configuration in one node** = overwhelming
- **No visual progression** = confusing
- **No guidance** = users don't know what to do next

### New Vision
**"Each node is a mini-wizard"** - When you click a node, you get a delightful, guided configuration experience that feels like a natural conversation.

---

## 🎨 Visual Design Concepts

### Concept 1: Node Configuration Modal with Embedded Stepper

```
┌────────────────────────────────────────────────────────────────┐
│  Configure: Website Source Node                          [×]   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────┬────────────────────────────────────────────┐ │
│  │             │                                            │ │
│  │  ●  Basic   │  Step 1: Basic Information                │ │
│  │  │          │                                            │ │
│  │  ●  URLs    │  Configuration Name *                     │ │
│  │  │          │  ┌──────────────────────────────────────┐ │ │
│  │  ○  Filter  │  │ My Website Source                    │ │ │
│  │  │          │  └──────────────────────────────────────┘ │ │
│  │  ○  Content │                                            │ │
│  │  │          │  Website URL *                            │ │
│  │  ○  Output  │  ┌──────────────────────────────────────┐ │ │
│  │             │  │ https://docs.example.com             │ │ │
│  │             │  └──────────────────────────────────────┘ │ │
│  │             │                                            │ │
│  │             │  Crawl Depth                              │ │
│  │             │  ├─────●───────────────┤ 4 levels        │ │
│  │             │  0  2  4  6  8  10                        │ │
│  │             │                                            │ │
│  │             │  [Previous]              [Next: URLs →]   │ │
│  │             │                                            │ │
│  └─────────────┴────────────────────────────────────────────┘ │
│                                                                │
│  💡 Tip: Start with depth 2-4 for best balance of coverage   │
│      and crawl time                                            │
└────────────────────────────────────────────────────────────────┘
```

### Concept 2: Compact Node Cards with Smart Defaults

```
PIPELINE CANVAS:
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  📄 Website     │────→│  ✂️  Splitter    │────→│  🎯 Embedding   │
│                 │     │                  │     │                 │
│  docs.ex...com  │     │  512 chunks      │     │  OpenAI Ada     │
│  ✓ Configured   │     │  ⚠️  Review      │     │  ○ Not set      │
│                 │     │                  │     │                 │
│  [Edit]         │     │  [Configure]     │     │  [Configure]    │
└─────────────────┘     └──────────────────┘     └─────────────────┘

STATUS BAR:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pipeline: Documentation Ingestion    Progress: 2/4 nodes configured
[Save Draft]                                    [▶ Run Pipeline]
```

---

## 📋 Node Type Breakdown & Configuration Steps

### 1. **Data Source Nodes** (Website, Multiple Pages, Single Page, Confluence)

#### Website Source Node - 5 Steps (mirrors existing wizard)

**Step 0: Basic Info & Scraping** (Teal #45c9bb)
```
┌─────────────────────────────────────────────────┐
│ ● STEP 1: BASIC INFORMATION                    │
├─────────────────────────────────────────────────┤
│                                                 │
│ Node Name *                                     │
│ ┌─────────────────────────────────────────────┐ │
│ │ Company Documentation Crawler              │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Description (optional)                          │
│ ┌─────────────────────────────────────────────┐ │
│ │ Crawls internal documentation site          │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Website URL *                                   │
│ ┌─────────────────────────────────────────────┐ │
│ │ https://docs.company.com                    │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Crawl Depth (how many link levels to follow)   │
│ ┌─────────────────────────────────────────────┐ │
│ │ ├───●─────────┤ 4 levels                    │ │
│ │ 0  2  4  6  8  10                            │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ 💡 Recommended: 2-4 levels for documentation   │
│                                                 │
│              [Cancel]      [Next: Filtering →] │
└─────────────────────────────────────────────────┘
```

**Step 1: Domain Filtering** (Green #bbe773) - OPTIONAL
```
┌─────────────────────────────────────────────────┐
│ ● STEP 2: DOMAIN FILTERING (OPTIONAL)          │
├─────────────────────────────────────────────────┤
│                                                 │
│ ☑️ Allow All Subdomains                        │
│                                                 │
│ OR Specify allowed subdomains:                  │
│ ┌─────────────────────────────────────────────┐ │
│ │ docs.company.com              [+ Add more]  │ │
│ │ help.company.com              [× Remove]    │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Block specific subdomains:                      │
│ ┌─────────────────────────────────────────────┐ │
│ │ blog.company.com              [× Remove]    │ │
│ │                                 [+ Add]     │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ URL Patterns (advanced):                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ /api/**           [× Remove]                │ │
│ │ /docs/**          [× Remove]                │ │
│ │                               [+ Add]       │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ℹ️  Leave empty to crawl all subdomains        │
│                                                 │
│         [← Previous]   [Skip]   [Next: Content →] │
└─────────────────────────────────────────────────┘
```

**Step 2: Content Filtering** (Yellow #ddde65) - OPTIONAL
```
┌─────────────────────────────────────────────────┐
│ ● STEP 3: CONTENT FILTERING (OPTIONAL)         │
├─────────────────────────────────────────────────┤
│                                                 │
│ Target specific HTML elements:                  │
│ ┌─────────────────────────────────────────────┐ │
│ │ CSS Selector              [+ Add]           │ │
│ ├─────────────────────────────────────────────┤ │
│ │ main                      [× Remove]        │ │
│ │ article                   [× Remove]        │ │
│ │ .documentation-content    [× Remove]        │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [🔍 Test Selector on Page]                     │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ PREVIEW (if test clicked):                  │ │
│ │ ✓ Found 15 matching elements               │ │
│ │                                             │ │
│ │ <main class="docs-main">                    │ │
│ │   <article>                                 │ │
│ │     Content preview...                      │ │
│ │   </article>                                │ │
│ │ </main>                                     │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ℹ️  Leave empty to extract entire page content │
│                                                 │
│         [← Previous]   [Skip]   [Next: Output →] │
└─────────────────────────────────────────────────┘
```

**Step 3: Output Format** (Dark Green #3bc57d) - OPTIONAL
```
┌─────────────────────────────────────────────────┐
│ ● STEP 4: OUTPUT FORMAT (OPTIONAL)             │
├─────────────────────────────────────────────────┤
│                                                 │
│ Output Format:                                  │
│ ┌─────────────────────────────────────────────┐ │
│ │  ○ HTML (raw)                               │ │
│ │  ● Markdown (structured)         [Selected] │ │
│ │  ○ LLM Markdown (AI-powered)                │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ IF Markdown selected:                           │
│ ┌─────────────────────────────────────────────┐ │
│ │ Markdown Generation Method:                 │ │
│ │  ● Standard (built-in converter)            │ │
│ │  ○ LLM-powered (better quality)             │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ IF LLM-powered selected:                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ Content Filter:                             │ │
│ │  ● Use existing: [Select Filter ▼]         │ │
│ │  ○ Create new filter                        │ │
│ │                                             │ │
│ │  [Create New LLM Content Filter]            │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ⚠️  LLM processing adds cost (~$0.001/page)    │
│                                                 │
│           [← Previous]   [Skip]   [Next: Review →] │
└─────────────────────────────────────────────────┘
```

**Step 4: Review & Confirm** (Purple #ae89ae)
```
┌─────────────────────────────────────────────────┐
│ ● STEP 5: REVIEW & CONFIRM                     │
├─────────────────────────────────────────────────┤
│                                                 │
│ Configuration Summary:                          │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ ✓ Basic Information                         │ │
│ │   Name: Company Documentation Crawler       │ │
│ │   URL: https://docs.company.com             │ │
│ │   Crawl Depth: 4 levels                     │ │
│ │                                             │ │
│ │ ✓ Domain Filtering                          │ │
│ │   Allowed: docs.*, help.*                   │ │
│ │   Blocked: blog.*                           │ │
│ │                                             │ │
│ │ ✓ Content Filtering                         │ │
│ │   Target: main, article, .docs-content      │ │
│ │                                             │ │
│ │ ✓ Output Format                             │ │
│ │   Format: Markdown (standard)               │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [← Edit]                    [✓ Save & Close]   │
└─────────────────────────────────────────────────┘
```

---

### 2. **Text Splitter Node** - 3 Steps

**Step 0: Splitter Type** (Teal)
```
┌─────────────────────────────────────────────────┐
│ ● STEP 1: CHOOSE SPLITTER TYPE                 │
├─────────────────────────────────────────────────┤
│                                                 │
│ Node Name *                                     │
│ ┌─────────────────────────────────────────────┐ │
│ │ Documentation Splitter                      │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Splitter Type:                                  │
│ ┌───────────────────────────┬─────────────────┐ │
│ │ ● TEXT SPLITTER          │ ○ DOCUMENT      │ │
│ │                          │   SPLITTER      │ │
│ │ Split by character count │ Split by        │ │
│ │ (best for most use cases)│ headers         │ │
│ │                          │ (Markdown/HTML) │ │
│ └───────────────────────────┴─────────────────┘ │
│                                                 │
│ 💡 Recommended: Text splitter for documentation │
│                                                 │
│              [Cancel]         [Next: Settings →]│
└─────────────────────────────────────────────────┘
```

**Step 1: Chunk Settings** (Green)
```
┌─────────────────────────────────────────────────┐
│ ● STEP 2: CHUNK SETTINGS                       │
├─────────────────────────────────────────────────┤
│                                                 │
│ Chunk Size (characters):                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ ├────────●──────────┤ 512                   │ │
│ │ 64   256   512  1024  2048  4096            │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Chunk Overlap:                                  │
│ ┌─────────────────────────────────────────────┐ │
│ │ ⚙️  Auto-calculated: 64 chars (12.5%)       │ │
│ │ [✓] Use smart overlap                       │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Text Separators:                                │
│ ┌─────────────────────────────────────────────┐ │
│ │ 1. Paragraph breaks (\n\n)                  │ │
│ │ 2. Line breaks (\n)                         │ │
│ │ 3. Spaces ( )                               │ │
│ │ 4. No separator                             │ │
│ │                                             │ │
│ │ [+ Add Custom Separator]                    │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ 💡 512-1024 chunks work best with most models  │
│                                                 │
│           [← Previous]            [Next: Review →]│
└─────────────────────────────────────────────────┘
```

**Step 2: Review**
```
┌─────────────────────────────────────────────────┐
│ ● STEP 3: REVIEW                                │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ ✓ Configuration Complete                    │ │
│ │                                             │ │
│ │   Type: Text Splitter                       │ │
│ │   Chunk Size: 512 characters                │ │
│ │   Overlap: 64 characters (12.5%)            │ │
│ │   Separators: \n\n, \n, space               │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [← Edit]                    [✓ Save & Close]   │
└─────────────────────────────────────────────────┘
```

---

### 3. **Embedding Generator Node** - 3 Steps

**Step 0: Provider Selection** (Teal)
```
┌─────────────────────────────────────────────────┐
│ ● STEP 1: SELECT PROVIDER                      │
├─────────────────────────────────────────────────┤
│                                                 │
│ Node Name *                                     │
│ ┌─────────────────────────────────────────────┐ │
│ │ OpenAI Embeddings                           │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Embedding Provider:                             │
│ ┌─────────────────────────────────────────────┐ │
│ │ Search providers...                         │ │
│ ├─────────────────────────────────────────────┤ │
│ │ ● OpenAI                       ✓ Active     │ │
│ │   API Key configured                        │ │
│ ├─────────────────────────────────────────────┤ │
│ │ ○ Azure OpenAI                 ⚠️  Setup    │ │
│ │   Requires configuration                    │ │
│ ├─────────────────────────────────────────────┤ │
│ │ ○ Cohere                       ✓ Active     │ │
│ │   API Key configured                        │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [Manage Providers]                              │
│                                                 │
│              [Cancel]          [Next: Model →] │
└─────────────────────────────────────────────────┘
```

**Step 1: Model Selection** (Green)
```
┌─────────────────────────────────────────────────┐
│ ● STEP 2: SELECT MODEL                         │
├─────────────────────────────────────────────────┤
│                                                 │
│ Embedding Model:                                │
│ ┌─────────────────────────────────────────────┐ │
│ │ ● text-embedding-3-small                    │ │
│ │   Dimensions: 1536                          │ │
│ │   Cost: $0.02 per 1M tokens                 │ │
│ │   💡 Best balance of quality and cost       │ │
│ │                                             │ │
│ │ ○ text-embedding-3-large                    │ │
│ │   Dimensions: 3072                          │ │
│ │   Cost: $0.13 per 1M tokens                 │ │
│ │   Higher accuracy, more expensive           │ │
│ │                                             │ │
│ │ ○ text-embedding-ada-002                    │ │
│ │   Dimensions: 1536                          │ │
│ │   Cost: $0.10 per 1M tokens                 │ │
│ │   Legacy model (older version)              │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Vector Dimension: 1536 (auto-set)               │
│                                                 │
│           [← Previous]         [Next: Settings →]│
└─────────────────────────────────────────────────┘
```

**Step 2: Processing Settings** (Yellow)
```
┌─────────────────────────────────────────────────┐
│ ● STEP 3: PROCESSING SETTINGS                  │
├─────────────────────────────────────────────────┤
│                                                 │
│ Batch Size:                                     │
│ ┌─────────────────────────────────────────────┐ │
│ │ ├──────●────────┤ 100 chunks                │ │
│ │ 1   50  100  500  1000                       │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ℹ️  Process 100 chunks at a time               │
│    Larger batches = faster but more memory     │
│                                                 │
│ [← Previous]                    [Next: Review →]│
└─────────────────────────────────────────────────┘
```

---

### 4. **Vector Database Node** - 2 Steps

**Step 0: Collection Setup** (Teal)
```
┌─────────────────────────────────────────────────┐
│ ● STEP 1: COLLECTION SETUP                     │
├─────────────────────────────────────────────────┤
│                                                 │
│ Node Name *                                     │
│ ┌─────────────────────────────────────────────┐ │
│ │ Documentation Vector Store                  │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Collection Option:                              │
│ ┌───────────────────────┬─────────────────────┐ │
│ │ ● CREATE NEW         │ ○ USE EXISTING      │ │
│ │                      │                     │ │
│ │ Start fresh          │ Add to existing     │ │
│ │ collection           │ collection          │ │
│ └───────────────────────┴─────────────────────┘ │
│                                                 │
│ IF CREATE NEW:                                  │
│ ┌─────────────────────────────────────────────┐ │
│ │ Collection Name *                           │ │
│ │ ┌─────────────────────────────────────────┐ │ │
│ │ │ company_docs_v1                         │ │ │
│ │ └─────────────────────────────────────────┘ │ │
│ │                                             │ │
│ │ Description (optional)                      │ │
│ │ ┌─────────────────────────────────────────┐ │ │
│ │ │ Company documentation knowledge base    │ │ │
│ │ └─────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ⚙️  Inherits embedding config from generator   │
│     Model: text-embedding-3-small               │
│     Dimensions: 1536                            │
│                                                 │
│              [Cancel]        [Next: Options →] │
└─────────────────────────────────────────────────┘
```

**Step 1: Advanced Options** (Green)
```
┌─────────────────────────────────────────────────┐
│ ● STEP 2: ADVANCED OPTIONS                     │
├─────────────────────────────────────────────────┤
│                                                 │
│ Collection Management:                          │
│ ┌─────────────────────────────────────────────┐ │
│ │ ☑️ Clear collection before starting         │ │
│ │    Remove all existing data first           │ │
│ │                                             │ │
│ │ ☐ Check for duplicates                      │ │
│ │    Skip documents already in collection     │ │
│ │    (slower but prevents duplicates)         │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ⚠️  Clearing collection deletes all data       │
│                                                 │
│           [← Previous]         [✓ Save & Close]│
└─────────────────────────────────────────────────┘
```

---

### 5. **File Export Node** - 2 Steps (Simple)

**Step 0: Export Settings**
```
┌─────────────────────────────────────────────────┐
│ ● STEP 1: EXPORT SETTINGS                      │
├─────────────────────────────────────────────────┤
│                                                 │
│ Node Name *                                     │
│ ┌─────────────────────────────────────────────┐ │
│ │ Export Processed Documents                  │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ File Format:                                    │
│ ┌─────────────────────────────────────────────┐ │
│ │  ● JSON (structured)                        │ │
│ │  ○ CSV (tabular)                            │ │
│ │  ○ Markdown (readable)                      │ │
│ │  ○ Text (plain)                             │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Output Options:                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ ☑️ Save individual files                    │ │
│ │    One file per document                    │ │
│ │                                             │ │
│ │ ☐ Create consolidated file                  │ │
│ │    All documents in one file (large!)       │ │
│ │                                             │ │
│ │ ☑️ Include metadata                         │ │
│ │    Source URL, timestamps, etc.             │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ℹ️  Files saved to: ./output/                  │
│                                                 │
│              [Cancel]          [✓ Save & Close]│
└─────────────────────────────────────────────────┘
```

---

## 🎯 New UI Components Needed

### 1. **Node Configuration Modal** (New Component)

**File**: `dashboard/src/pages/dashboard/management/pipeline-builder/components/NodeConfigModal.tsx`

```typescript
interface NodeConfigModalProps {
  node: PipelineNode;
  opened: boolean;
  onClose: () => void;
  onSave: (config: any) => void;
}

// Uses ColorfulVerticalStepper inside modal
// Each node type has its own step configuration
```

### 2. **Enhanced Node Card** (Update Existing)

```typescript
// Current node is just a box
// New node shows:
- Icon (based on type)
- Status indicator (not configured, configured, running, error)
- Quick preview of config (e.g., "docs.example.com, depth: 4")
- Visual connection points
- [Configure] button that opens modal
```

### 3. **Pipeline Progress Bar** (New)

```typescript
// Shows overall pipeline readiness
┌────────────────────────────────────────────────┐
│ Pipeline Readiness:  ████████░░  75%           │
│                                                │
│ ✓ Source configured                           │
│ ✓ Splitter configured                         │
│ ✓ Embeddings configured                       │
│ ⚠️  Vector database needs configuration       │
└────────────────────────────────────────────────┘
```

### 4. **Smart Connection Rules** (Enhanced)

```typescript
// Visual feedback when connecting nodes
// Green line = valid connection
// Red line with error message = invalid

INVALID CONNECTION:
  [Embedding] ──×──> [Website]
     ❌ Cannot connect: Embedding must come after Splitter

VALID CONNECTION:
  [Website] ──✓──> [Splitter]
     ✅ Valid: Data source → Processing
```

---

## 🚀 Implementation Plan

### Phase 1: Core Modal System (Week 1)
- [ ] Create `NodeConfigModal.tsx` wrapper component
- [ ] Integrate `ColorfulVerticalStepper` into modal
- [ ] Build step configurations for Website Source node (5 steps)
- [ ] Add save/cancel logic with validation
- [ ] Update node card to show config preview

### Phase 2: Essential Nodes (Week 2)
- [ ] Text Splitter node configuration (3 steps)
- [ ] Embedding Generator node configuration (3 steps)
- [ ] Vector Database node configuration (2 steps)
- [ ] Test full pipeline flow: Source → Splitter → Embedding → VectorDB

### Phase 3: Polish & Enhancement (Week 3)
- [ ] Add Pipeline Progress Bar
- [ ] Enhanced connection validation with visual feedback
- [ ] Smart defaults and auto-configuration
- [ ] Node status indicators (configured, error, running)
- [ ] Tooltips and contextual help

### Phase 4: Advanced Features (Week 4)
- [ ] File Export node
- [ ] Report Generator node
- [ ] Pipeline templates (save & load)
- [ ] Duplicate pipeline functionality
- [ ] Export/import pipeline as JSON

---

## 💡 Smart Features to Add

### 1. **Auto-Configuration Chain**
When you configure one node, smart defaults propagate:
```
Configure Website Source with URL "docs.example.com"
  ↓ Auto-suggests node name
Splitter Node → Auto-names "docs.example.com Splitter"
  ↓ Auto-calculates chunk size
Embedding → Suggests best model for documentation
  ↓ Auto-sets dimensions
Vector DB → Auto-names "docs_example_com_collection"
```

### 2. **Configuration Validation Panel**
```
┌────────────────────────────────────────────────┐
│ 🔍 PIPELINE VALIDATION                         │
├────────────────────────────────────────────────┤
│ ✓ All required nodes present                  │
│ ✓ All nodes configured                        │
│ ✓ Connections are valid                       │
│ ⚠️  Warning: Large crawl depth may take time  │
│                                                │
│ Estimated processing time: ~30 minutes         │
│ Estimated cost: ~$2.50                         │
│                                                │
│ [✓ Ready to Run]                               │
└────────────────────────────────────────────────┘
```

### 3. **Quick Actions Menu**
Right-click any node:
```
┌─────────────────────────┐
│ ⚙️  Configure           │
│ 📋 Duplicate            │
│ 🗑️  Delete              │
│ 📄 View Configuration   │
│ 🔗 Show Connections     │
└─────────────────────────┘
```

### 4. **Pipeline Templates**
Pre-built templates for common use cases:
```
📚 Documentation Crawler
   Website → Splitter → Embedding → VectorDB

📰 Blog Content Ingestion
   Multiple Pages → LLM Filter → Splitter → Embedding → VectorDB

🎓 Course Materials
   Confluence → Document Splitter → Embedding → VectorDB + File Export
```

---

## 🎨 Visual Design Guidelines

### Color Palette (from existing wizards)
```css
/* Step colors */
--step-basic: #45c9bb;      /* Teal - Input/Setup */
--step-filter: #bbe773;     /* Green - Filtering */
--step-content: #ddde65;    /* Yellow - Content */
--step-advanced: #3bc57d;   /* Dark Green - Processing */
--step-review: #ae89ae;     /* Purple - Review */

/* Status colors */
--status-not-configured: #e0e0e0;  /* Gray */
--status-configured: #3bc57d;      /* Green */
--status-running: #45c9bb;         /* Teal */
--status-error: #ff6b6b;           /* Red */
--status-warning: #ffc107;         /* Yellow */
```

### Animation Timings (match existing)
```css
--fade-in: 300ms;
--slide-in: 400ms;
--pulse: 2s infinite;
--hover-translate: 6px;
```

### Node Visual States
```
NOT CONFIGURED:
┌─────────────────┐
│  📄 Website     │  Gray border, dashed
│                 │
│  ○ Not set      │
│  [Configure]    │
└─────────────────┘

CONFIGURED:
┌─────────────────┐
│  📄 Website     │  Green border, solid
│  ✓ Configured   │
│  docs.ex...com  │  Shows preview
│  [Edit]         │
└─────────────────┘

RUNNING:
┌─────────────────┐
│  📄 Website     │  Blue border, pulsing
│  ⚙️  Running    │
│  Progress: 45%  │  Shows progress
│  [View Logs]    │
└─────────────────┘

ERROR:
┌─────────────────┐
│  📄 Website     │  Red border, solid
│  ❌ Error       │
│  Connection...  │  Shows error
│  [Fix] [Retry]  │
└─────────────────┘
```

---

## 📊 User Journey Comparison

### Before (Current - Overwhelming)
```
1. Open pipeline builder
2. Add Website node
3. Click node → HUGE configuration form appears
4. User sees 20+ fields at once
5. Overwhelmed, confused, quits
```

### After (Proposed - Delightful)
```
1. Open pipeline builder
2. Add Website node
3. Click "Configure" → Modal opens with Step 1/5
4. Fill 3 basic fields → Click "Next"
5. See filtering options → Skip if not needed
6. Content selection → Test selectors with preview
7. Output format → Choose from 3 options
8. Review summary → Looks good!
9. Click "Save & Close"
10. Node shows green checkmark ✓
11. Add next node → Repeat enjoyable process
12. Click "Run Pipeline" → Everything works!
```

---

## 🎯 Success Metrics

### User Experience
- **Configuration time**: Reduce from 10+ minutes to 3-5 minutes
- **Error rate**: Reduce invalid configurations by 80%
- **Completion rate**: Increase from 40% to 90%
- **User satisfaction**: "This is actually fun!" feedback

### Technical
- **Code reuse**: 90% component reuse from existing wizards
- **Consistency**: 100% visual/UX alignment with existing patterns
- **Performance**: Modal opens in <100ms
- **Validation**: Real-time, step-by-step

---

## 📝 Next Steps

1. **Review this proposal** - Get feedback from team/stakeholders
2. **Prioritize features** - Which nodes need configuration first?
3. **Start with Phase 1** - Build the modal system
4. **Iterate quickly** - Ship one node type, get feedback, improve
5. **Expand gradually** - Add more node types based on usage

---

## 🤔 Open Questions

1. Should we allow "Quick Configure" with smart defaults vs full wizard?
2. Do we need a "Pipeline Template Library" right away?
3. Should nodes auto-connect when added (if only one valid connection)?
4. Do we want "Test Pipeline" mode (dry run without execution)?
5. Should configuration be saved automatically or require explicit save?

---

**Ready to make your pipeline builder the most attractive and easy-to-use part of your application!** 🚀

Let's discuss which approach you prefer and start building!
