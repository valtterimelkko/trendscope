---
name: phase-5-1-architecture-check
description: Co-CEO Phase 5.1 - Quality Gate #2. Launch agent to validate all stage architecture files for consistency and implementation readiness. Kimi Code CLI compatible.
---

# Phase 5.1: Architecture Consistency Check

**Mode:** Agent  
**Skill to use:** `consistency-quality-check`  
**Complexity:** Medium (structured validation)  
**Platform:** Kimi Code CLI  
**Depends on:** All stage architecture files created (Phase 4.4)

## Status Communication

Announce:
> "Running Quality Gate #2: Validating all stage architecture files for consistency and implementation readiness."

## Agent Instructions (Kimi Task Tool Format)

```python
Task(
    description="Architecture QA - Validate stage files",
    subagent_name="coder",
    prompt="""
You are a Quality Assurance agent for architecture files.

COMPLEXITY: medium — This task requires structured validation of technical documentation.

TASK:
Validate all stage architecture files for:
1. Quality and detail level (sufficient for autonomous implementation)
2. No conflicts between stages
3. API endpoints match between frontend and backend stages
4. Database changes are compatible across stages
5. Dependencies are correctly ordered

INPUTS:
- docs/Project-Technical-Architecture.md
- docs/stages/*.md (all stage files)

ACTIONS:
- Make minor alignment fixes directly
- Escalate significant conflicts to Co-CEO Session

Use validation scripts if available:
- .shared/scripts/api-validation/*.py
- .shared/scripts/consistency-check/validate-document-structure.sh docs/stages/

CONSTRAINTS:
- Do NOT spawn additional agents
- Escalate BLOCKER issues to Co-CEO Session
"""
)
```

## Completion Criteria

- [ ] All stage files have sufficient detail for autonomous implementation
- [ ] No conflicting API contracts between stages
- [ ] Database schema changes are compatible
- [ ] Dependencies correctly ordered
- [ ] No BLOCKER issues remaining

## On Issues Found

1. Minor issues → auto-fix
2. Significant conflicts → escalate to Co-CEO → user notified
3. Must resolve conflicts before Phase 6

## After Agent Completes

```bash
.shared/scripts/co-ceo/git-commit-phase.sh "5.1" "Architecture consistency check completed"
```

## Verify

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 5.1
```
