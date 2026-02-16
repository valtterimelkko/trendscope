---
name: phase-3-1-quality-gate
description: Co-CEO Phase 3.1 - Launch Quality Assurance agent to validate all Phase 1 & 2 documents for completeness and consistency. BLOCKER issues must be resolved before Phase 4. Kimi Code CLI compatible.
---

# Phase 3.1: Consistency & Quality Check

**Mode:** Agent  
**Skill to use:** `consistency-quality-check`  
**Complexity:** Low (rule-based validation)  
**Platform:** Kimi Code CLI  
**Depends on:** All Phase 1 & 2 outputs

## Status Communication

Announce:
> "Launching Quality Assurance check now. This agent validates all documents for completeness, consistency, and conflicts. Should take 5-10 minutes."

## Agent Instructions (Kimi Task Tool Format)

```python
Task(
    description="Quality Assurance - Validate document consistency",
    subagent_name="coder",
    prompt="""
You are a Quality Assurance agent. Use the consistency-quality-check skill.

COMPLEXITY: low — This is a structured, rule-based validation task.

TASK:
Validate all created documents for:
1. Completeness (all required sections per skill templates)
2. Cross-document consistency (names, colors, features match)
3. No conflicting information between documents
4. API endpoints consistent (if PRD defines them)
5. Marketing materials align with Master Concept and Brand Kit

INPUTS (Phase 1.1-1.3 Core Documents):
- docs/concept/master-concept.md
- docs/brand/brand-kit-guide.md

INPUTS (Phase 1.4 Marketing Foundation):
- marketing/positioning-angles.md
- marketing/keyword-research.md
- marketing/lead-magnet.md
- marketing/direct-response-copy.md
- marketing/seo-content.md

INPUTS (Phase 2.1-2.2 Design Documents):
- docs/mvp-ux-[project].md
- docs/Project-Technical-Architecture.md

OUTPUTS:
Quality report with issues categorized:
- BLOCKER: Must fix before proceeding
- WARNING: Should fix, doesn't block
- SUGGESTION: Nice to have

ACTIONS:
- Auto-fix minor issues if safe
- Run validation scripts:
  - .shared/scripts/consistency-check/validate-document-structure.sh docs/
  - .shared/scripts/consistency-check/validate-document-structure.sh marketing/
  - .shared/scripts/consistency-check/cross-reference-check.sh docs/

CONSTRAINTS:
- Do NOT spawn additional agents
- Escalate any BLOCKER issues to Co-CEO Session
"""
)
```

## On Issues Found

1. If BLOCKERS exist → escalate to Co-CEO → user notified
2. BLOCKERS must be resolved before Phase 4
3. WARNINGS can proceed with acknowledgment

## After Agent Completes

```bash
.shared/scripts/co-ceo/git-commit-phase.sh "3.1" "Quality gate checks completed"
```

## Verify

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 3.1
```
