# DataPilot Flow Wizard UX - Quick Reference Guide

## Visual Architecture Overview

### Knowledge Source Configuration Wizard (5 Steps)
```
┌─────────────────────────────────────────────────────────────────┐
│ ColorfulVerticalStepper Component                               │
├─────────────────────────┬───────────────────────────────────────┤
│                         │                                       │
│  Step Tracker (200px)   │  Content Area (Dynamic)              │
│                         │                                       │
│  [0] • Settings ✓       │  ┌─────────────────────────────────┐ │
│       Basic Info        │  │ STEP 0: Basic Info & Scraping   │ │
│       ─────────────     │  │                                 │ │
│       [name] ✓          │  │ Configuration name:  [_______]  │ │
│       [description]     │  │ Scraping mode:       [●website]│ │
│                         │  │ Website URL:         [_______]  │ │
│  [1] ● Filter           │  │ Crawl depth:         [4]        │ │
│       Domain Filtering  │  │                                 │ │
│       ─────────────     │  │ [Previous] [Next]               │ │
│       No validation     │  └─────────────────────────────────┘ │
│                         │                                       │
│  [2]   Content          │                                       │
│       Filter Elements   │                                       │
│       ─────────────     │                                       │
│       Optional          │                                       │
│                         │                                       │
│  [3]   Generation       │                                       │
│       Output Format     │                                       │
│       ─────────────     │                                       │
│       Optional          │                                       │
│                         │                                       │
│  [4]   Review           │                                       │
│       Confirmation      │                                       │
│       ─────────────     │                                       │
│       Always valid      │                                       │
│                         │                                       │
└─────────────────────────┴───────────────────────────────────────┘
```

### Knowledge Job Wizard (6 Steps)
```
Step 0: Job Setup
  ├─ config_id (required)
  ├─ name (required)
  └─ description (optional)
           ↓
Step 1: Vector DB Collection
  ├─ use_existing_collection (toggle)
  ├─ If new:
  │  ├─ collection_name (required)
  │  └─ vectordb_collection_description (optional)
  └─ If existing:
     └─ existing_collection_id (required)
           ↓
Step 2: Document Splitter
  ├─ splitter_type (text | document)
  ├─ If text:
  │  ├─ chunk_size (64-4096) ✓ auto-calculated
  │  └─ chunk_overlap (auto-calculated as 12.5%)
  └─ If document:
     └─ headers_to_split_on (array of patterns)
           ↓
Step 3: Embedding Model (skipped if using existing collection)
  ├─ embedding_model_provider_id (required if new)
  ├─ embedding_model_name (required if new)
  └─ vector_dimension (1-4096)
           ↓
Step 4: Processing Settings
  ├─ batch_size (1-1000)
  ├─ save_to_file (boolean)
  ├─ write_consolidated_file (boolean)
  ├─ clear_collection_before_start (boolean)
  └─ check_duplicates_before_insert (boolean)
           ↓
Step 5: Review & Create
  └─ Display all settings + alignment check
```

## Component File Structure

```
dashboard/src/
├── components/
│   └── colorful-vertical-stepper.tsx (Generic stepper component)
│       ├── Props: activeStep, completedSteps, steps[], onStepClick
│       ├── CSS Module: colorful-vertical-stepper.module.css
│       └── Features: Animations, color gradients, progress tracking
│
├── pages/dashboard/management/
│   └── knowledge-sources/
│       ├── config-create/index.tsx (Knowledge Source Wizard - Create)
│       ├── config-edit/index.tsx (Knowledge Source Wizard - Edit)
│       ├── job-create/index.tsx (Knowledge Job Wizard - Create/Edit)
│       ├── jobs/index.tsx (Jobs list with pipeline visualization)
│       └── configs/index.tsx (Configurations list)
```

## Field Dependency Tree

