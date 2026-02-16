---
name: master-concept-creation
description: Use when creating or refining a Master Concept document for an MVP - a strategic product definition that articulates the why and what before technical requirements. Use before PRD creation, when gaps exist in the concept, or when stakeholder alignment is needed.
---

# Master Concept Creation

## Overview

Create a comprehensive Master Concept document through collaborative dialogue. The Master Concept is the strategic foundation for an MVP - it defines the problem, audience, value proposition, and success criteria before any technical work begins.

**Core principle:** If you can't explain the concept clearly in a concise document, it's too complex or ill-defined to succeed as software.

## When to Use

- Starting a new MVP project with an initial idea
- Refining an existing concept that has gaps
- Creating stakeholder alignment before development
- Before writing a PRD (Product Requirements Document)

**NOT for:**
- Technical architecture (use PRD/architecture docs)
- Implementation planning (use writing-plans)
- Projects already in development

## The Process

**Phase 1: Context & Problem Discovery**
- Review any existing concept files or notes
- Ask one question at a time to understand:
  - What problem are we solving?
  - Who feels this pain most acutely?
  - What's the current workaround/status quo?
  - Why now? (market timing, technology shift, regulatory change)
- Classify: Is this a "painkiller" (urgent) or "vitamin" (nice-to-have)?

**Phase 2: Target Audience Definition**
- Define the Initial Target Audience (early adopter segment)
- Distinguish Buyer vs User (especially for B2B)
- Apply Jobs to Be Done framework:
  - What job is the user trying to accomplish?
  - What struggle/friction prevents them today?
  - What does success look like for them?

**Phase 3: Solution Vision**
- Craft a high-level concept description (not features)
- Define the Unique Value Proposition (UVP)
- Create a "Day in the Life" narrative showing the transformed user experience
- Specify form factor (web, mobile, API, etc.) with justification

**Phase 4: MVP Scope (MoSCoW)**
- **Must Have:** Non-negotiables without which product is useless
- **Should Have:** Important but not vital, first to cut if timeline slips
- **Could Have:** Nice-to-haves included only if time permits
- **Won't Have:** Explicit exclusions (critical for preventing scope creep)

**Phase 5: Business Viability**
- Revenue model hypothesis (SaaS, transactional, etc.)
- Define 3-5 Key Performance Indicators
- Identify the "North Star" metric that captures core value
- Prioritize actionable metrics over vanity metrics

**Phase 6: Risks & Validation**
- List critical assumptions
- Identify the "Riskiest Assumption" (if false, kills the project)
- Define validation approach (smoke tests, concierge MVP, etc.)
- Document known constraints (budget, timeline, technical)

## Document Structure

**High-level structure overview** (shown below). For a detailed template with examples, guidance text, and formatting, use the validator script's template generation:

```bash
.shared/scripts/master-concept/validate-concept.sh --generate-template docs/concept/master-concept.md
```

The detailed template includes:
- Inline examples for each section
- Formatted tables for metrics
- Checkboxes for feature lists
- Placeholder guidance text

**Simplified structure for reference:**

```markdown
# [Product Name] Master Concept

## Executive Summary
*One paragraph elevator pitch*

## Problem Statement & Market Context
### The Pain
*What specific problem are we solving?*

### Current State
*How is it solved today? (competitors/workarounds)*

### Why Now?
*Market timing, technology shift, opportunity*

## Target Audience
### Primary Persona
*Who is the early adopter? Behavioral description, not demographics.*

### Job to Be Done
*What are they trying to achieve? What's blocking them?*

## Solution Vision
### The Concept
*High-level description (e.g., "Uber for X")*

### Unique Value Proposition
*Why is this better than the status quo?*

### User Journey
*Narrative "Day in the Life" walkthrough*

## MVP Scope (MoSCoW)
### Must Have
*Non-negotiable core features*

### Should Have
*Important but cuttable*

### Could Have
*Nice-to-haves*

### Won't Have
*Explicit exclusions for MVP*

## Business Model & Success Metrics
### Revenue Model
*How does it capture value?*

### Key Metrics
*3-5 KPIs, including North Star metric*

## Risks & Assumptions
### Critical Assumptions
*What must be true for this to work?*

### Riskiest Assumption
*The one belief that, if false, kills the project*

### Validation Plan
*How will we test critical assumptions?*

### Constraints
*Known limitations (budget, timeline, technical)*

## FAQ
### External (User Questions)
*What would users ask?*

### Internal (Stakeholder Questions)
*Tough questions from the team*
```

## Key Principles

**One question at a time** - Don't overwhelm, explore thoroughly

**Problem before solution** - Resist "solution bias"; understand the pain first

**Root cause analysis** - Go beyond symptoms to underlying causes

**Constraint-based scoping** - Define scope by constraints (budget/time/team) not just features

**Explicit exclusions** - "Won't Have" list prevents scope creep

**Quantified success** - Use measurable criteria, not "easy to use" or "fast"

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Kitchen Sink Syndrome | Strict MoSCoW, prominent "Won't Have" list |
| Vague success criteria | Quantify: "50% reduction" not "faster" |
| Ignoring the admin/ops user | Include operational requirements in FAQ |
| Solutioning too early | Focus on outcomes, not screen layouts |
| Everyone is the target | Define narrow early adopter segment |

## Helper Script

Location: `.shared/scripts/master-concept/validate-concept.sh`

### Generate Template
```bash
.shared/scripts/master-concept/validate-concept.sh --generate-template docs/concept/master-concept.md
```

### Validate Completeness
```bash
.shared/scripts/master-concept/validate-concept.sh docs/concept/master-concept.md
```

Output shows required vs recommended sections, detects unfilled placeholders, and checks document length.

## Examples

See `.shared/skills/master-concept-creation/examples/` for complete, realistic Master Concept examples:

- **dashsync-example.md**: A comprehensive example showing a fictional SaaS product concept with all sections properly filled out
- **README.md**: Guidance on using the examples

These examples demonstrate best practices for:
- Problem statement depth and specificity
- Behavioral persona definition
- Jobs to Be Done articulation
- MoSCoW prioritization with explicit exclusions
- Quantified success metrics with rationale

Use these as references when creating your own Master Concept.

## After the Concept

**Save document to:** `docs/concept/master-concept.md` (or project-specific path)

**Validate before finalizing:** Run the validator script to ensure all required sections are complete.

**Next steps:**
- Service name & domain ideation (use domain-name-brainstormer)
- Brand Kit & Guide creation
- MVP User Experience design
- Technical PRD creation

## Framework Reference

This skill synthesizes best practices from:
- **Amazon Working Backwards (PR/FAQ)** - Customer-first narrative approach
- **Lean Canvas** - Problem-solution fit focus
- **Jobs to Be Done** - User motivation framework
- **MoSCoW** - Prioritization methodology

For detailed framework comparisons, see the research document at `research/MVP_Master_Concept_Document_Best_Practices.md`.
