# DataPilot Flow: Wizard Implementations Analysis

## Executive Summary

The application uses two primary wizard flows implemented with a **ColorfulVerticalStepper** component pattern:
1. **Knowledge Source Configuration Wizard** (5 steps) - for configuring data sources
2. **Knowledge Job Creation Wizard** (6 steps) - for creating processing jobs

Both wizards follow a step-by-step guided process with validation, state management, and clear visual feedback.

---

## 1. KNOWLEDGE SOURCE WIZARD IMPLEMENTATION

### File Locations
- **Create**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/knowledge-sources/config-create/index.tsx`
- **Edit**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/knowledge-sources/config-edit/index.tsx`
- **Stepper Component**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/components/colorful-vertical-stepper.tsx`

### Step-by-Step Flow

#### Step 0: Basic Info & Scraping Configuration
**Color**: Teal (#45c9bb)
**Icon**: IconSettings
**Description**: Name, description, URL

**Configuration Fields**:
- `name` - Configuration name (required, text input)
- `description` - Optional description (textarea)
- `scraping_mode` - Choice of: 'single_page', 'multiple_pages', 'website'
- `url` - Page/Website URL (conditional based on scraping_mode)
- `url_source` - File with multiple URLs (conditional, for 'multiple_pages' mode)
- `crawl_depth` - Number input (0-6, default: 4)

**Validation**:
- Name is required
- URL is required based on scraping mode
- URL format validation (must start with http:// or https://)
- File size max 10MB for URL lists
- Maximum 50,000 URLs per file

**UI Features**:
- Dynamic field visibility based on scraping_mode selection
- Drag-and-drop file upload with visual feedback
- Descriptive help text for each mode
- File preview showing loaded URL count

---

#### Step 1: Domain & URL Filtering
**Color**: Green (#bbe773)
**Icon**: IconFilter
**Description**: Allowed/blocked domains

**Configuration Fields**:
- `allowed_subdomains` - Array of subdomains to allow (optional)
- `blocked_subdomains` - Array of subdomains to block (optional)
- `url_patterns` - Array of patterns with structure:
  ```typescript
  {
    pattern: string;      // e.g., "*/jp/*"
    reverse: boolean;     // Exclude matching URLs
  }
  ```

**Validation**:
- Step is entirely optional
- No required fields

**UI Features**:
- Two-column layout for allowed/blocked domains
- Add/remove buttons for dynamic fields
- Pattern matching with wildcard support
- Toggle switch for include/exclude behavior
- Information alert with pattern examples

---

#### Step 2: Content Filter & Target Elements
**Color**: Yellow (#ddde65)
**Icon**: IconCode
**Description**: Target elements

**Configuration Fields**:
- `target_elements` - Array of CSS selectors (e.g., ['main', 'article', 'div.content'])
- Text-based selector input with validation

**Validation**:
- Step is optional
- Selectors must be valid CSS

**UI Features**:
- Three-column layout:
  1. Left: Add new selector input + current selectors list
  2. Right: Quick-start guide and instructions
  3. Floating panel: Real-time selector testing
- Quick reference: "How to Get Selectors" (browser dev tools steps)
- Auto-included 'header' selector for metadata
- "Test Selectors" button - floating test panel with HTML/Markdown output format toggle
- Live preview of extracted content

---

#### Step 3: Generation & Output Format
**Color**: Green (#3bc57d)
**Icon**: IconWand
**Description**: Output format

**Configuration Fields**:
- `output_format` - Choice of 'html' or 'markdown'
- `markdown_generation` - Choice of 'standard' or 'llm' (when output_format === 'markdown')
- `content_filter_threshold` - Number 0-1 (default 0.6, for standard markdown)
- `llm_content_filter_id` - Reference to LLM filter (for llm markdown)

**Conditional Fields (LLM Markdown)**:
- Can create new LLM filter via modal with:
  - `name` - Filter name (required)
  - `description` - Optional description
  - `llm_provider_id` - LLM provider selection (required)
  - `llm_model_name` - Model selection (required)
  - `instruction` - Custom filtering instructions (required, with templates)
  - `temperature` - Number 0-2 (default 0.0)
  - `max_retries` - Number 1-10 (default 3)
  - `timeout_seconds` - Number 10-300 (default 30)
  - `chunk_token_threshold` - Number (default 1000)

**Validation**:
- Step is optional
- LLM provider must be active

**UI Features**:
- Radio buttons for output format selection
- Conditional markdown generation method selector
- Cost notice alert for LLM processing
- Provider and model dropdowns (filtered for active providers)
- Template selector for filter instructions (Technical Docs, API Reference, Tutorials, Release Notes, Troubleshooting)
- "Create New Filter" button opens modal
- "Preview Content" floating test panel

---

#### Step 4: Review & Confirmation
**Color**: Purple (#ae89ae)
**Icon**: IconClipboardCheck
**Description**: Review and create

**Content Displayed**:
- Configuration name and scraping mode
- URL(s) information
- Domain/URL filtering settings (if configured)
- Target elements and selectors
- Content filter selection
- Output format configuration

**Validation**:
- Always valid (review-only step)

**UI Features**:
- Card-based display of all settings
- Color-coded badges for status
- Simple, scannable format
- Success message confirmation

---

### State Management

```typescript
const form = useForm({
  initialValues: {
    name: '',
    description: '',
    url: '',
    scraping_mode: 'website',
    url_source: { file_name: '', urls: [] },
    allowed_subdomains: [],
    blocked_subdomains: [],
    url_patterns: [],
    crawl_depth: 4,
    target_elements: [],
    content_filter_threshold: 0.6,
    llm_content_filter_id: null,
    output_format: 'html',
    markdown_generation: 'standard'
  }
});

