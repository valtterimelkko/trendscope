# MVP UX Design Quick Reference

Condensed checklists and tables for rapid lookup during design.

---

## Four Screen States Checklist

For every major screen, document:

- [ ] **Ideal State**: Fully populated with realistic data
- [ ] **Empty State**: First-time user view with CTA and guidance
- [ ] **Loading State**: Skeleton screens showing content structure
- [ ] **Error State**: Human-readable message with recovery action

---

## Button States (6 Required)

| State | Visual | Cursor |
|-------|--------|--------|
| Default | Brand color | default |
| Hover | Darken 10% | pointer |
| Focus | Default + 3px ring | - |
| Pressed | Darken 20% or scale 98% | pointer |
| Disabled | Gray tones (verify 3:1 contrast) | not-allowed |
| Loading | Spinner replaces label | wait |

### Button Hierarchy

| Type | Usage | Example |
|------|-------|---------|
| Primary | Main action (1 per screen) | "Create Project" |
| Secondary | Alternative actions | "Cancel", "Save Draft" |
| Destructive | High-risk actions | "Delete Account" (Red) |
| Tertiary/Link | Subtle actions | "Read more" |

---

## Form Field Anatomy

```
┌─ Label (top-aligned, persistent) ─────────────────┐
│  [Input Field with placeholder hint]              │
│  Helper text: Format guidance                     │
│  Error text: Validation message (red + icon)      │
└───────────────────────────────────────────────────┘
```

### Validation Timing

| When | Use For |
|------|---------|
| On Blur | Complex fields (email, phone) |
| On Typing | Password strength, character limits |
| On Submit | Fallback validation, form-level errors |

---

## WCAG 2.1 AA Checklist

| Requirement | Minimum | Check |
|-------------|---------|-------|
| Text contrast | 4.5:1 | [ ] |
| Large text contrast | 3:1 | [ ] |
| Touch targets | 44x44px | [ ] |
| Focus visible | Yes | [ ] |
| Form labels | Persistent | [ ] |
| Error identification | Icon + text | [ ] |
| Heading hierarchy | Logical | [ ] |
| Keyboard navigable | All interactive | [ ] |

---

## User Flow Symbols

| Symbol | Meaning |
|--------|---------|
| ⬭ Oval | Start/End point |
| ◇ Diamond | Decision (Yes/No or multi-choice) |
| □ Rectangle | Screen/State/Process |
| ▱ Parallelogram | Data input/output |

---

## Validation Metrics

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Task Success Rate | >80% | <70% = redesign |
| SUS Score | >70 | <68 = below average |
| Time on Task | Varies | Significantly slower than expected |
| Error Rate | <20% | High = design flaw |

---

## Navigation Patterns

### B2B SaaS Standard: Vertical Sidebar

```
┌──────────────────────────────────────┐
│ Logo            🔔 👤                │
├─────────┬────────────────────────────┤
│ Dashboard│                           │
│ Projects │    Main Content Area      │
│ Reports  │                           │
│ Team     │                           │
│ Settings │                           │
└─────────┴────────────────────────────┘
```

**Behavior:**
- Collapsible to icons only
- Responsive: hamburger menu on mobile
- Max 2 levels deep

---

## Responsive Breakpoints (Suggested)

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Desktop | ≥1024px | Full sidebar, multi-column |
| Tablet | 768-1023px | Collapsed sidebar, fewer columns |
| Mobile | <768px | Hamburger menu, single column |

---

## Empty State Template

```
┌─────────────────────────────────────────┐
│                                         │
│           [Illustration]                │
│                                         │
│     "No [items] yet"                    │
│                                         │
│  [Explain what will appear here]        │
│                                         │
│     [ + Create First [Item] ]           │
│                                         │
└─────────────────────────────────────────┘
```

---

## Error Message Template

**Structure:** What happened + Why + How to fix

**Bad:** "Error 500"
**Good:** "We couldn't save your changes. Check your connection and try again."

**Inline error format:**
```
⚠️ [Clear description of what's wrong]
   [Specific fix instruction]
```

---

## Loading State: Skeleton Screens

Prefer skeleton screens over spinners:
- Gray pulsing shapes mimicking content layout
- Shows structural preview
- Reduces perceived wait time

```
┌─────────────────────────────────────────┐
│ ██████████████                          │
│ ████████████████████████████            │
│ █████████████████████                   │
│                                         │
│ ┌───────┐ ┌───────┐ ┌───────┐          │
│ │  ░░░  │ │  ░░░  │ │  ░░░  │          │
│ └───────┘ └───────┘ └───────┘          │
└─────────────────────────────────────────┘
```

---

## PRD Sections for UX

| Section | Content |
|---------|---------|
| Problem Statement | User pain in 1-2 sentences |
| Personas | 2-3 archetypes with tech proficiency |
| Success Metrics | Quantifiable (Time to Value, conversion) |
| Must Have | MVP-critical features |
| Should Have | Important but deferrable |
| Could Have | Nice-to-have |
| Won't Have | Explicitly out of scope |
| Use Cases | Narrative user tasks |