### Knowledge Source Wizard
```
scraping_mode
├─ single_page
│  └─ url (required)
├─ multiple_pages
│  └─ url_source (required)
│     ├─ file_name (from upload)
│     └─ urls[] (from file parsing)
└─ website
   ├─ url (required)
   └─ crawl_depth (0-6)

output_format
├─ html
│  └─ (no sub-fields)
└─ markdown
   └─ markdown_generation
      ├─ standard
      │  └─ content_filter_threshold (0-1)
      └─ llm
         └─ llm_content_filter_id (or create new)
            ├─ name
            ├─ llm_provider_id
            ├─ llm_model_name
            ├─ instruction
            ├─ temperature
            ├─ max_retries
            └─ timeout_seconds
```

### Knowledge Job Wizard
```
use_existing_collection
├─ true
│  └─ existing_collection_id (required)
│     └─ Inherits: embedding_model_provider_id, embedding_model_name, vector_dimension
└─ false
   ├─ collection_name (required)
   └─ Then in Step 3:
      ├─ embedding_model_provider_id (required)
      └─ embedding_model_name (required)

splitter_type
├─ text
│  ├─ chunk_size (64-4096)
│  └─ chunk_overlap (auto-calculated)
└─ document
   └─ headers_to_split_on (array)

save_to_file
└─ true
   └─ write_consolidated_file (can be toggled)
```

## Color Scheme Reference

### Knowledge Source Wizard Steps
```
Step 0: #45c9bb (Teal)      → Basic Configuration
Step 1: #bbe773 (Green)     → Filtering
Step 2: #ddde65 (Yellow)    → Content Selection
Step 3: #3bc57d (Dark Green)→ Output Processing
Step 4: #ae89ae (Purple)    → Review
```

### Knowledge Job Wizard Steps
```
Step 0: #45c9bb (Teal)      → Job Setup
Step 1: #bbe773 (Green)     → Vector DB
Step 2: #ddde65 (Yellow)    → Document Splitting
Step 3: #3bc57d (Dark Green)→ Embedding Model
Step 4: #ae89ae (Purple)    → Processing
Step 5: #45c9bb→#3bc57d     → Review & Create
```

## Validation Rules at Each Step

### Knowledge Source Wizard Validation
```
Step 0: REQUIRED
├─ name: non-empty string
├─ scraping_mode: one of [single_page, multiple_pages, website]
└─ url: (conditional)
   ├─ if scraping_mode=single_page: required, valid URL
   ├─ if scraping_mode=website: required, valid URL
   └─ if scraping_mode=multiple_pages: not required

Step 1: OPTIONAL ✓ Always valid

Step 2: OPTIONAL ✓ Always valid

Step 3: OPTIONAL ✓ Always valid (unless LLM provider is inactive)

Step 4: REVIEW ONLY ✓ Always valid
```

### Knowledge Job Wizard Validation
```
Step 0: REQUIRED
├─ config_id: non-empty string
└─ name: non-empty string

Step 1: REQUIRED (context-dependent)
├─ if use_existing_collection=true: existing_collection_id required
└─ if use_existing_collection=false: collection_name required

Step 2: REQUIRED (context-dependent)
├─ if splitter_type=text:
│  ├─ chunk_size: 64-4096
│  └─ chunk_overlap: 0 to floor(chunk_size/2)
└─ if splitter_type=document: ✓ Always valid

Step 3: REQUIRED (conditional on collection mode)
├─ if use_existing_collection=true: ✓ SKIPPED (auto-valid)
└─ if use_existing_collection=false:
   ├─ embedding_model_provider_id: required, must be active
   ├─ embedding_model_name: required
   └─ vector_dimension: 1-4096

Step 4: REQUIRED
└─ batch_size: 1-1000

Step 5: REVIEW ONLY ✓ Always valid
```

## UX Patterns Applied

### Pattern Matrix
```
Pattern                          Knowledge Source  Knowledge Job
─────────────────────────────────────────────────────────────────
1. Conditional Field Visibility       ✓              ✓
2. Modal Sub-wizards                  ✓              
3. Floating Test Panels               ✓              
4. Auto-calculation                                  ✓
5. Smart Recommendations                            ✓
6. Progressive Disclosure             ✓              ✓
7. API Validation                                    ✓
8. Review & Confirmation              ✓              ✓
9. Breadcrumb Navigation              ✓              ✓
10. Edit Mode State Preservation                    ✓
```

## Common UI Components Used

