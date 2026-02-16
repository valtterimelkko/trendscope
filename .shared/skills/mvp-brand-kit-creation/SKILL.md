---
name: mvp-brand-kit-creation
description: Use when creating brand identity assets and brand guide documentation for a SaaS or web application MVP. Creates visual identity (logo system, colors, typography) and verbal identity (voice, tone, microcopy dictionary) plus a lean brand guide document.
---

# MVP Brand Kit & Brand Guide Creation

## Overview

Create a Minimum Viable Brand (MVB) for SaaS/web application MVPs. The goal is professional credibility and trust—not perfection. A consistent, accessible brand signals technical reliability to early adopters.

**Core principle:** Brand trust enables product validation. Users who struggle with chaotic visuals can't evaluate your value proposition.

## When to Use

- Starting a new SaaS/web app MVP project
- Need visual identity (logo, colors, typography) for product development
- Need verbal identity (voice, tone, microcopy) for consistent UX
- Creating brand documentation for team/designer handoff

## Pre-Requisites

**CRITICAL: Before starting, verify these exist or gather them:**

Check for Master Concept file:
```bash
find . -name "*master-concept*" -o -name "*concept*" -type f
```

**Required inputs checklist:**
- [ ] Master Concept file exists (product purpose, target user, value proposition)
- [ ] Service name is finalized or near-final
- [ ] Product type identified: B2B SaaS or B2C App (affects voice, color, formality)

**If Master Concept is missing:** Use the `master-concept-creation` skill first.

**Gather through conversation if not in Master Concept:**
- [ ] Ideal user and their core frustration (status quo pain)
- [ ] Unique utility that justifies the product's existence
- [ ] Brand personality archetype: "Smart Professor," "Rebellious Disrupter," or "Efficient Assistant"
- [ ] Brand antithesis: What the brand is NOT (e.g., professional but not corporate)

## Process Workflow

### Phase 1: Brand Discovery (Conversational)

Extract brand DNA through strategic questions:

1. **User Identification**: Target user and their core frustration
2. **Differentiation**: Unique utility that justifies existence
3. **Personality Archetype**: Guides font and voice choices
4. **Antithesis**: What the brand is NOT (sets guardrails)

**Output:** Clear understanding of brand personality and positioning

### Phase 2: Visual Identity System

Create these core assets:

#### Logo System
| Variant | Use Case | Size |
|---------|----------|------|
| Primary Lockup | Landing page, invoices | Full size |
| Secondary/Stacked | Social profiles, sidebars | Vertical |
| Symbol/Icon | Favicon, app icon, avatars | 16x16px minimum |
| Wordmark | Co-branding, tight spaces | Text only |

**How to create logos for MVP:**
1. Use AI tools (DALL-E, Midjourney) with this prompt template:
   ```
   "Minimalist logo for [service name], a [product category] for [target user].
   Style: [modern/professional/playful], [geometric/organic/abstract].
   Format: Simple icon that works at 16x16px. Flat design, 2-3 colors maximum.
   [Include/exclude text in logo]."
   ```
2. Or use logo makers: Looka, Hatchful, Canva (free tiers available)
3. Export as SVG for scalability + PNG variants (512px, 192px, 32px, 16px)

**Favicon creation:**
- Start with square Symbol/Icon variant (512x512px)
- Generate multi-size ICO: Use `convert logo.png -define icon:auto-resize=16,32,48 favicon.ico`
- Or use online tool: favicon.io, realfavicongenerator.net
- **Critical:** Test visibility on light, dark, and grey browser tabs

#### Color Architecture
```
Primary Brand Color     → Main CTA buttons, key navigation
Secondary/Accent        → Highlights, illustrations
Semantic Colors (FIXED):
  - Success: #28A745 (green)
  - Warning: #FFC107 (yellow/orange)
  - Error: #DC3545 (red)
  - Info: #17A2B8 (blue)
Neutrals               → Text, borders, backgrounds (grey spectrum)
```

