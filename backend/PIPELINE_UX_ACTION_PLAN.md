# Pipeline Builder UX - Action Plan & Quick Start

## 🎯 TL;DR - The New Experience

**Before**: Click node → See 20+ fields → Get overwhelmed → Quit

**After**: Click node → Beautiful 3-5 step wizard in modal → Each step has 2-4 fields → Feel guided and confident → Complete with joy!

---

## 📸 Visual Mockup - The Modal Wizard

```
CANVAS VIEW (Main Page):
┌──────────────────────────────────────────────────────────────────┐
│  Pipeline: Documentation Ingestion        [Save] [▶ Run Pipeline]│
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────┐     ┌──────────────────┐                 │
│   │  📄 Website     │────→│  ✂️  Splitter    │                 │
│   │  ✓ Configured   │     │  ⚠️  Review      │                 │
│   │  docs.ex...com  │     │  512 chunks      │                 │
│   │  [Edit]         │     │  [Configure]     │                 │
│   └─────────────────┘     └──────────────────┘                 │
│                                                                  │
│                           ┌──────────────────┐                 │
│                      ────→│  🎯 Embedding    │                 │
│                           │  ○ Not set       │                 │
│                           │  [Configure]     │                 │
│                           └──────────────────┘                 │
│                                                                  │
│  Pipeline Status: ████████░░ 2/3 configured (67%)              │
└──────────────────────────────────────────────────────────────────┘

CLICK [Configure] on Website Node → MODAL OPENS:

┌──────────────────────────────────────────────────────────────────┐
│  Configure: Website Source                               [×]     │
├──────────────────────────────────────────────────────────────────┤
│  ┌──────────────┬───────────────────────────────────────────────┐│
│  │              │                                               ││
│  │  ● Basic     │  STEP 1: BASIC INFORMATION                   ││
│  │  │           │                                               ││
│  │  │           │  Node Name *                                  ││
│  │  ○ Filter    │  ┌─────────────────────────────────────────┐ ││
│  │  │           │  │ Company Documentation                   │ ││
│  │  │           │  └─────────────────────────────────────────┘ ││
│  │  ○ Content   │                                               ││
│  │  │           │  Website URL *                                ││
│  │  │           │  ┌─────────────────────────────────────────┐ ││
│  │  ○ Output    │  │ https://docs.company.com                │ ││
│  │  │           │  └─────────────────────────────────────────┘ ││
│  │  ○ Review    │                                               ││
│  │              │  Crawl Depth                                  ││
│  │              │  ├───●─────┤ 4 levels                        ││
│  │              │  0  2  4  6  8                                ││
│  │              │                                               ││
│  │              │  💡 Recommended: 2-4 for documentation        ││
│  │              │                                               ││
│  │              │  [Cancel]            [Next: Filtering →]     ││
│  │              │                                               ││
│  └──────────────┴───────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔥 Top 3 Most Important Changes

### 1. **Modal-Based Configuration (Not Full Page)**
```
❌ BEFORE: Click node → Navigate to new page → Lose context
✅ AFTER:  Click node → Modal pops up → Stay on canvas → Configure → Close
```

### 2. **Step-by-Step Wizard (Not One Big Form)**
```
❌ BEFORE: 20+ fields on one screen → Overwhelming
✅ AFTER:  5 steps, 2-4 fields each → Manageable and guided
```

### 3. **Visual Node Status (Not Just Text)**
```
❌ BEFORE: Hard to tell if node is configured
✅ AFTER:  Color-coded nodes with icons:
           Gray + ○ = Not configured
           Green + ✓ = Configured
           Blue + ⚙️ = Running
           Red + ❌ = Error