---

## Design Fidelity Guide

| Phase | Fidelity | Tools | Purpose |
|-------|----------|-------|---------|
| Discovery | Sketch/notes | Paper, whiteboard | Capture ideas |
| Exploration | Low | Balsamiq, Figma lo-fi | Validate structure |
| Refinement | Medium | Figma with UI kit | User testing |
| Handoff | High (critical screens) | Figma Dev Mode | Developer spec |

---

## Annotation Badge System

Place numbered badges on mockup, list explanations separately:

```
Design:                    Annotations:
┌────────────────┐         1. Primary CTA - only one per screen
│   ① [Button]   │         2. Opens modal on click
│   ②──┘         │         3. Shows tooltip on hover
│   ③────────┐   │         4. Requires Admin role to see
└────────────────┘
```

Categories to annotate:
- **Logic:** Conditional display rules
- **Interaction:** Hover, click, focus behavior
- **Validation:** Input requirements
- **Truncation:** Text overflow handling
- **Loading:** API-dependent content

---

## Full UX Document Template

Filename: `docs/mvp-ux-[product-name].md`

```markdown
# [Product Name] MVP User Experience

> **Status**: Draft | In Review | Final
> **Last Updated**: [Date]
> **Designer**: [Name]

## 1. Overview

### Problem Statement
[1-2 sentences describing the user pain point this MVP solves]

### Target Personas

**Persona 1: [Name/Role]**
- Tech Proficiency: Low | Medium | High
- Primary Goal: [What they want to accomplish]
- Pain Points: [Current frustrations]
- Context: [Where/when they'll use this]

**Persona 2: [Name/Role]**
- [Same structure as above]

### Success Metrics
- [Metric 1]: [Target value, e.g., "Task completion < 2 min"]
- [Metric 2]: [Target value, e.g., "Success rate > 80%"]
- Time to Value: [X minutes to first successful outcome]
- [Business metric]: [e.g., "Conversion rate > 15%"]

### Scope (MoSCoW)

**Must Have** (MVP-critical):
- [Feature 1]
- [Feature 2]

**Should Have** (Important but deferrable):
- [Feature 3]
- [Feature 4]

**Could Have** (Nice-to-have):
- [Feature 5]

**Won't Have** (Explicitly out of scope):
- [Feature 6 - explain why excluded]
- [Feature 7 - explain why excluded]

---

## 2. User Flows

### Flow 1: [Primary Flow Name, e.g., "New User Onboarding"]

```
[Start: Landing Page]
    ↓
[Sign Up Form]
    ↓
<Email Valid?> ─No→ [Show validation error] → [Sign Up Form]
    ↓ Yes
[Email Verification Sent]
    ↓
<User clicks link?> ─No→ [Send reminder after 24h]
    ↓ Yes
[Account Setup Wizard]
    ↓
[Dashboard - Empty State]
    ↓
[End]
```

**Edge Cases**:
- User email already exists → Show "Already registered, log in instead"
- Email service fails → Show error + retry option
- User abandons mid-flow → Save progress, send reminder email

**Success Criteria**: >80% complete flow within 5 minutes

---

### Flow 2: [Secondary Flow Name]
[Repeat structure above]

---

## 3. Screen Specifications

### Screen 1: [Screen Name, e.g., "Dashboard"]

#### Wireframe/Mockup
[Insert Figma link or ASCII wireframe]

```
┌─────────────────────────────────────────┐
│ Logo              🔔 Profile ▼          │
├────────┬────────────────────────────────┤
│ Nav 1  │  Main Content Area             │
│ Nav 2  │  ┌──────────────────────┐      │
│ Nav 3  │  │  Card 1              │      │
│        │  └──────────────────────┘      │
│        │  [+ Add New]                   │
└────────┴────────────────────────────────┘
```

#### States

**Ideal State** (Fully Populated):
- Header: Logo, notification bell (3 unread), profile dropdown
- Sidebar: 5 navigation items, current page highlighted
- Main area: 8 project cards showing name, status, last updated
- Primary CTA: "+ New Project" button (top right)

**Empty State** (First-Time User):
```
┌─────────────────────────────────────────┐
│          [Folder Illustration]          │
│                                         │
│         "No projects yet"               │
│                                         │
│  Create your first project to start    │
│  tracking tasks and collaborating      │
│                                         │
│     [+ Create First Project]            │
│                                         │
└─────────────────────────────────────────┘
```

**Loading State**:
- Skeleton screens: 3 pulsing gray card shapes
- Preserves layout structure
- Sidebar fully rendered, only main content shows skeleton

**Error State**:
```
⚠️  We couldn't load your projects

Check your internet connection and try again.
If the problem persists, contact support.

