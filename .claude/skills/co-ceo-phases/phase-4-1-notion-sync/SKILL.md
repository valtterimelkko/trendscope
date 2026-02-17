---
name: phase-4-1-notion-sync
description: Co-CEO Phase 4.1 - Optional agent to sync documentation to Notion database. Requires NOTION_TOKEN environment variable.
---

# Phase 4.1: Notion Database Building

**Mode:** Agent (optional, requires NOTION_TOKEN)  
**Skills to use:** `notion-list-projects`, `notion-create-project`, `notion-create-note`, `notion-add-note-to-project`  
**Model:** Haiku  
**Depends on:** Phase 3.1 complete with no blockers

## Status Communication

Announce:
> "Syncing your documentation to Notion now (if NOTION_TOKEN is configured). This creates a central project where all documentation is organized. Should take 2-3 minutes."

## Agent Instructions

```
You are a Notion Sync agent. Use the Notion skills.

TASK:
1. List existing Notion projects
2. If project with service name doesn't exist → create it
3. Copy these files as notes to the project:
   - docs/concept/master-concept.md → "Master Concept"
   - docs/brand/brand-kit-guide.md → "Brand Kit & Guide"
   - marketing/positioning-angles.md → "Positioning Angles"
   - marketing/keyword-research.md → "Keyword Research"
   - marketing/lead-magnet.md → "Lead Magnet Strategy"
   - marketing/direct-response-copy.md → "Direct Response Copy"
   - marketing/seo-content.md → "SEO Content Plan"
   - docs/mvp-ux-[project].md → "MVP User Experience"
   - docs/Project-Technical-Architecture.md → "Technical Architecture"

CONSTRAINTS:
- Copy FULL content, no summaries
- Do NOT spawn additional agents
- Verify notes are linked to project after creation
- If NOTION_TOKEN is not configured, skip gracefully
```

## Completion Criteria

- [ ] All documents synced to Notion (or gracefully skipped if no token)
- [ ] Notes linked to project

## After Agent Completes (if applicable)

```bash
.shared/scripts/co-ceo/git-commit-phase.sh "4.1" "Documentation synced to Notion"
```

## Skip Conditions

If NOTION_TOKEN is not configured, announce:
> "Notion sync skipped (NOTION_TOKEN not configured). Proceeding to user approval."

Then proceed to Phase 4.2.