const [activeStep, setActiveStep] = useState(0);
const [completedSteps, setCompletedSteps] = useState<number[]>([]);
const [hasReachedFinalStep, setHasReachedFinalStep] = useState(false);
```

### Navigation Logic

- **Next Button**: Validates current step → moves to next
- **Previous Button**: Always allowed
- **Step Click**: 
  - Can click back to previous steps
  - Can click to next step only if current validated
  - Cannot skip steps
- **Final Step**: Explicit submit flag prevents accidental submission

---

## 2. KNOWLEDGE JOB WIZARD IMPLEMENTATION

### File Location
- **Create/Edit**: `/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/pages/dashboard/management/knowledge-sources/job-create/index.tsx`

### Step-by-Step Flow

#### Step 0: Job Setup
**Color**: Teal (#45c9bb)
**Icon**: IconClock
**Description**: Basic job information

**Configuration Fields**:
- `config_id` - Knowledge source configuration selection (required)
- `name` - Job name (required)
- `description` - Job description (optional)

**Validation**:
- config_id is required
- name is required

**UI Features**:
- Dropdown select for available configurations
- Text input for job name
- Textarea for description
- Information alert explaining step purpose

---

#### Step 1: Vector DB Collection Configuration
**Color**: Green (#bbe773)
**Icon**: IconDatabase
**Description**: Configure vector database

**Configuration Fields**:
- `use_existing_collection` - Boolean toggle
- If creating new:
  - `collection_name` - Name for new collection (required, alphanumeric + underscores only)
  - `vectordb_collection_description` - Optional description
- If using existing:
  - `existing_collection_id` - Select from dropdown (required)
  - Inherited fields displayed as disabled:
    - Collection name, description
    - Embedding provider, model
    - Vector dimension

**Validation**:
- If using existing: existing_collection_id required
- If creating new: collection_name required
- Collection name uniqueness checked via API

**UI Features**:
- Radio buttons to toggle between create/existing
- Dynamic field visibility
- "View All" button to see all URLs in collection modal
- Inheritance section shows inherited settings when using existing
- Real-time collection name uniqueness check on next step

---

#### Step 2: Document Splitter Configuration
**Color**: Yellow (#ddde65)
**Icon**: IconScissors
**Description**: Choose splitting strategy

**Configuration Fields**:
- `splitter_type` - Choice of 'text' or 'document'
- For text-based:
  - `chunk_size` - Number 64-4096 (default 256)
  - `chunk_overlap` - Number 0-512 (auto-calculated as 12.5% of chunk size)
- For document-based:
  - `headers_to_split_on` - Array of [pattern, label] pairs
    - Default: [['#', 'Header 1'], ['##', 'Header 2'], ['###', 'Header 3']]

**Validation**:
- Text splitter: chunk_size 64-4096, overlap 0-50% of chunk_size
- Document splitter: always valid if selected

**UI Features**:
- Configuration-based recommendation (based on source output_format)
- Radio selection with descriptions
- "Apply Recommendation" button for recommended splitter
- Warning if non-recommended splitter selected
- Dynamic field display based on splitter type
- Auto-calculation notification for chunk overlap
- Add/remove header levels for document splitting
- Recommended tag badges

---

#### Step 3: Embedding Model Configuration
**Color**: Green (#3bc57d)
**Icon**: IconBrain
**Description**: Select embedding model

**Configuration Fields** (only if not using existing collection):
- `embedding_model_provider_id` - Provider dropdown (required, filtered for active)
- `embedding_model_name` - Model dropdown (required, populated based on provider)
- `vector_dimension` - Number 1-4096 (default 1536)

**Validation**:
- Provider required and must be active
- Model required
- Vector dimension: 1-4096
- If using existing collection: step skipped (auto-valid)

**UI Features**:
- Provider selector with active/inactive status
- Model selector (disabled until provider selected)
- Vector dimension input with examples
- Detailed explanation of vector dimensions and impact
- Inactive provider warning alert
- Information alert about dimension consistency requirement

---

#### Step 4: Processing Settings
**Color**: Purple (#ae89ae)
**Icon**: IconCpu
**Description**: Job processing settings

**Configuration Fields**:
- `batch_size` - Number 1-1000 (default 20)
- `save_to_file` - Boolean (default false)
- `write_consolidated_file` - Boolean, disabled unless save_to_file true (default false)
- `clear_collection_before_start` - Boolean (default false)
- `check_duplicates_before_insert` - Boolean (default false)

**Validation**:
- batch_size: 1-1000

**UI Features**:
- Number input for batch size with description
- Multiple switch toggles for boolean settings
- Divider sections for grouping
- Descriptions for each toggle option
- Conditional disabling of consolidate file option

---

#### Step 5: Review & Create/Update
**Color**: Teal (#45c9bb) to Green (#3bc57d)
**Icon**: IconClipboardCheck
**Description**: Review and create/update

**Content Displayed**:
- Job Overview: Configuration, Job Name
- Vector DB Collection: Type, Name, Provider, Model, Dimension
- Document Splitting: Splitter type, Chunk size/overlap (if text)
- Embedding Configuration (if not using existing collection)
- Processing Settings: Batch size, file options, collection options
- Configuration alignment alert showing if splitter matches recommendation

**Validation**:
- Always valid (review-only step)
- Configuration alignment shown with color indicator

**UI Features**:
- SimpleGrid layout for organized display
- Alignment alert showing match/mismatch with recommendations
- All settings displayed in read-only format
- Clear section headers
- Visual indicators for configuration status

---

### State Management

```typescript
const form = useForm({
  initialValues: {
    config_id: '',
    name: '',
    description: '',
    use_existing_collection: false,
    existing_collection_id: '',
    vectordb_collection_description: '',
    embedding_model_provider_id: '',
    embedding_model_name: '',
    vector_dimension: 1536,
    collection_name: '',
    splitter_type: 'text',
    chunk_size: 256,
    chunk_overlap: 32,
    headers_to_split_on: [['#', 'Header 1'], ['##', 'Header 2'], ['###', 'Header 3']],
    batch_size: 20,
    save_to_file: false,
    write_consolidated_file: false,
    clear_collection_before_start: false,
    check_duplicates_before_insert: false
  }
});

