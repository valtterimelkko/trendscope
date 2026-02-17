---
name: template-selector
description: Use when helping users choose the right frontend template for their MVP. Analyzes the Master Concept and UX Design to recommend the best-fitting template (analytics-dashboard, productivity-tool, content-creator, utility-processor, or digital-download) with clear reasoning.
---

# Template Selector

## Overview

Guide users through selecting the most appropriate frontend template for their MVP based on their Master Concept, UX Design, and target user needs. This skill is used conversationally by the Co-CEO during Phase 4.2 (User Approval Checkpoint).

**Core principle:** Template selection should feel natural and well-reasoned. The recommendation should be obvious once explained, not arbitrary.

## When to Use

- During Phase 4.2 after reviewing completed documentation
- When user is ready to move from planning to implementation
- When user asks "which template should I use?"

## Pre-Requisites

**Required documents must exist:**
```bash
# Verify these exist
ls docs/concept/master-concept.md
ls docs/brand/brand-kit-guide.md
ls docs/mvp-ux-*.md
```

## The Five Templates

### 1. Analytics Dashboard (`templates/analytics-dashboard/`)

**Best for:** Data visualization, metrics tracking, reporting tools

**Key characteristics:**
- Primary value is showing data/insights
- Users check dashboards regularly
- Numbers, charts, and trends are central
- Often has public/shareable views
- Tracking code or data ingestion component

**Personality:** Clean, trustworthy, light theme default

**Billing model:** Usage-based (events/month, API calls)

**Indicator keywords in Master Concept:**
- analytics, metrics, tracking, dashboard
- insights, data, visualization, reports
- monitor, measure, stats, performance
- events, pageviews, visitors, usage

**Example products:** Plausible, Simple Analytics, Baremetrics, Mixpanel

### 2. Productivity Tool (`templates/productivity-tool/`)

**Best for:** Task management, project tracking, workflow tools

**Key characteristics:**
- Primary value is organizing/managing work
- Users create and manipulate items (tasks, projects, docs)
- Collaboration features are common
- Keyboard shortcuts are important
- Workspaces or team structures

**Personality:** Fast, dark mode default, keyboard-first

**Billing model:** Seat-based (per team member)

**Indicator keywords in Master Concept:**
- tasks, projects, team, workspace
- organize, manage, workflow, productivity
- collaborate, assign, track, status
- kanban, list, board, timeline

**Example products:** Linear, Notion, Asana, Todoist

### 3. Content Creator (`templates/content-creator/`)

**Best for:** Content creation, publishing, scheduling tools

**Key characteristics:**
- Primary value is creating/publishing content
- Users compose, edit, and schedule posts
- Platform connections (social, email, etc.)
- Queue and scheduling features
- Analytics on content performance

**Personality:** Creative, warm, editorial feel

**Billing model:** Feature limits (posts/month, connected accounts)

**Indicator keywords in Master Concept:**
- content, posts, publish, schedule
- social, twitter, linkedin, newsletter
- creator, writer, editor, compose
- queue, calendar, draft, campaign

**Example products:** Buffer, Typefully, ConvertKit, Ghost

### 4. Utility Processor (`templates/utility-processor/`)

**Best for:** Single-action tools (upload/process/download), photo/file utilities, converters, QR/asset generators

**Key characteristics:**
- One core workflow with primary CTA
- Minimal navigation (2-4 items max)
- Shows progress, status, and history of jobs
- Usage/credit billing or simple subscription with allowance
- Clear quota meter and job history

**Personality:** Minimal, focused, CTA-first

**Billing model:** Usage-based or credit-pack with overage

**Indicator keywords in Master Concept:**
- upload, convert, process, resize, compress, transcode
- QR, generator, transform, filter, export, download
- credits, usage, jobs, tasks, allowance

**Example products:** CloudConvert, ProductMotion (simple flow variants), TinyPNG

### 5. Digital Download Portal (`templates/digital-download/`)

**Best for:** Selling downloadable assets/packs (design kits, presets, LUTs, PDFs), paid resource hubs

**Key characteristics:**
- Landing + pricing with social proof
- Gated downloads locker with license/access keys
- Order history and receipts
- Limits based on plan (downloads per month or storage cap)
- Simple account/billing settings

**Personality:** Clean, trustworthy, light theme

**Billing model:** Tiered download access (monthly/annual), optional one-time add-ons

**Indicator keywords in Master Concept:**
- downloads, assets, files, bundles, packs, presets, LUTs
- store, paywall, portal, access, license, receipt
- members area, customer portal, digital goods

**Example products:** Gumroad-style portals, design kit stores, preset marketplaces

## Selection Process

### Step 1: Extract Key Signals

Read the Master Concept and identify:

