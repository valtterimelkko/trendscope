---
name: phase-6-1-stage-execution
description: Co-CEO Phase 6.1 - Orchestrate Implementation agents for each stage with hybrid complexity-aware git workflow. Simple stages stay on main, complex stages use worktrees with mandatory verification gates. Kimi Code CLI compatible.
---

# Phase 6.1: Stage Execution - Hybrid Complexity-Aware Orchestration

**Mode:** Sequential Agents with complexity-aware branching
**Skills:** `test-driven-development`, `systematic-debugging`, `verification-before-completion`, `writing-plans`
**Complexity:** Varies by stage (simple to complex)
**Platform:** Kimi Code CLI
**Depends on:** Phase 5.1 complete **and Phase 6.2 security review complete**

## Critical Context

Phase 4.3 already deployed: Frontend UI, Database schema, Auth, Stripe products. Phase 4.3.5 Supabase security audit **and** Phase 6.2 security review must be PASS before starting any stage work.

**Implementation focuses on:**
- Backend API endpoints (replace mock responses with real queries)
- Stripe webhook handlers (subscription lifecycle events)
- Business logic (connect frontend to database)
- Custom features (project-specific processing)

**Out of scope for Phase 6.1:**
- Lead magnet campaign tooling (landing pages, capture flows, nurture automation)
- Growth/marketing automation infrastructure (CRM sync, email campaigns)
- Any non-core marketing systems beyond the Phase 1.4 strategy docs

**CRITICAL: Stripe Account Verification**
Before implementation begins, ensure:
- ✅ Stripe account is created (signup at stripe.com)
- ✅ Account is verified (email + phone verification complete)
- ✅ Live API keys are obtained from Dashboard → Developers → API Keys
- ✅ Set `STRIPE_SECRET_KEY` environment variable to LIVE key (not test key) for production
- ✅ Test keys are available for staging/development before going live
- Note: During Phase 4.3, test keys were used. Stage 6.1 implementation should use test keys unless explicitly deploying to production.

## Hybrid Complexity-Aware Git Workflow

**The CO-CEO Session automatically detects stage complexity and chooses the appropriate strategy:**

### Step 1: Analyze Stage Complexity

**Before starting any stage:**
```bash
.shared/scripts/co-ceo/detect-stage-complexity.sh --verbose
```

This produces a recommendation:
- **`single-branch`** → Simple, sequential stages affecting isolated files
- **`hybrid-worktrees`** → Complex stages with external dependencies or schema changes

### Step 2: Choose Strategy Based on Complexity

#### Strategy A: Single-Branch (Simple Stages)
**When:** Stages are straightforward with minimal cross-stage dependencies

```bash
# BEFORE Agent:
.shared/scripts/co-ceo/verify-stage-readiness.sh <stage-number>

# AFTER Agent Completes:
.shared/scripts/co-ceo/verify-stage-completion.sh <stage-number>
# ^ Confirms all changes committed, no uncommitted files left behind
```

**Advantages:**
- No branch management overhead
- Simpler workflow for sequential work
- Faster builds and testing

#### Strategy B: Hybrid Worktrees (Complex Stages)
**When:** Stages have external integrations, schema changes, or high complexity

```bash
# BEFORE Agent:
.shared/scripts/co-ceo/verify-stage-readiness.sh <stage-number>
git checkout -b stage/[NN]-[stage-name]

# AGENT COMPLETES...

# AFTER Agent Completes:
.shared/scripts/co-ceo/verify-stage-completion.sh <stage-number> stage/[NN]-[stage-name]
# ^ Verifies merge to main actually succeeded

# If using worktree strategy:
git branch -d stage/[NN]-[stage-name]  # Clean up after merge verified
```

**Advantages:**
- Rollback capability if stage fails
- Isolation for complex changes
- Safety for external API integrations

## CRITICAL VERIFICATION GATES

**These gates MUST happen between every stage. They prevent the "uncommitted files left behind" bug:**

### GATE 1: Pre-Stage Readiness (Before Agent Starts)
```bash
# Run before spawning each Implementation agent
.shared/scripts/co-ceo/verify-stage-readiness.sh <stage-number> --strict

# This verifies:
# ✓ Stage architecture file exists
# ✓ Previous stage completed (if applicable)
# ✓ Git working directory is CLEAN
# ✓ No uncommitted changes exist
```

### GATE 2: Post-Stage Completion (After Agent Finishes)
```bash
# Run after agent reports completion
.shared/scripts/co-ceo/verify-stage-completion.sh <stage-number>

# This verifies:
# ✓ All implementation committed (no files left hanging)
# ✓ Stage architecture file updated
# ✓ If using worktrees: branch was actually merged to main
# ✓ Main branch contains stage changes
```

**If GATE 2 fails with uncommitted files:**
1. Identify the orphaned files
2. Either commit them: `git add . && git commit -m "Fix: commit missed changes"`
3. Or discard them: `git checkout -- <files>`
4. Run GATE 2 again to verify

## Implementation Agent Template (Kimi Task Tool Format)