const [activeStep, setActiveStep] = useState(0);
const [completedSteps, setCompletedSteps] = useState<number[]>([]);
const [isExplicitSubmit, setIsExplicitSubmit] = useState(false);
```

### Navigation Logic
- Same as knowledge source wizard
- Additional: explicit submit flag on final step prevents accidental form submission
- Edit mode support: loads existing job data and pre-populates form

---

## 3. COLORFUL VERTICAL STEPPER COMPONENT

### File Location
`/Users/bassem.elsodany/workspaces/datapilotflow/dashboard/src/components/colorful-vertical-stepper.tsx`

### Architecture

**Props**:
```typescript
interface ColorfulVerticalStepperProps {
  activeStep: number;
  completedSteps: number[];
  steps: StepConfig[];
  children: ReactNode;
  onStepClick?: (step: number) => void;
}

interface StepConfig {
  label: string;
  description: string;
  icon: ReactNode;
  color: string;
  gradientFrom?: string;
  gradientTo?: string;
}
```

### Visual Design

**Layout**: Two-column
- Left sidebar (200px fixed width): Step tracker
- Right content area (flex): Current step content

**Step Indicator Features**:
- Circular icon with color gradient
- Step number badge (top-right)
- Checkmark for completed steps
- Pulse animation for active step
- Rotating ring animation for active step
- Connecting lines between steps with gradient
- Color-coded based on step status

**Step States**:
- **Completed**: Green gradient, checkmark icon, opacity 1
- **Active**: Pulsing animation, bright color, full opacity, shadow glow
- **Pending**: Gray gradient, opacity 0.7, step number badge
- **Disabled**: Gray, opacity reduced, no interaction

**Content Card**:
- Gradient background (white to light gray)
- Border with step-specific color
- Top accent bar with gradient
- Fade-in animation
- Shadow with step-color tint
- Minimum height 440px

### Animations & Effects

**CSS Animations**:
- `pulse`: Active step breathing effect (2s)
- `rotate`: Rotating ring for active step (3s)
- `fadeInUp`: Content card entrance (0.4s)
- `slideIn`: Step indicator slide (0.3s)
- `growLine`: Connecting line animation (0.6s)
- `checkmarkBounce`: Completed step checkmark (0.6s)
- `shimmer`: Shimmer effect on completed steps (3s)

**Hover Effects**:
- Clickable steps: Translate X by 6px
- Non-active steps: Glassmorphism backdrop blur effect
- Color transition on state change

**Responsive Design**:
- Mobile: Reduced animations, scaled transforms
- Tablet+: Full animations enabled

---

## 4. CURRENT UX PATTERNS

### Pattern 1: Conditional Field Visibility
**Used In**: Knowledge Source wizard (scraping mode)
**Pattern**: Show/hide input fields based on radio selection or parent field value
**Implementation**: Conditional rendering with field visibility tied to form state
**Example**: 
```jsx
{form.values.scraping_mode === 'single_page' && (
  <TextInput label="Page URL" {...form.getInputProps('url')} />
)}
```

### Pattern 2: Modal-based Sub-wizards
**Used In**: Both wizards for advanced configuration
**Pattern**: Modal dialogs for creating related entities without leaving wizard
**Implementation**: Mantine Modal with separate form
**Examples**:
- Create LLM Content Filter (Knowledge Source wizard)
- Multiple step validation before modal opens
- Async mutation in background
- Modal form submission without wizard progression

### Pattern 3: Floating Test/Preview Panels
**Used In**: Knowledge Source wizard steps 2-3
**Pattern**: Collapsible floating panel for real-time testing
**Implementation**: Position absolute with toggle expand/collapse
**Features**:
- Shows as small button when collapsed
- Expands to full panel with test controls
- Real-time preview of extraction results
- No page scroll when panel visible

### Pattern 4: Auto-calculation & Smart Defaults
**Used In**: Job wizard (chunk overlap calculation)
**Pattern**: Auto-calculate dependent fields based on user input
**Implementation**: onChange handler with formula
**Example**: Overlap = min(chunkSize * 0.125, chunkSize / 2)
**Notification**: Toast showing calculated value

### Pattern 5: Intelligent Recommendations
**Used In**: Job wizard (document splitter)
**Pattern**: Recommend options based on configuration context
**Implementation**: Calculate recommendation from related data
**Display**: Alert box with "Apply Recommendation" button
**UI States**: Badge showing "Recommended" tag, warning for non-recommended

### Pattern 6: Progressive Disclosure
**Used In**: All wizards
**Pattern**: Hide advanced fields until user toggles or enters basic mode
**Examples**:
- URL patterns only show after user indicates need
- LLM settings only visible when markdown format selected
- Headers configuration hidden until document splitter selected

### Pattern 7: Multi-step Validation
**Used In**: Job wizard (collection name uniqueness)
**Pattern**: Validate across API before step progression
**Implementation**: API call in nextStep() function before setActiveStep
**Feedback**: Toast notification if validation fails, prevents progression

### Pattern 8: Step-based Review & Confirmation
**Used In**: All wizards (final step)
**Pattern**: Final summary of all decisions before submission
**Implementation**: Read-only display of all form values
**Benefit**: Catch configuration errors before submission

### Pattern 9: Breadcrumb Navigation
**Used In**: All wizard pages
**Pattern**: Show navigation path through application
**Implementation**: PageHeader component with breadcrumbs array
**Purpose**: Quick context and navigation back to management areas

### Pattern 10: State Preservation on Edit
**Used In**: Job wizard edit mode
**Pattern**: Fetch existing data and populate form
**Implementation**: useEffect that loads data into form when job loads
**Consideration**: Some fields become immutable (config_id, collection changes)

---

## 5. CONFIGURATION FIELDS SUMMARY

### Knowledge Source Wizard - All Fields
```
Step 0 (Basic Info & Scraping):
  - name (string, required)
  - description (string, optional)
  - scraping_mode (enum: single_page|multiple_pages|website, required)
  - url (string, conditional required)
  - url_source.file_name (string, conditional)
  - url_source.urls (array, conditional)
  - crawl_depth (number: 0-6, default: 4)

