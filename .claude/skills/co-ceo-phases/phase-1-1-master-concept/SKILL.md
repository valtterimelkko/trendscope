---
name: phase-1-1-master-concept
description: Co-CEO Phase 1.1 - Refine Master Concept through collaborative dialogue. Conversational with main user.
---

# Phase 1.1: Master Concept Refinement

**Mode:** Conversational with main user  
**Skill to use:** `master-concept-creation`  
**Model:** Opus (Co-CEO Session)  
**Depends on:** None

## Status Communication

Before starting, announce:
> "Starting Phase 1.1: Refining your Master Concept. This is a conversation about what you're building, why, and for whom. I'll guide you through key questions."

## Process

1. Check for existing Overall Concept file in project root
2. Use the `master-concept-creation` skill's question-by-question approach
3. Fill gaps collaboratively—don't assume answers
4. Create/update `docs/concept/master-concept.md`
5. Validate with helper script:
```bash
.shared/scripts/master-concept/validate-concept.sh docs/concept/master-concept.md
```

## Completion Criteria

- [ ] All required sections present (validator passes)
- [ ] Problem, audience, value prop clearly defined
- [ ] MoSCoW scope with explicit "Won't Have" list
- [ ] Success metrics are quantifiable

## After Completion

Run the commit helper:
```bash
.shared/scripts/co-ceo/git-commit-phase.sh "1.1" "Master Concept created and validated"
```

Display to user:
> "Master Concept created and committed. You can push to GitHub: `git push origin main`"

## Verify Before Proceeding

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 1.1
```
