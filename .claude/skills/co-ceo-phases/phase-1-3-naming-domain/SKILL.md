---
name: phase-1-3-naming-domain
description: Co-CEO Phase 1.3 - Service naming and domain selection through user conversation. Uses domain-name-brainstormer skill for availability checking.
---

# Phase 1.3: Service Naming & Domain Ideation

**Mode:** Conversational with main user  
**Skill to use:** `domain-name-brainstormer` (for domain checking)  
**Model:** Opus (Co-CEO Session)  
**Depends on:** Phase 1.1, 1.2 complete

## Status Communication

Announce:
> "Starting Phase 1.3: Naming & Domain Selection. We'll brainstorm names that fit your brand, then research domain availability. This is important—we want a name that's actually available."

## Process

1. Review Master Concept and Brand Kit for context
2. Guide naming style preferences with options (action-oriented vs personality-based, etc.)
3. Brainstorm service names aligned with brand personality
4. Use `domain-name-brainstormer` skill to research 10+ name/domain combinations
5. Compile findings report showing all researched domains with availability status
6. Present findings—offer user option to select, verify externally, or revisit later
7. After user decision, update both documents:
   - `docs/concept/master-concept.md` with official name
   - `docs/brand/brand-kit-guide.md` with name

**Critical:** Domain availability verification is crucial. A domain selected as "available" that is taken requires extensive file changes later.

## Completion Criteria

- [ ] Service name finalized and approved by user (or decision deferred)
- [ ] Domain verified available (or holding while user verifies)
- [ ] Name appears consistently in Master Concept and Brand Kit

## After Completion

```bash
.shared/scripts/co-ceo/git-commit-phase.sh "1.3" "Service name and domain finalized"
```

Display: "Name and domain locked. Committed to git."

## Verify Before Proceeding

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 1.3
```
