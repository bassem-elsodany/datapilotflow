# DataPilot Flow - Wizard Implementation Analysis

Complete documentation of the existing wizard implementations for knowledge sources and jobs.

## Documentation Files

### 1. **ANALYSIS_SUMMARY.txt** (9.3KB)
**Start here** - High-level overview and key findings
- Executive summary of both wizard flows
- Architecture overview
- Key findings and recommendations
- Quick reference to all patterns

### 2. **WIZARD_ANALYSIS.md** (23KB)
**Main reference** - Comprehensive technical documentation
- Detailed step-by-step flow for each wizard
- Complete field specifications and validation rules
- Configuration state examples
- UX patterns with implementation details
- Component reusability notes
- Performance and accessibility considerations

### 3. **WIZARD_UX_QUICK_REFERENCE.md** (14KB)
**Visual guide** - Diagrams and quick lookups
- ASCII architecture diagrams
- Field dependency trees
- Color scheme reference
- Validation rules matrix
- UX patterns comparison table
- Error handling flow diagrams

---

## Quick Navigation

### For Designers
1. Read: ANALYSIS_SUMMARY.txt (sections: "ARCHITECTURE" and "COLOR SCHEME")
2. Review: WIZARD_UX_QUICK_REFERENCE.md (sections: "Visual Architecture" and "Color Scheme Reference")
3. Study: WIZARD_ANALYSIS.md (section: "4. CURRENT UX PATTERNS")

### For Developers
1. Read: ANALYSIS_SUMMARY.txt (full document)
2. Study: WIZARD_ANALYSIS.md (sections: "1. KNOWLEDGE SOURCE WIZARD" and "2. KNOWLEDGE JOB WIZARD")
3. Reference: WIZARD_UX_QUICK_REFERENCE.md (sections: "Component File Structure" and "Navigation State Machine")
4. Code: Check the actual implementations in `/dashboard/src/`

### For Pipeline Builder Implementation
1. Start: ANALYSIS_SUMMARY.txt (section: "RECOMMENDATIONS FOR PIPELINE BUILDER UX")
2. Study: WIZARD_UX_QUICK_REFERENCE.md (section: "Editor Recommendations for Pipeline Builder")
3. Reference: WIZARD_ANALYSIS.md (section: "6. RECOMMENDED PATTERNS FOR PIPELINE BUILDER UX")
4. Patterns: WIZARD_ANALYSIS.md (section: "4. CURRENT UX PATTERNS")

---

## Key Components Analyzed

### ColorfulVerticalStepper
- **Location**: `/dashboard/src/components/colorful-vertical-stepper.tsx`
- **Type**: Generic, reusable multi-step wizard component
- **Purpose**: Left sidebar step tracker + right content area
- **Features**: Animations, color gradients, progress tracking

### Knowledge Source Configuration Wizard
- **Create**: `/dashboard/src/pages/dashboard/management/knowledge-sources/config-create/index.tsx`
- **Edit**: `/dashboard/src/pages/dashboard/management/knowledge-sources/config-edit/index.tsx`
- **Steps**: 5 (Basic Info, Filtering, Content, Generation, Review)
- **Fields**: 15+ configuration parameters

### Knowledge Job Wizard
- **Create/Edit**: `/dashboard/src/pages/dashboard/management/knowledge-sources/job-create/index.tsx`
- **Steps**: 6 (Setup, Collection, Splitter, Embedding, Processing, Review)
- **Fields**: 20+ configuration parameters including complex nested objects

---

## Key Patterns Identified

| # | Pattern | Knowledge Source | Knowledge Job | Use in Pipeline Builder |
|---|---------|------------------|---------------|------------------------|
| 1 | Conditional Field Visibility | ✓ | ✓ | Yes |
| 2 | Modal Sub-wizards | ✓ | | Yes (node config) |
| 3 | Floating Test/Preview Panels | ✓ | | Yes (pipeline preview) |
| 4 | Auto-calculation & Smart Defaults | | ✓ | Yes |
| 5 | Intelligent Recommendations | | ✓ | Yes |
| 6 | Progressive Disclosure | ✓ | ✓ | Yes |
| 7 | Multi-step API Validation | | ✓ | Yes |
| 8 | Step-based Review & Confirmation | ✓ | ✓ | Yes |
| 9 | Breadcrumb Navigation | ✓ | ✓ | No |
| 10 | Edit Mode State Preservation | ✓ | ✓ | Yes |

---

## Color Scheme

