# Phase 4.4 Stage Planning Stability Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Prevent Co-CEO crashes during Phase 4.4 by limiting Stage Architect agent concurrency and clarifying batching/wait steps.

**Architecture:** Documentation-only updates to Phase 4.4 orchestration instructions. No runtime code or agent logic changes; reinforce batching and completion checks in skill and process docs.

**Tech Stack:** Markdown documentation.

---

### Task 1: Update Phase 4.4 skill to batch Stage Architect launches

**Files:**
- Modify: `.shared/skills/co-ceo-phases/phase-4-4-stage-planning/SKILL.md`

**Step 1: Draft the instruction changes**

Adjust the skill to state a hard cap of 3 concurrent Stage Architect agents, instruct batching (wait for a batch to finish before starting the next), and add a short status/logging note to avoid long outputs.

**Step 2: Save and review**

Open the file and confirm the new batching guidance and status note read clearly.

**Step 3: Commit**

Use `report_progress` with a descriptive message after verification.

---

### Task 2: Align slimmed process doc with batching guidance

**Files:**
- Modify: `slimmed-strategic-co-ceo-process.md` (Phase 4.4 entry)

**Step 1: Update Phase 4.4 description**

Change the Phase 4.4 summary to note “parallel in batches of up to 3,” clarifying that batching is required despite file-level isolation.

**Step 2: Save and review**

Confirm the process table/section reflects the same batching rule as the skill.

**Step 3: Commit**

Use `report_progress` after verification to capture the change.

---

# Plan complete and saved to `docs/plans/2026-01-05-phase-4-4-stability.md`. Two execution options:
1) Subagent-Driven (this session) — dispatch fresh subagent per task using `subagent-driven-development`.
2) Parallel Session — open a new session with `executing-plans` to run tasks with checkpoints.