[Retry]  [Go Offline Mode]
```

#### Behavioral Annotations

1. **Project Card Hover**: Shows "⋮" menu icon (Edit/Archive/Delete)
2. **Notification Bell**: Red dot if unread, shows dropdown with last 5 items
3. **Profile Dropdown**: Avatar + name, links to Settings/Logout
4. **Search Bar**: Auto-complete after 2 characters typed
5. **Delete Action**: Requires confirmation modal with project name verification

#### Accessibility Notes
- Heading hierarchy: H1 (Dashboard) → H2 (Section titles) → H3 (Card titles)
- Keyboard navigation: Tab order follows visual flow (L→R, top→bottom)
- Focus indicators: 3px blue ring on all interactive elements
- Color contrast: All text meets 4.5:1 minimum (body), 3:1 (large headings)
- Screen reader: Cards announced as "Project: [Name], Status: [Active], Last updated: [Date]"
- ARIA labels: Notification bell has `aria-label="Notifications, 3 unread"`

---

### Screen 2: [Next Screen Name]
[Repeat structure above]

---

## 4. Component Specifications

### Buttons

| State | Visual | Text Color | Cursor | Use Case |
|-------|--------|------------|--------|----------|
| Default | bg-blue-600 | white | default | Rest state |
| Hover | bg-blue-700 | white | pointer | Mouse over |
| Focus | bg-blue-600 + 3px ring | white | - | Keyboard nav |
| Active/Pressed | bg-blue-800, scale(0.98) | white | pointer | Click moment |
| Disabled | bg-gray-300 | gray-500 | not-allowed | Cannot click |
| Loading | bg-blue-600 + spinner | - | wait | Processing |

**Button Hierarchy**:
- **Primary**: Main action (1 per screen max) - Blue filled
- **Secondary**: Alternative actions - White with blue border
- **Destructive**: High-risk actions - Red filled
- **Tertiary/Link**: Low-emphasis - Text only, underline on hover

### Form Fields

**Anatomy**:
```
Label (persistent, above field)
┌─────────────────────────────────────┐
│ [Input field with placeholder]      │
└─────────────────────────────────────┘
Helper text: Format guidance
⚠️ Error text: Validation message (only if error)
```

**States**:
- Default: Gray border (1px)
- Focus: Blue border (2px) + focus ring
- Filled: Default state with value
- Error: Red border + error icon + message below
- Disabled: Gray background, not-allowed cursor

**Validation Timing**:
- Email/Phone: On blur (after user leaves field)
- Password strength: On typing (real-time feedback)
- Form-level errors: On submit attempt

### Navigation Sidebar

- Width: 240px expanded, 64px collapsed (icon-only)
- Collapse toggle: Hamburger icon (top)
- Active item: Blue left border (4px) + blue background (light)
- Hover: Gray background
- Mobile: Full overlay with backdrop, close on item click

---

## 5. Validation Results

### Test Summary
- **Participants**: 5 users (3 matching Persona 1, 2 matching Persona 2)
- **Method**: Moderated remote testing (Zoom)
- **Date**: [Test date range]
- **Tasks Tested**: [List 3-5 key tasks]

### Findings

| Task | Success Rate | Avg Time | Issues Found |
|------|--------------|----------|--------------|
| Sign up and verify email | 5/5 (100%) | 2m 14s | None |
| Create first project | 4/5 (80%) | 3m 47s | 1 user confused by modal close behavior |
| Invite team member | 3/5 (60%) | 5m 12s | 2 users didn't see "Invite" button (visibility issue) |
| Generate report | 5/5 (100%) | 1m 33s | None |

**Overall SUS Score**: 78 (Above average - target was >70) ✓

### Resolutions

**Issue 1: Invite button low visibility**
- **Root Cause**: Gray secondary button blended with background
- **Fix**: Changed to primary blue button, moved to top-right corner
- **Retest Result**: 5/5 users found it immediately

**Issue 2: Modal close behavior confusing**
- **Root Cause**: X button vs Cancel button had different behaviors (one saved draft, one discarded)
- **Fix**: Made both discard, added explicit "Save Draft" button
- **Retest Result**: No confusion in follow-up tests

---

## 6. Open Questions

**Design Decisions**:
- [ ] Should we add keyboard shortcuts for power users? (e.g., Cmd+K for search)
- [ ] Dark mode: MVP or post-launch?
- [ ] Mobile app: Native or responsive web first?

**Technical Feasibility**:
- [ ] Can backend support real-time collaboration? (affects loading state design)
- [ ] File upload size limits? (affects error message copy)

**Business Requirements**:
- [ ] Paywall placement: After how many projects should we prompt upgrade?
- [ ] Onboarding: Required fields vs optional (affects conversion vs data quality)

---

## Appendix

### Design Files
- Figma: [Link to Figma file with edit access]
- User Flow Diagrams: [Link to FigJam or Miro board]
- Design System: [Link to component library]

### Research Artifacts
- User Interview Notes: [Link to Notion/Docs]
- Competitive Analysis: [Link to spreadsheet]
- Analytics Dashboard: [Link to current product metrics]
- User Testing Videos: [Link to recordings folder]

### Revision History
- v1.0 (Date): Initial draft
- v1.1 (Date): Updated based on stakeholder feedback
- v2.0 (Date): Post-user testing revisions
```

---