```

---

## 🚀 Implementation Priority

### MUST HAVE (Launch Blocker) - Week 1

**1. Core Modal Component**
- [ ] Create `NodeConfigModal.tsx`
- [ ] Integrate `ColorfulVerticalStepper` (already exists!)
- [ ] Add modal open/close animations

**2. Website Source Node Wizard (5 steps)**
- [ ] Step 0: Basic Info (name, URL, crawl depth)
- [ ] Step 1: Domain Filtering (optional, can skip)
- [ ] Step 2: Content Filter (optional, can skip)
- [ ] Step 3: Output Format (optional, can skip)
- [ ] Step 4: Review & Save

**3. Enhanced Node Cards**
- [ ] Show configuration status (gray/green)
- [ ] Show config preview ("docs.example.com, depth: 4")
- [ ] [Configure] button opens modal

### SHOULD HAVE (Important) - Week 2

**4. Text Splitter Node Wizard (3 steps)**
- [ ] Step 0: Type selection
- [ ] Step 1: Chunk settings
- [ ] Step 2: Review

**5. Embedding Generator Node Wizard (3 steps)**
- [ ] Step 0: Provider selection
- [ ] Step 1: Model selection
- [ ] Step 2: Processing settings

**6. Vector Database Node Wizard (2 steps)**
- [ ] Step 0: Collection setup
- [ ] Step 1: Advanced options

**7. Pipeline Progress Indicator**
- [ ] Show "X/Y nodes configured (Z%)"
- [ ] Visual progress bar

### NICE TO HAVE (Polish) - Week 3

**8. Smart Connection Validation**
- [ ] Green line for valid connections
- [ ] Red line with error for invalid
- [ ] Real-time validation messages

**9. Quick Actions**
- [ ] Right-click menu on nodes
- [ ] Duplicate node functionality
- [ ] Quick edit vs full configure

**10. Pipeline Templates**
- [ ] Pre-built templates
- [ ] Save custom templates
- [ ] Template marketplace UI

---

## 📁 Files to Create/Modify

### New Files to Create

```
dashboard/src/pages/dashboard/management/pipeline-builder/
├── components/
│   ├── NodeConfigModal.tsx                    ← NEW: Main modal wrapper
│   ├── node-configs/
│   │   ├── WebsiteSourceConfig.tsx           ← NEW: Website node steps
│   │   ├── TextSplitterConfig.tsx            ← NEW: Splitter node steps
│   │   ├── EmbeddingGeneratorConfig.tsx      ← NEW: Embedding node steps
│   │   ├── VectorDatabaseConfig.tsx          ← NEW: VectorDB node steps
│   │   └── FileExportConfig.tsx              ← NEW: Export node steps
│   ├── NodeCard.tsx                          ← NEW: Enhanced node display
│   └── PipelineProgressBar.tsx               ← NEW: Progress indicator
```

### Files to Modify

```
dashboard/src/pages/dashboard/management/pipeline-builder/
├── index.tsx                                  ← UPDATE: Add modal state
├── components/
│   ├── Canvas.tsx                            ← UPDATE: Use new NodeCard
│   └── NodeEditor.tsx                        ← UPDATE: Use modal instead
```

### Files to Reuse (Already Exist!)

```
dashboard/src/components/
└── colorful-vertical-stepper.tsx             ← REUSE: Already perfect!
    └── colorful-vertical-stepper.module.css  ← REUSE: Already styled!
```

---

## 🔧 Code Structure Example

### NodeConfigModal.tsx (New File)

```typescript
import { Modal } from '@mantine/core';
import { ColorfulVerticalStepper } from '@/components/colorful-vertical-stepper';
import { PipelineNode } from '@/api/resources/pipelines';

// Import node-specific configurations
import { WebsiteSourceConfig } from './node-configs/WebsiteSourceConfig';
import { TextSplitterConfig } from './node-configs/TextSplitterConfig';
// ... other node configs

interface NodeConfigModalProps {
  node: PipelineNode | null;
  opened: boolean;
  onClose: () => void;
  onSave: (nodeId: string, config: any) => void;
}