1. **Primary user action:** What does the user DO most in the app?
   - View/analyze data → Analytics
   - Create/organize items → Productivity
   - Create/publish content → Content
   - Upload/process and download outputs → Utility Processor
   - Purchase and access downloadable files → Digital Download

2. **Value delivery mechanism:** How does the product help?
   - Shows insights/trends → Analytics
   - Manages work/tasks → Productivity
   - Distributes content → Content
   - Converts/processes assets efficiently → Utility Processor
   - Unlocks/downloads paid assets securely → Digital Download

3. **Billing fit:** What makes sense for pricing?
   - Usage/volume-based → Analytics
   - Team size matters → Productivity
   - Feature tiers make sense → Content

### Step 2: Check UX Design Alignment

Review the UX document for:

- **Dashboard-heavy?** Charts, metrics, date ranges → Analytics
- **Item-centric?** Lists, cards, kanban, detail views → Productivity
- **Composer-centric?** Editors, previews, scheduling → Content
- **Single primary flow?** Upload/process, status, history → Utility Processor
- **Storefront + locker?** Pricing + download/account area → Digital Download

### Step 3: Handle Edge Cases

**Hybrid products:** Some products span categories. Choose based on PRIMARY value:

| Scenario | Recommendation | Reasoning |
|----------|----------------|-----------|
| Task tool with analytics | Productivity | Tasks are primary, analytics is secondary |
| Newsletter with subscriber stats | Content | Publishing is primary, stats support it |
| Dashboard builder tool | Analytics | Even though users "create," the output is dashboards |
| File converter with public landing sales page | Utility Processor | Core value is processing, not the store |
| Asset store with occasional processing (e.g., custom zip) | Digital Download | Core value is purchased downloads |

**Unclear fit:** If genuinely unclear, present all 3 with honest pros/cons and let user decide.

### Step 4: Present Recommendation

Structure your recommendation:

```markdown
## Template Recommendation

Based on your Master Concept and UX Design, I recommend: **[Template Name]**

### Why This Template Fits

1. **Primary user action alignment:** [Explain match]
2. **Value delivery match:** [Explain match]
3. **Billing model fit:** [Explain match]

### What You Get

- [Key feature 1 from this template]
- [Key feature 2 from this template]
- [Key feature 3 from this template]

### Alternatives Considered

**[Other Template 1]:** [Why it's less suitable]
**[Other Template 2]:** [Why it's less suitable]

### Confirm Selection

Does this template feel right for your product? We can discuss alternatives if needed.
```

## Conversation Flow

### Opening (During Phase 4.2)

After summarizing completed work, transition:

> "Now let's select the frontend template for your MVP. Based on what we've built so far, I'll recommend the best-fitting template."

### Analysis Phase

Walk through your reasoning:

> "Looking at your Master Concept, I see [key observations]..."
> "Your UX design emphasizes [relevant patterns]..."
> "This points toward the [template] template because..."

### Recommendation

Present clearly:

> "I recommend the **[template]** template. Here's why..."

### Confirmation

Seek explicit agreement:

> "Does this feel right? We can discuss alternatives if you see it differently."

### Edge Cases

If user pushes back:

> "I hear you. Let me explain the trade-offs between [Template A] and [Template B]..."

If user is unsure:

> "Would it help to see what each template includes? I can walk through the key differences."

## Template Comparison Quick Reference

| Aspect | Analytics | Productivity | Content |
|--------|-----------|--------------|---------|
| Primary UI | Dashboard with charts | Lists/boards with items | Editor with preview |
| User goal | Understand data | Organize work | Publish content |
| Billing | Usage-based | Seat-based | Feature limits |
| Theme default | Light | Dark | Light/warm |
| Key pages | Dashboard, snippet setup | Workspace, item detail | Composer, queue |
| Collaboration | View sharing | Team workspaces | Connected accounts |

## After Selection

Once template is confirmed:

1. Document the selection in a clear location
2. Proceed to Phase 4.3: Template Integration
3. Pass template path to subsequent agents:
   - `templates/analytics-dashboard/`
   - `templates/productivity-tool/`
   - `templates/content-creator/`

## Common Mistakes to Avoid

1. **Choosing based on aesthetics:** Templates can be styled. Choose based on functionality.
2. **Overthinking:** If it's 60/40 between two, either will work. Pick the 60.
3. **Ignoring billing model:** The billing architecture matters—usage vs seats vs features.
4. **Forcing hybrid:** Don't try to combine templates. Pick one, customize later.

## Quick Decision Tree

```
What does the user primarily DO in your app?

├── View/analyze information
│   └── → Analytics Dashboard
│
├── Create and manage items (tasks, projects, docs)
│   └── → Productivity Tool
│
└── Create and publish/schedule content
    └── → Content Creator
```
