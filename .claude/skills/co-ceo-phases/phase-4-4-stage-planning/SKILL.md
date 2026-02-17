---
name: phase-4-4-stage-planning
description: Co-CEO Phase 4.4 - Launch parallel Stage Architect agents to create detailed architecture plans for each implementation stage. Safe for parallel execution as each writes to different file. Kimi Code CLI compatible.
---

# Phase 4.4: Stage Architecture Planning

**Mode:** Parallel Agents in batches (max 3 concurrent — each agent writes to different file)  
**Uses:** Stage-architecture-template from `mvp-technical-prd-architecture`  
**Complexity:** Medium (structured architecture planning)  
**Platform:** Kimi Code CLI  
**Depends on:** Phase 4.3 complete

## Context

Phase 4.3 has already deployed:
- ✅ Complete frontend UI (all pages personalized)
- ✅ Database schema with RLS policies
- ✅ Authentication (Google OAuth)
- ✅ Stripe products/prices created
- ✅ Stripe webhook endpoint URL registered (handlers pending)

## What Stages Focus On

- ❌ Backend API endpoint logic
- ❌ Stripe webhook handler logic
- ❌ Business logic connecting frontend to database
- ❌ Custom integrations beyond template scope

**Explicitly exclude from stage plans:**
- Lead magnet or marketing campaign implementation (capture forms, nurture flows, CRM sync)
- Growth tooling outside the core app deployment scope

## Status Communication

Announce:
> "Creating detailed architecture plans for each implementation stage. I'll launch Stage Architect agents in parallel—each writes to a separate file so this is safe."

## Process

1. Analyze Technical PRD to determine stages
2. Filter out infrastructure stages (handled by 4.3)
3. Spawn Stage Architect agents in **batches of up to 3** in parallel using Kimi Task tool; wait until every agent in the batch reports finished (completed file output or explicit failure/timeout noted) before launching the next batch. Keep status pings short (e.g., "Stage 1 ✅, Stage 2 running") to avoid log bloat.

## Stage Architect Agent Template (Kimi Task Tool Format)

```python
# For each stage, spawn with:
Task(
    description=f"Stage Architect - Stage {N}: {stage_name}",
    subagent_name="coder",
    prompt=f"""
You are a Stage Architect agent for Stage {N}: {stage_name}.

COMPLEXITY: medium — This task requires structured architecture planning and documentation.

INPUTS:
- Read: docs/Project-Technical-Architecture.md (especially Section 5: Stages)

CONTEXT - Already Deployed by Phase 4.3:
- Frontend UI complete, Database schema deployed, Auth configured
- Stripe products exist, webhook endpoint registered

Your stage focuses on IMPLEMENTATION GAPS: API logic, webhook handlers, business logic.

TASK:
Create detailed architecture plan using stage-architecture-template.

OUTPUT:
- docs/stages/stage-{NN:02d}-{name}.md

INCLUDE:
- Stage overview, Dependencies, Technical components
- API contracts, Database schema changes (if any)
- Testing requirements, Progress log section, Issues section

CONSTRAINTS:
- Do NOT spawn additional agents
- On 3 failed attempts, escalate to Co-CEO Session
"""
)
```

## Parallel Safety

Each agent writes to a *different* file (still cap at 3 concurrent to avoid session overload):
- `docs/stages/stage-01-*.md`
- `docs/stages/stage-02-*.md`
- etc.

No file overlap = safe for parallel execution.

## After All Agents Complete

```bash
.shared/scripts/co-ceo/git-commit-phase.sh "4.4" "Stage architecture plans created"
```

## Verify

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 4.4
```
