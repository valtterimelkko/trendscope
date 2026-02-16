---
name: phase-1-4-marketing-foundation
description: Co-CEO Phase 1.4 - Orchestrate 6 sequential marketing agents for positioning, keywords, lead magnets, copy, voice, and SEO planning.
---

# Phase 1.4: Marketing Foundation

**Mode:** Sequential Agents (6 total)  
**Depends on:** Phase 1.1, 1.2, 1.3 complete

## Status Communication

Announce:
> "Starting Phase 1.4: Marketing Foundation. I'll launch 6 agents sequentially to create positioning, keyword research, lead magnet strategy, direct response copy, brand voice codification, and SEO content plan. This takes 25-40 minutes total."

## Agent Sequence

### 1.4.1 Positioning Angles
**Skill:** `positioning-angles-generator` | **Model:** Haiku

```
You are a Positioning Strategist agent. Use positioning-angles-generator skill.

INPUTS:
- docs/concept/master-concept.md
- docs/brand/brand-kit-guide.md

TASK: Generate 3-5 positioning angles using 8 frameworks. Output: marketing/positioning-angles.md

CONSTRAINTS: No additional agents. 3-attempt escalation protocol.
```

### 1.4.2 Keyword Research
**Skill:** `keyword-research-generator` | **Model:** Haiku | **Depends:** 1.4.1

```
You are a Keyword Research Strategist. Use keyword-research-generator skill.

INPUTS: master-concept.md, positioning-angles.md
TASK: Build keyword map using 6 Circles Method. Output: marketing/keyword-research.md
```

### 1.4.3 Lead Magnet Strategy
**Skill:** `lead-magnet-architect` | **Model:** Haiku | **Depends:** 1.4.1, 1.4.2

```
You are a Lead Magnet Strategist. Use lead-magnet-architect skill.

INPUTS: master-concept.md, positioning-angles.md, keyword-research.md
TASK: Design 2-3 lead magnet formats with specs. Output: marketing/lead-magnet.md
```

### 1.4.4 Direct Response Copy
**Skill:** `direct-response-copy-generator` | **Model:** Haiku | **Depends:** 1.4.1

```
You are a Direct Response Copywriter. Use direct-response-copy-generator skill.

INPUTS: master-concept.md, brand-kit-guide.md, positioning-angles.md
TASK: Generate landing page and email copy. Output: marketing/direct-response-copy.md
```

### 1.4.5 Brand Voice Codification
**Skill:** `brand-voice-codifier` | **Model:** Haiku | **Depends:** 1.4.4

```
You are a Brand Voice Strategist. Use brand-voice-codifier skill.

INPUTS: master-concept.md, brand-kit-guide.md, direct-response-copy.md
TASK: Extend Brand Kit with voice guidelines. EXTENDS: docs/brand/brand-kit-guide.md
```

### 1.4.6 SEO Content Planning
**Skill:** `seo-content-planner` | **Model:** Haiku | **Depends:** 1.4.2, 1.4.5

```
You are an SEO Content Strategist. Use seo-content-planner skill.

INPUTS: keyword-research.md, positioning-angles.md, master-concept.md, brand-kit-guide.md
TASK: Create pillar-cluster content strategy. Output: marketing/seo-content.md
```

## After Phase 1.4 Completes

```bash
.shared/scripts/co-ceo/git-commit-phase.sh "1.4" "Marketing Foundation complete"
```

## Verify

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 1.4
```
