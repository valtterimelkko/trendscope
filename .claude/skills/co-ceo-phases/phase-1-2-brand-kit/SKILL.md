---
name: phase-1-2-brand-kit
description: Co-CEO Phase 1.2 - Launch Brand Designer agent to create visual and verbal identity. Agent-based.
---

# Phase 1.2: Brand Kit & Guide Creation

**Mode:** Agent  
**Skill to use:** `mvp-brand-kit-creation`  
**Complexity:** High  
**Depends on:** Phase 1.1 complete

## Status Communication

Announce to user:
> "Now launching the Brand Designer agent. This creates your visual and verbal identity—logos, colors, typography, voice, and tone. Should take 5-10 minutes. I'll give updates as it progresses."

Monitor for 3-attempt escalations during agent work.

## Agent Instructions

Spawn agent with this prompt:

```
You are a Brand Designer agent. Use the mvp-brand-kit-creation skill.

INPUTS:
- Read: docs/concept/master-concept.md

TASK:
Create a complete Brand Kit & Guide following the skill's process.

OUTPUTS:
- docs/brand/brand-kit-guide.md
- docs/brand/color-palette.md (if detailed)
- docs/brand/microcopy-dictionary.md

CONSTRAINTS:
- Do NOT spawn additional agents
- Do NOT write code or do anything beyond the brand-kit-creation skill
- On 3 failed attempts at any step, escalate to Co-CEO Session with documentation
```

## Completion Criteria

- [ ] Logo system defined (variants documented)
- [ ] Color architecture with semantic colors
- [ ] Typography decisions made
- [ ] Voice & tone defined
- [ ] Microcopy dictionary started

## After Agent Completes

Run commit helper:
```bash
.shared/scripts/co-ceo/git-commit-phase.sh "1.2" "Brand Kit created"
```

Display: "Brand Kit created and committed. Push to GitHub: `git push origin main`"

## Verify Before Proceeding

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 1.2
```