Step 1 (Domain Filtering):
  - allowed_subdomains (array of strings, optional)
  - blocked_subdomains (array of strings, optional)
  - url_patterns (array of {pattern, reverse}, optional)

Step 2 (Content Filter):
  - target_elements (array of CSS selectors, optional)

Step 3 (Generation):
  - output_format (enum: html|markdown, default: html)
  - markdown_generation (enum: standard|llm, default: standard)
  - content_filter_threshold (number: 0-1, default: 0.6)
  - llm_content_filter_id (string|null, optional)
  - llm_content_filter.name (string, required for creation)
  - llm_content_filter.description (string, optional)
  - llm_content_filter.llm_provider_id (string, required)
  - llm_content_filter.llm_model_name (string, required)
  - llm_content_filter.instruction (string, required)
  - llm_content_filter.temperature (number: 0-2, default: 0.0)
  - llm_content_filter.max_retries (number: 1-10, default: 3)
  - llm_content_filter.timeout_seconds (number: 10-300, default: 30)
  - llm_content_filter.chunk_token_threshold (number, default: 1000)
```

### Knowledge Job Wizard - All Fields
```
Step 0 (Job Setup):
  - config_id (string, required)
  - name (string, required)
  - description (string, optional)

Step 1 (Vector DB Collection):
  - use_existing_collection (boolean, default: false)
  - existing_collection_id (string, conditional required)
  - collection_name (string, conditional required)
  - vectordb_collection_description (string, optional)

