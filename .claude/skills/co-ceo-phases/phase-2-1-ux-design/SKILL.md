---
name: phase-2-1-ux-design
description: Co-CEO Phase 2.1 - Launch UX Designer agent to create detailed user flows, screen specifications, and interaction design. Kimi Code CLI compatible.
---

# Phase 2.1: MVP UX Design

**Mode:** Agent  
**Skill to use:** `mvp-ux-design`  
**Complexity:** High (requires creative reasoning and design decisions)  
**Platform:** Kimi Code CLI  
**Depends on:** Phase 1.1, 1.2, 1.3, 1.4 complete

## Status Communication

Announce:
> "Launching the UX Designer agent now. This creates detailed user flows, screen specifications, and interaction design based on your concept and brand. This is a bigger task—should take 15-30 minutes. I'll give progress updates."

Monitor agent progress and watch for 3-attempt escalations.

## Agent Instructions (Kimi Task Tool Format)

```python
Task(
    description="UX Designer - Create MVP UX documentation",
    subagent_name="coder",
    prompt="""
You are a UX Designer agent. Use the mvp-ux-design skill.

COMPLEXITY: high — This task requires deep reasoning, creative design decisions, and comprehensive user experience planning.

INPUTS (Required):
- Read: docs/concept/master-concept.md
- Read: docs/brand/brand-kit-guide.md

INPUTS (Marketing Context):
- Read: marketing/positioning-angles.md (for messaging context)
- Read: marketing/direct-response-copy.md (for copy patterns)

TASK:
Create comprehensive MVP User Experience documentation following the skill's 6-phase process.

OUTPUTS:
- docs/mvp-ux-[project-name].md

CONSTRAINTS:
- Do NOT spawn additional agents
- Do NOT write code or create mockups beyond the skill's scope
- Follow all phase completion checklists in the skill
- Document all 4 states for major screens (ideal, empty, loading, error)
- On 3 failed attempts at any step, escalate to Co-CEO Session with documentation
"""
)
```

## Completion Criteria

- [ ] All 6 phases completed per skill checklists
- [ ] User flows for all critical journeys
- [ ] Screen specifications with 4 states documented
- [ ] Accessibility requirements noted

## After Agent Completes

```bash
.shared/scripts/co-ceo/git-commit-phase.sh "2.1" "MVP User Experience design completed"
```

Display: "UX Design committed to git. Push to GitHub: `git push origin main`"

## Verify Before Proceeding

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 2.1
```
