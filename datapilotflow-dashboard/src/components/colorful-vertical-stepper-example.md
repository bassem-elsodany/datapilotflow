# ColorfulVerticalStepper Component

## Overview
A modern, visually appealing vertical stepper component with colorful progress indicators, smooth animations, and glassmorphic design effects. Perfectly aligned with the DataPilotFlow brand colors.

## Features
- ✅ Vertical progress tracker with colored icons
- ✅ Gradient connecting lines between steps
- ✅ Smooth animations and transitions
- ✅ Glassmorphism effects
- ✅ Pulse animation for active step
- ✅ Checkmark animation for completed steps
- ✅ Clickable steps for navigation
- ✅ Color-coded steps matching brand
- ✅ Responsive design
- ✅ Customizable gradient colors

## Usage

```tsx
import { ColorfulVerticalStepper, StepConfig } from '@/components/colorful-vertical-stepper';
import { IconClock, IconDatabase, IconBrain } from '@tabler/icons-react';

function MyWizard() {
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  const steps: StepConfig[] = [
    {
      label: 'Setup',
      description: 'Basic information',
      icon: <IconClock size={24} />,
      color: '#45c9bb',
      gradientFrom: '#45c9bb',
      gradientTo: '#87cbbc'
    },
    {
      label: 'Configuration',
      description: 'Configure settings',
      icon: <IconDatabase size={24} />,
      color: '#bbe773',
      gradientFrom: '#bbe773',
      gradientTo: '#9dd245'
    },
    {
      label: 'Review',
      description: 'Review and submit',
      icon: <IconBrain size={24} />,
      color: '#3bc57d',
      gradientFrom: '#3bc57d',
      gradientTo: '#45c9bb'
    }
  ];

  const handleStepClick = (step: number) => {
    // Allow navigation to completed steps or previous steps
    if (step < activeStep || completedSteps.includes(step)) {
      setActiveStep(step);
    }
  };

  return (
    <ColorfulVerticalStepper
      activeStep={activeStep}
      completedSteps={completedSteps}
      steps={steps}
      onStepClick={handleStepClick}
    >
      {/* Content for current step */}
      {activeStep === 0 && <div>Step 1 Content</div>}
      {activeStep === 1 && <div>Step 2 Content</div>}
      {activeStep === 2 && <div>Step 3 Content</div>}
    </ColorfulVerticalStepper>
  );
}
```

## Props

### ColorfulVerticalStepper

| Prop | Type | Description |
|------|------|-------------|
| `activeStep` | `number` | The currently active step index (0-based) |
| `completedSteps` | `number[]` | Array of completed step indices |
| `steps` | `StepConfig[]` | Array of step configurations |
| `children` | `ReactNode` | Content to display for the current step |
| `onStepClick` | `(step: number) => void` | Optional callback when a step is clicked |

### StepConfig

| Prop | Type | Description |
|------|------|-------------|
| `label` | `string` | Step label text |
| `description` | `string` | Step description text |
| `icon` | `ReactNode` | Icon component to display |
| `color` | `string` | Primary color for the step (hex) |
| `gradientFrom` | `string` | Optional - Start color for gradients |
| `gradientTo` | `string` | Optional - End color for gradients |

## DataPilotFlow Brand Colors

Use these colors for a consistent brand experience:

```tsx
const brandColors = {
  tealCyan: '#45c9bb',
  tealCyanLight: '#87cbbc',
  yellowLime: '#bbe773',
  lime: '#9dd245',
  yellow: '#ddde65',
  green: '#3bc57d',
  purple: '#ae89ae',
  gray: '#8d949d'
};
```

## Animations

The component includes several built-in animations:
- **Pulse Effect**: Active step icon pulses gently
- **Slide-in**: Active indicator bar slides in from the left
- **Grow Line**: Connecting lines grow when a step is completed
- **Fade In Up**: Content area fades in with upward motion
- **Checkmark Bounce**: Completed checkmarks bounce into view
- **Hover Lift**: Step cards lift slightly on hover

## Styling

The component uses CSS modules for styling. You can customize the appearance by modifying:
- `colorful-vertical-stepper.module.css` - Component-specific styles and animations
- Step colors and gradients via the `StepConfig` props

## Best Practices

1. **Step Order**: Use 0-based indexing for steps
2. **Colors**: Use complementary colors from the brand palette
3. **Icons**: Use 24px icons for consistency
4. **Gradients**: Provide both `gradientFrom` and `gradientTo` for smooth transitions
5. **Completion**: Mark steps as completed when validation passes
6. **Navigation**: Allow users to go back to previous steps for editing

## Example: Job Wizard

See the full implementation in:
```
/src/pages/dashboard/management/knowledge-sources/job-create/index.tsx
```

This shows a complete 6-step wizard with form validation, data persistence, and step navigation.