Step 2 (Document Splitter):
  - splitter_type (enum: text|document, default: text)
  - chunk_size (number: 64-4096, default: 256)
  - chunk_overlap (number: 0-512, default: 32, auto-calculated)
  - headers_to_split_on (array of [pattern, label], default: 3 levels)

Step 3 (Embedding Model):
  - embedding_model_provider_id (string, conditional required)
  - embedding_model_name (string, conditional required)
  - vector_dimension (number: 1-4096, default: 1536)

Step 4 (Processing):
  - batch_size (number: 1-1000, default: 20)
  - save_to_file (boolean, default: false)
  - write_consolidated_file (boolean, default: false)
  - clear_collection_before_start (boolean, default: false)
  - check_duplicates_before_insert (boolean, default: false)
```

---

## 6. RECOMMENDED PATTERNS FOR PIPELINE BUILDER UX

Based on the existing wizards, here are patterns to adopt for your pipeline builder:

### 1. Multi-step Workflow with Validation
- Use ColorfulVerticalStepper for pipeline construction
- Each pipeline stage as a step
- Validate connections before progression
- Show configuration complexity at each stage

### 2. Node Configuration Modal Pattern
- Clicking a node opens a modal (not a new page)
- Modal has simplified controls for quick edits
- Sub-configurations available via buttons
- Modal closes after save, returns to pipeline view

### 3. Real-time Validation & Feedback
- Show connection validity immediately
- Color-code pipeline nodes based on state (invalid/valid/active)
- Display validation errors as inline alerts
- Prevent invalid pipeline execution

### 4. Visual State Indicators
- Adopt the ColorfulVerticalStepper aesthetic
- Use consistent color scheme:
  - Teal: Input stages
  - Green: Processing stages
  - Orange: Transformation stages
  - Purple: Output stages
- Pulsing animations for active nodes
- Checkmarks for completed configurations

### 5. Drag-drop with Smart Feedback
- Visual feedback during drag over (highlight drop zones)
- Preview of connections before release
- Undo/Redo support for drag operations
- Keyboard shortcuts for power users

### 6. Configuration Inheritance Pattern
- Child nodes inherit parent configurations
- Show inherited values as disabled fields
- Allow override with visual indicator
- Clear dependency chain display

### 7. Testing & Preview Pattern
- "Test Stage" button opens preview panel (floating like Content Filter wizard)
- Show sample data through pipeline at each step
- Real-time validation output
- Performance metrics (processing time, data volume)

### 8. Save & Execute Flow
- Save button for configuration changes
- Separate "Run Pipeline" button for execution
- Show confirmation with full pipeline review
- Status monitoring after execution

---

## 7. IMPLEMENTATION NOTES

### Component Reusability
- ColorfulVerticalStepper is generic and reusable
- Step configuration easily customizable
- Can be adapted for any multi-step process

### State Management
- Use Mantine useForm for field management
- Additional hooks for step navigation (useState for activeStep, completedSteps)
- Explicit submit flag prevents accidental submissions
- Form validation on each step progression

### Performance Considerations
- Lazy load heavy components (modals, floating panels)
- Debounce API validation checks (collection name uniqueness)
- Use React.memo for non-dependent step contents
- Conditional rendering for optional steps

### Accessibility
- Semantic HTML in form fields
- ARIA labels for step indicators
- Keyboard navigation (Tab, Enter, Arrow keys)
- Focus management on step transitions
- Screen reader support for progress indication

### Error Handling
- User-friendly validation messages
- Specific error highlighting on problem fields
- Recovery options (edit previous steps)
- Retry mechanisms for API failures