**Choosing primary colors by personality:**
- **Smart Professor** → Blues (#2563EB), Teals (#14B8A6), Deep Purples (#7C3AED) — Trust, intelligence
- **Rebellious Disrupter** → Oranges (#F97316), Magentas (#D946EF), Lime (#84CC16) — Energy, boldness
- **Efficient Assistant** → Greens (#10B981), Slate Blues (#3B82F6), Grays (#6B7280) — Calm, reliability

**B2B vs B2C color guidance:**
- B2B SaaS: Professional blues, greys, subdued greens (avoid neon/saturated)
- B2C Apps: More vibrant, saturated colors acceptable (builds emotional connection)

**Validate contrast:** Use WebAIM Contrast Checker or run:
```bash
# Check if contrast meets WCAG AA (requires npm package)
npx @adobe/leonardo-contrast-colors --bg "#FFFFFF" --fg "#3B82F6"
```
**Accessibility requirement:** 4.5:1 for text, 3:1 for UI components (WCAG AA minimum)

#### Typography
- **Recommendation for MVP:** System fonts (San Francisco, Segoe UI, Roboto) or Google Fonts (Inter, Open Sans, Lato)
- Define type scale: H1, H2, H3, Body, Caption with mathematical ratios
- Avoid custom fonts in MVP (licensing costs, performance drag)

#### Iconography
- Use established libraries: Phosphor Icons, Heroicons, or Material Symbols
- Maintain consistent stroke width and corner radius
- Don't mix filled and outlined styles (filled = active state convention)

### Phase 3: Verbal Identity

#### Voice vs Tone
- **Voice** = Consistent personality (the "person" behind the software). Does not change.
- **Tone** = Emotional inflection that adapts to context (cheerful for success, serious for errors).

#### Microcopy Dictionary
Standardize UI terms to prevent cognitive load:

| Category | Decision |
|----------|----------|
| Authentication | "Log in" OR "Sign in" (pick one) |
| Destruction | "Delete" OR "Remove" OR "Trash" (pick one) |
| User naming | "Users" OR "Members" OR "Teammates" (pick one) |

**Microcopy stages:**
1. Pre-action (motivation): "Launch Project" vs generic "Submit"
2. During-action (instruction): "Enter 8+ characters for safety"
3. Post-action (feedback): "We couldn't reach the server. Please try again."

### Phase 4: Brand Guide Document

Create a lean 5-10 page guide (or digital page):

| Section | Content |
|---------|---------|
| 01 Brand Heart | Mission, Vision, Value Proposition |
| 02 Logo Usage | Clear space rules, minimum size, "Don'ts" |
| 03 Color Palette | HEX, RGB values for all colors |
| 04 Typography | Font names, download links, type scale |
| 05 Voice & Tone | 3-4 key attributes, microcopy dictionary |
| 06 Imagery | Icon style, photography mood |

**Format:** Prefer digital/web-based (Notion, Figma public page) over static PDF for easy updates.

**Template:** See `brand-guide-template.md` in this skill's directory for complete copyable template with CSS variables and design tokens.

## Output Files

Create these deliverables in the project folder:

```
docs/
├── brand/
│   ├── brand-kit-guide.md         # Main brand guide document
│   ├── color-palette.md           # Detailed color specifications
│   ├── microcopy-dictionary.md    # Standardized UI terminology
│   └── design-tokens.json         # Design tokens for developer handoff
```

**After creating files, verify they exist:**
```bash
ls -lh docs/brand/
```

## Naming Conventions for Assets

When organizing brand assets, use:
- **Lowercase only** (avoids case-sensitivity issues)
- **Hyphens for separation** (not underscores or spaces)
- **Format:** `category-component-variant-state.extension`
  - Example: `icon-user-filled-active.svg`
  - Example: `logo-primary-light.png`

## Pre-Launch Checklist

Before MVP goes live, verify:
- [ ] Favicon visible on light/dark browser tabs
- [ ] OG tags generate correct social preview image
- [ ] 404 page is branded and helpful
- [ ] Transactional emails match app visual identity
- [ ] All text meets WCAG AA contrast requirements

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Hard-coded colors everywhere | Use design tokens/variables from start |
| Mixing "Log in" and "Sign in" | Pick one term, use consistently |
| Generic error messages ("Error 504") | Human-readable with solution ("Couldn't reach server. Try again.") |
| Designing logo for large display only | Test at 16x16px favicon size |
| Ignoring accessibility | Validate contrast ratios before finalizing |

## Integration Points

This skill produces inputs for:
- **Frontend development**: Colors, fonts, spacing as design tokens
- **Marketing**: Consistent visual assets for landing pages
- **UX design**: Microcopy dictionary for consistent interface language

**Dependencies:** Requires finalized Master Concept and service name before starting.
