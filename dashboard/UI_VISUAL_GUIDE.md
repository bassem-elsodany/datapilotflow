# Job Wizard - Visual Guide

## 🎨 New UI Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Create Knowledge Injection Job                    [Back to Jobs]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────┐  ┌────────────────────────────────────┐  │
│  │                      │  │                                    │  │
│  │  VERTICAL TRACKER    │  │     LARGE CONTENT AREA            │  │
│  │  (280px width)       │  │     (Flexible width)              │  │
│  │                      │  │                                    │  │
│  │  ┌────────────────┐  │  │  ┌──────────────────────────────┐ │  │
│  │  │ [1] Job Setup  │◄─┼──┼──┤ Colored top bar (#45c9bb)   │ │  │
│  │  │ ✓ Completed    │  │  │  ├──────────────────────────────┤ │  │
│  │  │ #45c9bb        │  │  │  │                              │ │  │
│  │  └────────────────┘  │  │  │  📝 Step 1: Job Setup       │ │  │
│  │         │            │  │  │                              │ │  │
│  │         │ (gradient) │  │  │  [Configuration Field]      │ │  │
│  │         ▼            │  │  │  [Job Name Field]           │ │  │
│  │  ┌────────────────┐  │  │  │  [Description Field]        │ │  │
│  │  │ [2] Vector DB  │  │  │  │                              │ │  │
│  │  │ ● ACTIVE       │◄─┼──┼──┼─ Connected by color          │ │  │
│  │  │ #bbe773        │  │  │  │                              │ │  │
│  │  │ (PULSING!)     │  │  │  │  [More fields...]           │ │  │
│  │  └────────────────┘  │  │  │                              │ │  │
│  │         │            │  │  │                              │ │  │
│  │         │ (gray)     │  │  │                              │ │  │
│  │         ▼            │  │  │                              │ │  │
│  │  ┌────────────────┐  │  │  └──────────────────────────────┘ │  │
│  │  │ [3] Splitter   │  │  │                                    │  │
│  │  │ ○ Pending      │  │  │                                    │  │
│  │  │ #ddde65        │  │  │                                    │  │
│  │  └────────────────┘  │  │                                    │  │
│  │         │            │  │                                    │  │
│  │         ▼            │  │                                    │  │
│  │  ┌────────────────┐  │  │                                    │  │
│  │  │ [4] Embedding  │  │  │                                    │  │
│  │  │ ○ Pending      │  │  │                                    │  │
│  │  │ #3bc57d        │  │  │                                    │  │
│  │  └────────────────┘  │  │                                    │  │
│  │         │            │  │                                    │  │
│  │         ▼            │  │                                    │  │
│  │  ┌────────────────┐  │  │                                    │  │
│  │  │ [5] Processing │  │  │                                    │  │
│  │  │ ○ Pending      │  │  │                                    │  │
│  │  │ #ae89ae        │  │  │                                    │  │
│  │  └────────────────┘  │  │                                    │  │
│  │         │            │  │                                    │  │
│  │         ▼            │  │                                    │  │
│  │  ┌────────────────┐  │  │                                    │  │
│  │  │ [6] Review     │  │  │                                    │  │
│  │  │ ○ Pending      │  │  │                                    │  │
│  │  │ #45c9bb        │  │  │                                    │  │
│  │  └────────────────┘  │  │                                    │  │
│  │                      │  │                                    │  │
│  └──────────────────────┘  └────────────────────────────────────┘  │
│                                                                      │
│  [< Previous]                          [Cancel]  [Next >]           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Step Card States

### **1️⃣ COMPLETED STEP**
```
┌──────────────────────────────────────┐
│ ┃ ┌───────┐  Job Setup              │
│ ┃ │   ✓   │  Basic job information  │
│ ┃ └───────┘  ✓ Completed            │
└──────────────────────────────────────┘
  │
  └─ Active indicator bar (#45c9bb)

Style:
- Filled gradient icon with checkmark
- Colored border (subtle, 40% opacity)
- Tinted background (#45c9bb05)
- Soft shadow with color tint
- Checkmark bounces in
```

### **2️⃣ ACTIVE STEP**
```
┌──────────────────────────────────────┐
│ ┃ ┌───────┐  Vector DB Collection   │
│ ┃ │ 🗄️ [2]│  Configure vector db    │
│ ┃ └───────┘  ● ACTIVE                │
│ ┃   (PULSE)                          │
└──────────────────────────────────────┘
  │
  └─ Active indicator (#bbe773)

Style:
- Icon pulsing animation
- Thick colored border (#bbe773)
- Gradient background (teal → yellow)
- Elevated shadow (8px with color glow)
- Slides right 8px + scales 1.02x
- Step number badge on icon
```

### **3️⃣ PENDING STEP**
```
┌──────────────────────────────────────┐
│   ┌───────┐  Document Splitter      │
│   │ ✂️ [3]│  Choose splitting       │
│   └───────┘  ○ Pending              │
└──────────────────────────────────────┘

Style:
- Outline icon (gray border)
- Light gray border
- White background
- Minimal shadow
- 60% opacity
- Not clickable (unless completed)
```

---

## 🌈 Color Gradients

### **Connecting Lines Between Steps:**
```
Step 1 → Step 2: Linear gradient(#45c9bb → #bbe773)
Step 2 → Step 3: Linear gradient(#bbe773 → #ddde65)
Step 3 → Step 4: Linear gradient(#ddde65 → #3bc57d)
Step 4 → Step 5: Linear gradient(#3bc57d → #ae89ae)
Step 5 → Step 6: Linear gradient(#ae89ae → #45c9bb)

When completed: Full color gradient
When pending: Light gray (#e9ecef)
```

### **Step Card Backgrounds (Active):**
```
background: linear-gradient(135deg, {color}08 0%, {gradientTo}15 100%)

Example for Step 2:
  From: #bbe77308 (yellow-lime, 8% opacity)
  To:   #9dd24515 (lime, 15% opacity)
```

### **Icon Gradients (Completed):**
```
background: linear-gradient(135deg, {color} 0%, {gradientTo} 100%)

Example for Step 1:
  From: #45c9bb (teal)
  To:   #87cbbc (light teal)
```

---

## 💫 Animation Sequences

### **When Completing a Step:**
```
1. Icon scales from 0 → 1.2 → 1 (bounce)
2. Checkmark fades in
3. Background tints to step color
4. Border changes to colored
5. Connecting line below grows and changes color
6. Next step becomes active
7. Active indicator slides in on next step
8. Next step icon starts pulsing
```

### **When Clicking a Previous Step:**
```
1. Current step icon stops pulsing
2. Active indicator fades out
3. Content area fades out (300ms)
4. Active step changes
5. Clicked step slides right + scales up
6. Clicked step icon starts pulsing
7. Active indicator slides in
8. New content fades in (300ms)
```

### **Hover Effects:**
```
Clickable steps (completed or previous):
- Translate X: 0 → 4px
- Scale: 1 → 1.01
- Backdrop blur effect (glassmorphism)
- Cursor: pointer
- Transition: 300ms cubic-bezier
```

---

## 📐 Spacing & Sizing

```
Vertical Tracker (Sidebar):
- Width: 280px (fixed)
- Gap between steps: 16px (md)
- Step card padding: 16px (md)
- Step card border-radius: 8px (md)

Content Area:
- Flex: 1 (fills remaining space)
- Padding: 32px (xl)
- Border-radius: 12px (lg)
- Min height: 500px

Step Icons:
- Size: 48px × 48px
- Icon inside: 24px
- Border: 2px
- Border-radius: 8px (md)

Number Badges:
- Size: 22px × 22px
- Position: bottom-right of icon
- Font size: 11px
- Border: 2px solid white
- Border-radius: 50%

Connecting Lines:
- Width: 3px
- Height: 60px
- Position: Below icon, centered
- Animation: Grows from 0 to 60px
```

---

## 🎨 Typography

```
Step Labels (Active):
- Size: sm
- Weight: 700 (bold)
- Color: Step color

Step Labels (Completed):
- Size: sm
- Weight: 600 (semibold)
- Color: Dark gray (#343a40)

Step Labels (Pending):
- Size: sm
- Weight: 500 (medium)
- Color: Gray (#495057)

Step Descriptions:
- Size: xs
- Color: Dimmed
- Line height: 1.4
- Opacity: 0.8 (1.0 when active)

Number Badges:
- Size: 11px
- Weight: 700
- Color: White
```

---

## 🎬 Animation Timing

```css
/* Slide & Scale (Active Step) */
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

/* Color Changes */
transition: all 0.3s ease;

/* Content Fade */
transition: opacity 0.3s ease;

/* Pulse (Active Icon) */
animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;

/* Checkmark Bounce */
animation: checkmarkBounce 0.6s ease-out;

/* Line Growth */
animation: growLine 0.6s ease-out;

/* Content Entrance */
animation: fadeInUp 0.4s ease-out;
```

---

## 🌟 Visual Hierarchy

```
Priority 1 (Most Prominent):
- Active step card (colored, elevated, animated)
- Active step content area

Priority 2 (Secondary):
- Completed steps (checkmarks, colored icons)
- Step navigation buttons

Priority 3 (Tertiary):
- Pending steps (grayed out)
- Step descriptions
```

---

## 📱 Responsive Breakpoints

```css
Desktop (>768px):
- Full vertical layout
- Sidebar: 280px
- Animations: Full effects

Mobile (<768px):
- Optimized spacing
- Reduced transform effects
- Touch-friendly click targets
- No complex animations on low-end devices
```

---

## ✨ Special Effects

### **Glassmorphism (Hover):**
```css
backdrop-filter: blur(10px);
background: rgba(255, 255, 255, 0.9);
```

### **Colored Shadows (Active Step):**
```css
box-shadow:
  0 8px 24px {color}25,  /* Large soft glow */
  0 0 0 4px {color}10;    /* Small ring */
```

### **Gradient Top Bar (Content Card):**
```css
height: 4px;
background: linear-gradient(90deg, {color} 0%, {gradientTo} 100%);
border-radius: 12px 12px 0 0;
```

---

## 🎯 Accessibility Features

- ✅ High contrast colors
- ✅ Clear visual states
- ✅ Keyboard navigation support
- ✅ Descriptive labels
- ✅ Status indicators (✓, ●, ○)
- ✅ Color + icon + text (not just color)
- ✅ Reduced motion support (via CSS)

---

## 🎊 Final Result

**A modern, colorful, animated wizard that:**
- Looks professional and polished
- Matches the DataPilotFlow brand perfectly
- Provides excellent user feedback
- Is enjoyable to interact with
- Stands out from generic forms

**From boring horizontal stepper → Stunning vertical experience!** 🚀