```
Inputs:
├─ TextInput (name, description, URL, selectors)
├─ Textarea (descriptions, instructions)
├─ NumberInput (chunk size, crawl depth, dimensions)
├─ Select/MultiSelect (provider, model, collections)
└─ FileInput (URL list uploads)

Layouts:
├─ Stack (vertical grouping)
├─ Group (horizontal alignment)
├─ Card (section containers)
└─ SimpleGrid (review displays)

Controls:
├─ Button (Next, Previous, Submit)
├─ Radio.Group (single choice)
├─ Switch (toggles)
├─ ActionIcon (add, remove, delete)
└─ Divider (section separators)

Feedback:
├─ Alert (information, warnings, errors)
├─ Modal (sub-wizards, confirmations)
├─ Notification (toast messages)
└─ Badge (status indicators)
```

## Navigation State Machine

```
     ┌─────────────────────────────────────────┐
     │  Active Step (activeStep state)         │
     ├─────────────────────────────────────────┤
     │                                         │
     │  NextButton  PrevButton  StepClick     │
     │     ↓           ↓           ↓          │
     │  Validate   AllowIfActive Allow/Block  │
     │  Progress   +moveBack      Context     │
     │                                         │
     │  CompletedSteps[] tracks progress      │
     │  ├─ Can only click back or next→current│
     │  ├─ Can only click completed steps     │
     │  ├─ Cannot skip ahead                  │
     │  └─ Moves to completed when advancing  │
     │                                         │
     └─────────────────────────────────────────┘
```

## Animation Timeline

```
Content Card Transition (300ms):
├─ 0ms:   Old content fade out (0.3s)
├─ 150ms: New content fade in starts
└─ 300ms: New content fully visible

Step Progress:
├─ 0ms:    Step indicator scales (0.3s)
├─ 300ms:  Connecting line grows (0.6s)
├─ 400ms:  Content card slides in (0.4s)
└─ 600ms:  Animations complete

Active Step Pulse:
├─ Repeats every 2s
├─ 0-50%:   Opacity 1 → 0.8
└─ 50-100%: Opacity 0.8 → 1
```

## Form State Example

```typescript
// Knowledge Source Configuration
{
  name: "API Documentation",                    // Step 0
  description: "Scraped from docs.example.com", // Step 0
  scraping_mode: "website",                     // Step 0
  url: "https://docs.example.com",              // Step 0
  crawl_depth: 3,                               // Step 0
  
  allowed_subdomains: ["api", "docs"],          // Step 1 (Optional)
  blocked_subdomains: ["test", "dev"],          // Step 1 (Optional)
  url_patterns: [
    { pattern: "*/admin/*", reverse: true }     // Step 1 (Optional)
  ],
  
  target_elements: ["main", "article"],         // Step 2 (Optional)
  
  output_format: "markdown",                    // Step 3 (Optional)
  markdown_generation: "llm",                   // Step 3 (Optional)
  content_filter_threshold: 0.6,                // Step 3 (Optional)
  llm_content_filter_id: "filter-123",          // Step 3 (Optional)
}
```

## Error Handling Flow

```
User Action
    ↓
Validation Check
    ├─ PASS → Proceed to next action
    │         ├─ Navigate to next step
    │         ├─ Submit form
    │         └─ Update field
    │
    └─ FAIL → Show Error Feedback
              ├─ Toast Notification
              │  (for API errors, field invalid)
              │
              ├─ Inline Error
              │  (under form field)
              │
              ├─ Alert Box
              │  (for validation messages)
              │
              └─ Prevent Navigation
                 (block step change if invalid)
```

## Editor Recommendations for Pipeline Builder

Based on analyzed patterns, adopt:

1. **Visual Language**: Same colors, animations, patterns
2. **Navigation**: ColorfulVerticalStepper for multi-stage workflows
3. **Modals**: For node configuration (not full pages)
4. **State**: Form-based with validation before progression
5. **Feedback**: Floating panels for testing/preview
6. **Validation**: Real-time with clear error messages
7. **Review**: Final confirmation step before execution

---

**File Location**: `/Users/bassem.elsodany/workspaces/datapilotflow/WIZARD_ANALYSIS.md`

For full implementation details, refer to the comprehensive analysis document.