export function NodeConfigModal({ node, opened, onClose, onSave }: NodeConfigModalProps) {
  if (!node) return null;

  // Render appropriate configuration based on node type
  const renderNodeConfig = () => {
    switch (node.type) {
      case 'website':
        return <WebsiteSourceConfig node={node} onSave={onSave} onClose={onClose} />;
      case 'textSplitter':
        return <TextSplitterConfig node={node} onSave={onSave} onClose={onClose} />;
      case 'embeddingGenerator':
        return <EmbeddingGeneratorConfig node={node} onSave={onSave} onClose={onClose} />;
      case 'vectorDatabase':
        return <VectorDatabaseConfig node={node} onSave={onSave} onClose={onClose} />;
      default:
        return <div>Configuration not available for this node type</div>;
    }
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      size="xl"
      title={`Configure: ${node.name}`}
      padding="lg"
    >
      {renderNodeConfig()}
    </Modal>
  );
}
```

### WebsiteSourceConfig.tsx (New File)

```typescript
import { useState } from 'react';
import { useForm } from '@mantine/form';
import { ColorfulVerticalStepper } from '@/components/colorful-vertical-stepper';
import { TextInput, Slider, Button, Group, Stack } from '@mantine/core';

interface WebsiteSourceConfigProps {
  node: PipelineNode;
  onSave: (nodeId: string, config: any) => void;
  onClose: () => void;
}