```python
# Spawn implementation agent with:
Task(
    description=f"Implementation - Stage {N}: {stage_name}",
    subagent_name="coder",
    prompt=f"""
You are an Implementation agent for Stage {N}: {stage_name}.

COMPLEXITY: {complexity_level} — This stage involves {complexity_description}.

INPUTS:
- docs/stages/stage-{NN:02d}-{name}.md
- docs/Project-Technical-Architecture.md

CRITICAL INSTRUCTIONS:
- You are working {branch_instruction}
- ALL changes must be committed before you finish
- Do NOT leave any files uncommitted
- Update the stage architecture file Progress Log as you implement
- Run verification before declaring done

SKILLS TO USE:
- test-driven-development (RED-GREEN-REFACTOR)
- systematic-debugging (when issues arise)
- verification-before-completion (before declaring done)

PROCESS:
1. Review stage architecture file completely
2. Use writing-plans skill to create detailed task list
3. Implement using TDD: RED → GREEN → REFACTOR
4. Commit frequently with conventional messages
5. Update progress log in stage architecture file
6. Run verification before declaring complete
7. Ensure all files are committed—do not leave any uncommitted

ERROR HANDLING (3-attempt protocol):
1. On error: Use systematic-debugging skill
2. If unresolved: Try alternative approach
3. After 3 failed attempts:
   - Document issue in stage architecture file (Issues section)
   - Escalate to Co-CEO Session with detailed context
   - Include: issue description, all 3 attempts, error logs, root cause hypothesis

CONSTRAINTS:
- Do NOT spawn additional agents
- Commit frequently (after each component, before final check)
- Do NOT leave uncommitted files—this is a BLOCKER
"""
)
```

## Stripe Implementation Stages

Stages implementing Stripe webhooks should use `stripe-webhook-checker`:

```bash
# After stage implementation, verify webhook coverage
stripe-webhook-checker docs/stages/stage-[NN]-*.md

# Required events to handle:
# - checkout.session.completed
# - customer.subscription.created
# - customer.subscription.updated
# - customer.subscription.deleted
# - invoice.payment_succeeded
# - invoice.payment_failed
```

## Orchestration Algorithm for Co-CEO

```
FOR EACH STAGE:

  1. PRE-STAGE GATE
     Run: detect-stage-complexity.sh
     If recommendation = single-branch:
        Use Strategy A
     Else:
        Use Strategy B

  2. READINESS CHECK
     Run: verify-stage-readiness.sh <stage-number>
     If FAILED:
        STOP—fix issues and retry
     Else:
        Proceed to step 3

  3. GIT SETUP
     If Strategy A (single-branch):
        echo "Continuing on main branch"
     Else (Strategy B):
        git checkout -b stage/[NN]-[stage-name]
        echo "Created branch for complex stage"

  4. SPAWN IMPLEMENTATION AGENT
     Launch with Kimi Task tool using template above
     Agent implements stage
     Agent commits all changes
     Agent calls verification before finishing

  5. COMPLETION GATE
     Run: verify-stage-completion.sh <stage-number> [branch]
     If FAILED:
        Identify uncommitted files
        Fix and commit missing changes
        Re-run gate
     Else:
        Proceed to step 6

  6. BRANCH CLEANUP
     If Strategy B (worktrees):
        git branch -d stage/[NN]-[stage-name]
        echo "Cleaned up stage branch"
     Else:
        No cleanup needed

  7. STATUS COMMUNICATION
     "Stage [N] complete and verified. Moving to Stage [N+1]."
     git push origin main (optional, for GitHub sync)

AFTER ALL STAGES:
  git-commit-phase.sh "6.1" "All implementation stages complete"
```

## Status Communication

**Start of Phase:**
> "Starting implementation. Detecting stage complexity and proceeding with appropriate git strategy. I'll manage branches and verify each stage completes fully."

**Between Stages:**
> "Stage [N] verified and merged to main. No uncommitted files detected. Proceeding to Stage [N+1]."

**After All Stages:**
> "All stages implemented and verified. Ready for Phase 6.2 (Security Review)."

## Helper Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `detect-stage-complexity.sh` | Analyze stages and recommend strategy | `.shared/scripts/co-ceo/detect-stage-complexity.sh --verbose` |
| `verify-stage-readiness.sh` | Pre-stage verification gate | `.shared/scripts/co-ceo/verify-stage-readiness.sh <N> --strict` |
| `verify-stage-completion.sh` | Post-stage verification & merge confirm | `.shared/scripts/co-ceo/verify-stage-completion.sh <N> [branch]` |
| `git-commit-phase.sh` | Commit phase completion | `.shared/scripts/co-ceo/git-commit-phase.sh "6.1" "All stages complete"` |

## After All Stages Complete

```bash
# Verify all stages exist and are marked complete
for i in {1..N}; do
  .shared/scripts/co-ceo/verify-stage-completion.sh $i
done

# Commit final phase completion
.shared/scripts/co-ceo/git-commit-phase.sh "6.1" "All implementation stages complete"

# Push to GitHub (optional)
git push origin main
```

## Ready for Phase 6.2

After all stages complete and verified:
- All implementation committed to main
- No uncommitted files or orphaned branches
- Ready for Phase 6.2: Security Review