### Standard Gradient Progression
```
Teal (#45c9bb)      → Initial/input stages
Green (#bbe773)     → First processing stages  
Yellow (#ddde65)    → Content/configuration stages
Dark Green (#3bc57d)→ Advanced processing stages
Purple (#ae89ae)    → Final/review stages
```

---

## Validation Strategy

### Knowledge Source Wizard
- **Step 0**: REQUIRED (name, scraping_mode, url based on mode)
- **Steps 1-3**: OPTIONAL (advanced configuration)
- **Step 4**: REVIEW ONLY

### Knowledge Job Wizard
- **Steps 0, 1, 2, 4**: REQUIRED (job setup, collection, splitter, processing)
- **Step 3**: CONDITIONAL (skipped if using existing collection)
- **Step 5**: REVIEW ONLY

### Special Validations
- URL format checking (http/https required)
- File size limits (10MB max)
- API uniqueness checks (collection names)
- Active provider status validation

---

## State Management Examples

### Knowledge Source Configuration
```typescript
{
  name: string,                           // Step 0
  description: string,                    // Step 0
  scraping_mode: 'single_page' | 'multiple_pages' | 'website',
  url: string,                            // Step 0
  url_source: { file_name: string, urls: string[] },
  crawl_depth: number,                    // Step 0
  
  allowed_subdomains: string[],           // Step 1
  blocked_subdomains: string[],           // Step 1
  url_patterns: Array<{pattern, reverse}>,
  
  target_elements: string[],              // Step 2
  
  output_format: 'html' | 'markdown',     // Step 3
  markdown_generation: 'standard' | 'llm',
  content_filter_threshold: number,
  llm_content_filter_id: string | null
}
```

### Knowledge Job Configuration
```typescript
{
  config_id: string,                      // Step 0
  name: string,                           // Step 0
  description: string,
  
  use_existing_collection: boolean,       // Step 1
  existing_collection_id: string,         // Step 1
  collection_name: string,
  vectordb_collection_description: string,
  
  splitter_type: 'text' | 'document',     // Step 2
  chunk_size: number,
  chunk_overlap: number,
  headers_to_split_on: Array<[string, string]>,
  
  embedding_model_provider_id: string,    // Step 3
  embedding_model_name: string,
  vector_dimension: number,
  
  batch_size: number,                     // Step 4
  save_to_file: boolean,
  write_consolidated_file: boolean,
  clear_collection_before_start: boolean,
  check_duplicates_before_insert: boolean
}
```

---

## Animation Timings

- Content card fade: 300ms
- Step indicator scale: 300ms
- Connecting line growth: 600ms
- Content slide-in: 400ms
- Active step pulse: 2s (repeating)
- Hover translation: instant (6px offset)

---

## Recommendations for Pipeline Builder

### 1. Use ColorfulVerticalStepper
- For multi-stage pipeline construction
- Each pipeline segment as a step
- Consistent with existing UI language

### 2. Modal Node Configuration
- Click node → opens modal (not new page)
- Quick edit with advanced options
- Async save without wizard progression

### 3. Real-time Validation
- Show connection validity immediately
- Color-code nodes (invalid/valid/active)
- Prevent invalid execution

### 4. Visual Consistency
- Use same color scheme
- Adopt pulsing animations for active nodes
- Show checkmarks for completed configs

### 5. Floating Preview Panel
- Test sample data through pipeline
- Real-time validation output
- Performance metrics display

### 6. Configuration Inheritance
- Child nodes inherit parent settings
- Show inherited as disabled fields
- Allow override with visual indicator

### 7. Save & Execute Flow
- Separate save and execute buttons
- Full review before execution
- Status monitoring after start

---

## Next Steps

1. **For Design**: Review visual diagrams in WIZARD_UX_QUICK_REFERENCE.md
2. **For Development**: Study implementation details in WIZARD_ANALYSIS.md
3. **For Pipeline Builder**: Follow recommendations in ANALYSIS_SUMMARY.txt

---

## Questions?

Refer to the appropriate section:
- **"How does the current wizard work?"** → WIZARD_ANALYSIS.md
- **"What are the UX patterns used?"** → WIZARD_ANALYSIS.md section 4
- **"Can I see the visual architecture?"** → WIZARD_UX_QUICK_REFERENCE.md
- **"What colors are used?"** → WIZARD_UX_QUICK_REFERENCE.md (Color Scheme Reference)
- **"How should I build the pipeline UI?"** → ANALYSIS_SUMMARY.txt (Recommendations)

---

**Created**: October 20, 2025  
**Analysis Scope**: Knowledge Source Configuration Wizard, Knowledge Job Wizard, ColorfulVerticalStepper Component  
**Total Documentation**: 46KB across 3 files