export function WebsiteSourceConfig({ node, onSave, onClose }: WebsiteSourceConfigProps) {
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  const form = useForm({
    initialValues: {
      name: node.name || '',
      url: node.config?.url || '',
      crawl_depth: node.config?.crawl_depth || 4,
      // ... other fields
    },
    validate: {
      name: (value) => (value ? null : 'Name is required'),
      url: (value) => {
        if (activeStep === 0 && !value) return 'URL is required';
        if (value && !value.startsWith('http')) return 'Invalid URL';
        return null;
      },
    },
  });

  const steps = [
    {
      label: 'Basic Info',
      description: 'Name and URL',
      icon: '📄',
      color: '#45c9bb',
    },
    {
      label: 'Filtering',
      description: 'Domain rules',
      icon: '🔍',
      color: '#bbe773',
    },
    {
      label: 'Content',
      description: 'Target elements',
      icon: '📋',
      color: '#ddde65',
    },
    {
      label: 'Output',
      description: 'Format options',
      icon: '⚙️',
      color: '#3bc57d',
    },
    {
      label: 'Review',
      description: 'Confirm settings',
      icon: '✓',
      color: '#ae89ae',
    },
  ];

  const handleNext = () => {
    const errors = form.validate();
    if (errors.hasErrors) return;

    setCompletedSteps([...completedSteps, activeStep]);
    setActiveStep(activeStep + 1);
  };

  const handleSave = () => {
    onSave(node.id, form.values);
    onClose();
  };

  return (
    <ColorfulVerticalStepper
      activeStep={activeStep}
      completedSteps={completedSteps}
      steps={steps}
      onStepClick={(step) => setActiveStep(step)}
    >
      <Stack gap="md" p="md">
        {activeStep === 0 && (
          <>
            <TextInput
              label="Node Name"
              placeholder="Company Documentation"
              required
              {...form.getInputProps('name')}
            />
            <TextInput
              label="Website URL"
              placeholder="https://docs.company.com"
              required
              {...form.getInputProps('url')}
            />
            <div>
              <label>Crawl Depth</label>
              <Slider
                min={0}
                max={10}
                step={1}
                marks={[
                  { value: 0, label: '0' },
                  { value: 2, label: '2' },
                  { value: 4, label: '4' },
                  { value: 6, label: '6' },
                  { value: 8, label: '8' },
                  { value: 10, label: '10' },
                ]}
                {...form.getInputProps('crawl_depth')}
              />
            </div>
            <Group justify="flex-end" mt="md">
              <Button variant="default" onClick={onClose}>Cancel</Button>
              <Button onClick={handleNext}>Next: Filtering →</Button>
            </Group>
          </>
        )}

        {activeStep === 1 && (
          <>
            {/* Domain filtering fields */}
            <Group justify="flex-end" mt="md">
              <Button variant="default" onClick={() => setActiveStep(0)}>← Previous</Button>
              <Button variant="subtle" onClick={() => setActiveStep(2)}>Skip</Button>
              <Button onClick={handleNext}>Next: Content →</Button>
            </Group>
          </>
        )}

        {/* ... other steps ... */}

        {activeStep === 4 && (
          <>
            {/* Review summary */}
            <Group justify="flex-end" mt="md">
              <Button variant="default" onClick={() => setActiveStep(3)}>← Edit</Button>
              <Button onClick={handleSave}>✓ Save & Close</Button>
            </Group>
          </>
        )}
      </Stack>
    </ColorfulVerticalStepper>
  );
}
```

---

## ⚡ Quick Win #1: Start with ONE Node

**Don't build all nodes at once!**

Start with just the **Website Source Node** wizard and get it perfect:

1. Build `NodeConfigModal.tsx` (wrapper)
2. Build `WebsiteSourceConfig.tsx` (5 steps)
3. Update `index.tsx` to open modal on node click
4. Test, polish, get feedback
5. Then move to next node

**Why?** You'll learn what works, what doesn't, and iterate faster.

---

## 🎨 Visual Guidelines (Quick Reference)

### Colors
```
Teal:      #45c9bb  → Initial/Input steps
Green:     #bbe773  → Filtering/Processing steps
Yellow:    #ddde65  → Content/Selection steps
DarkGreen: #3bc57d  → Advanced/Output steps
Purple:    #ae89ae  → Review/Final steps
```

### Status Colors
```
Gray:   #e0e0e0  → Not configured
Green:  #3bc57d  → Configured
Blue:   #45c9bb  → Running
Red:    #ff6b6b  → Error
Yellow: #ffc107  → Warning
```

### Icons
```
📄 Website, 📝 Single Page, 📚 Multiple Pages
✂️  Splitter, 🎯 Embedding, 💾 Vector DB
📊 Analytics, 📤 Export, 📧 Notification
```

---

## 🧪 Testing Checklist

### Per Node Type
- [ ] Modal opens smoothly (no lag)
- [ ] All steps are reachable
- [ ] Validation works on each step
- [ ] Can go back and edit previous steps
- [ ] Can skip optional steps
- [ ] Review shows all configured values
- [ ] Save updates the node on canvas
- [ ] Node card shows correct status after save

### Integration
- [ ] Save pipeline with configured nodes
- [ ] Load pipeline and edit node configuration
- [ ] Run pipeline with all nodes configured
- [ ] Handle node with partial configuration (save draft)

---

## 📊 Success Metrics

After implementing this:

**User Metrics:**
- ⏱️ Configuration time: 10min → 3min (70% reduction)
- ✅ Completion rate: 40% → 90% (125% increase)
- 😊 User satisfaction: "Confusing" → "Easy & Fun"

**Technical Metrics:**
- 🎯 Code reuse: 90% from existing wizard components
- 🚀 Performance: Modal opens in <100ms
- 🐛 Error rate: 80% reduction in invalid configs

---

## 🤝 Next Steps

1. **Review this proposal** with your team
2. **Choose starting node** (recommend: Website Source)
3. **Set up dev environment**
4. **Build NodeConfigModal wrapper** (Day 1)
5. **Build Website Source wizard** (Day 2-3)
6. **Test and iterate** (Day 4)
7. **Add next node type** (Day 5+)

---

## 📞 Support & Questions

As you implement:

**Questions to ask yourself:**
- Is this step necessary or can we combine it?
- Can we provide smarter defaults?
- What would confuse a first-time user?
- How can we add more visual feedback?

**Remember:**
- Start small (one node)
- Iterate quickly (get feedback daily)
- Keep it simple (fewer fields = better)
- Make it beautiful (animations matter!)

---

**Let's make your pipeline builder the highlight of your product!** 🎉

Ready to start? Let's build the first node configuration modal! 🚀
