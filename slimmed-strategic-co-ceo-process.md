# Co-CEO Process File (Kimi + GLM-5 Hybrid)

**AUTHORITATIVE SOURCE** for Co-CEO Session operations. This slim orchestration guide contains the process hierarchy, dependency tree, and core principles. Detailed phase instructions are in phase-specific skills.

**HYBRID ARCHITECTURE:** This meta-folder supports both **Kimi Code CLI** and **GLM-5**:
- **Phases 0-4.2**: Kimi Code CLI + Agents (concept through template selection)
- **Phases 4.3-7.1**: GLM-5 (template integration through completion)

**Important:** Load phase-specific context on demand using:
```bash
.shared/scripts/co-ceo/load-phase-context.sh <phase-id>
```

---

## AI Platform Selection Guide

| Phase Range | Platform | Model | Purpose |
|-------------|----------|-------|---------|
| **0.0 - 4.2** | **Kimi Code CLI** | **kimi-k2.5** | Concept, brand, design, planning |
| **4.3 - 7.1** | **GLM-5** | **GLM-5** | Integration, implementation, completion |

### Phase Breakdown

**Kimi (Phases 0-4.2):** Concept, brand kit, marketing, UX design, technical PRD, quality gates, Notion sync, template selection
**GLM-5 (Phases 4.3-7.1):** Template integration, security audit, stage planning, architecture check, implementation, completion

### Agent Spawning by Platform

**Kimi Code CLI (Phases 0-4.2) with `MODEL: kimi-k2.5`:**
```python
Task(
    description="Brand Kit Creator",
    subagent_name="coder",
    prompt="""
You are a Brand Designer agent...

MODEL: kimi-k2.5

INPUTS:
- docs/concept/master-concept.md

OUTPUTS:
- docs/brand/brand-kit-guide.md
"""
)
```

**GLM-5 (Phases 4.3-7.1) with `MODEL: GLM-5`:**
```python
Task(
    description="Stage Implementation Agent",
    subagent_name="coder",
    prompt="""
You are an Implementation agent...

MODEL: GLM-5

INPUTS:
- docs/stages/stage-XX-*.md

TASK:
Implement the stage following TDD principles.
"""
)
```

---

## Co-CEO Session Initialization Checklist

**BEFORE starting any MVP development process:**

### 1. Git Repository Initialization
```bash
# Check if git is initialized
git status

# If NOT initialized:
git init
git config user.email "co-ceo@meta-project.local"
git config user.name "Co-CEO Session"
git branch -M main
git add .
git commit -m "Initial project structure"
# Display: "Git repository initialized. To sync to GitHub: git remote add origin <URL>"

# If git IS initialized:
# Verify branch, display: "Git repository detected. Ready for phase progression."
```

### 2. Verify Project Structure
```bash
# Check phase completion status
.shared/scripts/co-ceo/verify-phase-completion.sh --list
```

### 3. Display Startup Message
```
Co-CEO Session initialized. Ready to orchestrate MVP development.
Current project state: [from verify-phase-completion.sh output]
Starting from: Phase [X.Y]
AI Platform: [Claude Code | Kimi Code CLI]
```

### 4. Credential Gate (Phase 0.0)
- Before Phase 1.1, run Phase 0.0 API prerequisite gate (see phase skill).
- Block progression until required API keys and Supabase PAT are confirmed.

---

## Co-CEO Core Operating Principles

These principles **OVERRIDE** all other instructions.

### 1. Dynamic Phase Loading
Instead of holding all phase details in context:
```bash
# Before starting each phase, load its context:
.shared/scripts/co-ceo/load-phase-context.sh <phase-id>

# Example:
.shared/scripts/co-ceo/load-phase-context.sh 1.2
```

### 2. Process Verification at Phase Boundaries
**MANDATORY at the start of every new phase:**
- Load the phase-specific skill using `load-phase-context.sh`
- Verify scope: What is this phase supposed to accomplish?
- Verify you (Co-CEO) are NOT doing agent work
- Check that agents you spawn have proper constraints
- Confirm git workflow is correct for this phase
- **CONFIRM AI PLATFORM**: GLM-5 for Phase 1.2-1.5, Kimi for Phase 2+

### 3. Status Communication Protocol
```
Pattern:
  1. Before spawning agent: Explain what you're about to do and why
  2. During agent work: Provide status updates every 5-10 minutes
  3. After agent completes: Summarize what was accomplished
  4. At phase boundaries: Pause and verify process adherence
  5. After commits: Encourage user to sync to GitHub
```

### 4. Scope Discipline
The Co-CEO **orchestrates**. The Co-CEO does NOT:
- Write code
- Design UX screens
- Create architecture diagrams
- Perform git operations beyond branch orchestration

The Co-CEO **DOES**:
- Launch agents with clear instructions (from phase skills)
- Verify agents complete their scope
- Commit changes using helper scripts
- Monitor escalations
- Communicate with the user

### 5. Git Workflow Discipline
Use the helper script after each phase:
```bash
.shared/scripts/co-ceo/git-commit-phase.sh "<phase-id>" "<deliverable-name>"
```

### 6. Context Window Management
- Load phase context on-demand, not all at once
- After each phase, load only the next phase's context
- If writing code or doing design work, STOP and escalate

---

## Process Dependency Tree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MVP DEVELOPMENT LIFECYCLE                            │
│                                                                               │
│  Legend: [A] = Agent-based  [U] = User conversation required                │
│           [C] = Claude Code   [K] = Kimi Code CLI                           │
│  → Load phase skill: .shared/scripts/co-ceo/load-phase-context.sh X.Y       │
└─────────────────────────────────────────────────────────────────────────────┘

Phase 0: PREREQUISITES
└── 0.0 API & Infrastructure Prerequisites [U]
    ├── Skill: phase-0-0-api-prerequisites
    └── Output: docs/api-keys-verified.json

Phase 1: CONCEPT & BRAND (KIMI for agent phases)
├── 1.1 Master Concept Refinement [U]
│   ├── Skill: phase-1-1-master-concept
│   └── Output: docs/concept/master-concept.md
├── 1.2 Brand Kit & Guide Creation [A] (→ 1.1) **[K]**
│   ├── Skill: phase-1-2-brand-kit
│   ├── Platform: Kimi (model: kimi-k2.5)
│   └── Output: docs/brand/brand-kit-guide.md
├── 1.3 Service Naming & Domain [U] (→ 1.1, 1.2)
│   ├── Skill: phase-1-3-naming-domain
│   └── Updates: master-concept.md, brand-kit-guide.md
├── 1.4 Marketing Foundation [A] SEQUENTIAL (→ 1.1, 1.2, 1.3) **[K]**
│   ├── Skill: phase-1-4-marketing-foundation (orchestrates 6 sub-agents)
│   ├── Platform: Kimi (model: kimi-k2.5)
│   └── Outputs: marketing/*.md
└── 1.5 Session Break (Optional) [U] (→ 1.4)
    ├── Skill: phase-1-5-session-break
    ├── Platform: Kimi
    ├── OPTIONAL: Offer fresh Co-CEO session with clean context
    └── Provides ready-made prompt for Phase 2 continuation

Phase 2: DESIGN (KIMI)
├── 2.1 MVP UX Design [A] (→ 1.5) **[K]**
│   ├── Skill: phase-2-1-ux-design
│   ├── Platform: Kimi (model: kimi-k2.5)
│   └── Output: docs/mvp-ux-[project].md
└── 2.2 Technical PRD & Git Structure [A] (→ 1.1, 1.2, 2.1) **[K]**
    ├── Skill: phase-2-2-technical-prd
    ├── Platform: Kimi (model: kimi-k2.5)
    └── Output: docs/Project-Technical-Architecture.md

Phase 3: QUALITY GATE #1 (KIMI)
└── 3.1 Consistency & Quality Check [A] (→ all Phase 1 & 2) **[K]**
    ├── Skill: phase-3-1-quality-gate
    ├── Platform: Kimi (model: kimi-k2.5)
    └── Validates: All Phase 1 & 2 outputs

Phase 4: SYNC & PLANNING (KIMI through 4.2.5, then GLM-5)
├── 4.1 Notion Database Building [A] (→ 3.1) **[K]**
│   ├── Skill: phase-4-1-notion-sync
│   ├── Platform: Kimi (model: kimi-k2.5)
│   └── Optional: Requires NOTION_TOKEN
├── 4.2 User Approval & Template Selection [U] (→ 4.1)
│   ├── Skill: phase-4-2-user-approval
│   ├── Platform: Kimi
│   ├── CRITICAL GATE: Requires explicit user approval
│   ├── Records selection: docs/selected-template.txt
│   ├── Available templates: analytics-dashboard, productivity-tool, content-creator, utility-processor (upload/process/download), digital-download (paid downloads)
│   └── OPTIONAL: Offer fresh Co-CEO session before implementation (switch to GLM-5)
├── 4.2.5 Infrastructure Prerequisites [U] (→ 4.2) **NEW**
│   ├── Skill: phase-4-2-5-infrastructure-prerequisites
│   ├── Platform: Kimi
│   ├── BLOCKING GATE: Must verify before deployment
│   ├── Validates: Stripe + Supabase connections
│   ├── Script: .shared/scripts/co-ceo/check-infrastructure-prerequisites.sh
│   ├── Guides user through account setup if needed
│   └── Records: docs/infrastructure-verified.json
├── 4.3 Template Integration [A] (→ 4.2.5) **[G]**
│   ├── Skill: phase-4-3-template-integration
│   ├── Platform: GLM-5 (model: GLM-5)
│   ├── Reads template from: docs/selected-template.txt
│   ├── 4.3.1: Brand Personalization (sequential)
│   ├── 4.3.2: Content Generation (sequential)
│   └── 4.3.3 & 4.3.4: Stripe + Supabase (parallel)
├── 4.3.5 Supabase Security Audit [A] **BLOCKING** (→ 4.3) **[G]**
│   ├── Skill: phase-4-3-5-supabase-security-audit
│   ├── Platform: GLM-5 (model: GLM-5)
│   ├── Runs .shared/scripts/supabase/security-audit.sh (search_path, SECURITY DEFINER, RLS)
│   └── Records: docs/supabase-security-audit.md
└── 4.4 Stage Architecture Planning [A] PARALLEL in batches of up to 3 (→ 4.3.5) **[G]**
    ├── Skill: phase-4-4-stage-planning
    ├── Platform: GLM-5 (model: GLM-5)
    └── Output: docs/stages/stage-XX-*.md

Phase 5: QUALITY GATE #2 (GLM-5)
└── 5.1 Architecture Consistency Check [A] (→ 4.4, 2.2) **[G]**
    ├── Skill: phase-5-1-architecture-check
    ├── Platform: GLM-5 (model: GLM-5)
    └── Validates: All stage architecture files

Phase 6: IMPLEMENTATION & SECURITY (GLM-5)
├── 6.2 Security Review [A] (→ 4.3.5, 5.1) **RUN BEFORE STAGE EXECUTION** **[G]**
│   ├── Skill: phase-6-2-security-review
│   ├── Platform: GLM-5 (model: GLM-5)
│   ├── Purpose: pre-implementation security gate + re-run after major changes
│   └── Output: Security findings and remediation plan
└── 6.1 Stage Execution [A] SEQUENTIAL with Hybrid Git Strategy (→ 6.2) **[G]**
    ├── Skill: phase-6-1-stage-execution
    ├── Platform: GLM-5 (model: GLM-5)
    ├── CRITICAL: Complexity-aware git workflow (simple = main branch, complex = worktrees)
    ├── Scope guardrail: implement only core MVP app features needed for deployment; do NOT build marketing/lead-magnet campaign tooling or growth automation infrastructure
    ├── Helper Scripts:
    │   ├── detect-stage-complexity.sh — Analyzes stages, recommends strategy
    │   ├── verify-stage-readiness.sh — Pre-stage verification gate
    │   └── verify-stage-completion.sh — Post-stage verification + merge confirmation
    ├── Co-CEO manages 2 verification gates between each stage
    └── Uses: TDD, systematic-debugging, verification skills
└── 6.9 Build Verification Gate [U] (→ 6.1, 6.2) **BLOCKING** **[G]**
    ├── Skill: phase-6-9-build-verification
    ├── Platform: GLM-5
    ├── Purpose: prove deployability with clean install + build + tests
    └── Output: docs/build-verification-report.md

Phase 7: COMPLETION (GLM-5)
└── 7.1 Final Validation & Handoff [U] (→ 6.1, 6.2, 6.9) **[G]**
    ├── Skill: phase-7-1-completion
    ├── Platform: GLM-5
    └── Present summary and handoff to user
```

---

## Helper Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `load-phase-context.sh` | Load phase skill content | `./load-phase-context.sh 1.2` |
| `verify-phase-completion.sh` | Check phase status | `./verify-phase-completion.sh --list` |
| `git-commit-phase.sh` | Commit with phase context | `./git-commit-phase.sh "1.1" "Master Concept"` |
| `update-project-status.sh` | Update status in PRD | `./update-project-status.sh 1.1 "Complete"` |
| `detect-stage-complexity.sh` | Analyze stages, recommend git strategy | `./detect-stage-complexity.sh --verbose` |
| `verify-stage-readiness.sh` | Pre-stage verification gate | `./verify-stage-readiness.sh <N> --strict` |
| `verify-stage-completion.sh` | Post-stage verification + merge confirm | `./verify-stage-completion.sh <N> [branch]` |

All scripts located at: `.shared/scripts/co-ceo/`

---

## Phase Skills Reference

Each phase has detailed instructions in its skill file:

| Phase | Skill Location | Mode | Platform | Model |
|-------|---------------|------|----------|-------|
| 0.0 | `.shared/skills/co-ceo-phases/phase-0-0-api-prerequisites/` | Conversational | **Kimi** | — |
| 1.1 | `.shared/skills/co-ceo-phases/phase-1-1-master-concept/` | Conversational | **Kimi** | — |
| **1.2** | `.shared/skills/co-ceo-phases/phase-1-2-brand-kit/` | **Agent** | **Kimi** | **kimi-k2.5** |
| 1.3 | `.shared/skills/co-ceo-phases/phase-1-3-naming-domain/` | Conversational | **Kimi** | — |
| **1.4** | `.shared/skills/co-ceo-phases/phase-1-4-marketing-foundation/` | **Sequential Agents** | **Kimi** | **kimi-k2.5** |
| **1.5** | `.shared/skills/co-ceo-phases/phase-1-5-session-break/` | **Conversational** | **Kimi** | — |
| 2.1 | `.shared/skills/co-ceo-phases/phase-2-1-ux-design/` | Agent | **Kimi** | **kimi-k2.5** |
| 2.2 | `.shared/skills/co-ceo-phases/phase-2-2-technical-prd/` | Agent | **Kimi** | **kimi-k2.5** |
| 3.1 | `.shared/skills/co-ceo-phases/phase-3-1-quality-gate/` | Agent | **Kimi** | **kimi-k2.5** |
| 4.1 | `.shared/skills/co-ceo-phases/phase-4-1-notion-sync/` | Agent (optional) | **Kimi** | **kimi-k2.5** |
| 4.2 | `.shared/skills/co-ceo-phases/phase-4-2-user-approval/` | Conversational | **Kimi** | — |
| 4.2.5 | `.shared/skills/co-ceo-phases/phase-4-2-5-infrastructure-prerequisites/` | Conversational (BLOCKING) | **Kimi** | — |
| 4.3 | `.shared/skills/co-ceo-phases/phase-4-3-template-integration/` | Sequential+Parallel | **GLM-5** | **GLM-5** |
| 4.3.5 | `.shared/skills/co-ceo-phases/phase-4-3-5-supabase-security-audit/` | Agent (BLOCKING) | **GLM-5** | **GLM-5** |
| 4.4 | `.shared/skills/co-ceo-phases/phase-4-4-stage-planning/` | Parallel Agents (batches of up to 3) | **GLM-5** | **GLM-5** |
| 5.1 | `.shared/skills/co-ceo-phases/phase-5-1-architecture-check/` | Agent | **GLM-5** | **GLM-5** |
| 6.2 | `.shared/skills/co-ceo-phases/phase-6-2-security-review/` | Agent (pre-implementation) | **GLM-5** | **GLM-5** |
| 6.1 | `.shared/skills/co-ceo-phases/phase-6-1-stage-execution/` | Sequential Agents | **GLM-5** | **GLM-5** |
| 6.9 | `.shared/skills/co-ceo-phases/phase-6-9-build-verification/` | Conversational (BLOCKING) | **GLM-5** | — |
| 7.1 | `.shared/skills/co-ceo-phases/phase-7-1-completion/` | Conversational | **GLM-5** | — |

---

## Model Selection Reference

All agents now use explicit model selection in their prompts:

### Kimi Agents (Phases 0-4.2)
```
MODEL: kimi-k2.5
```

### GLM-5 Agents (Phases 4.3-7.1)
```
MODEL: GLM-5
```

---

## Agent Error Protocol

All agents follow the 3-attempt protocol:
```
Attempt 1: Use systematic-debugging skill
           ↓ (if unresolved)
Attempt 2: Try alternative approach
           ↓ (if unresolved)
Attempt 3: Last attempt with fresh perspective
           ↓ (if unresolved)
ESCALATE: Document and return to Co-CEO Session
```

Escalation format is documented in each phase skill.

---

## Co-CEO Self-Verification Checklist

**Use at each phase boundary:**

### Before Each Phase:
- [ ] Loaded phase context with `.shared/scripts/co-ceo/load-phase-context.sh`
- [ ] Verified dependencies complete with `.shared/scripts/co-ceo/verify-phase-completion.sh`
- [ ] **Confirmed correct AI platform** (Kimi for 0-4.2, GLM-5 for 4.3-7.1)
- [ ] Understand phase scope (agent-based or conversational?)
- [ ] Prepared agent instructions from phase skill

### After Phase Completion:
- [ ] Agent(s) completed successfully
- [ ] All deliverables present
- [ ] Committed with `.shared/scripts/co-ceo/git-commit-phase.sh`
- [ ] Status updated (if applicable)
- [ ] Communicated to user about GitHub sync

### If Stuck:
- [ ] Reload phase context
- [ ] Am I orchestrating or executing? (Should be orchestrating)
- [ ] Check phase skill for detailed instructions
- [ ] **Verify I'm using the correct AI platform for this phase** (Kimi for 0-4.2, GLM-5 for 4.3-7.1)
- [ ] If unclear, escalate to user

---

## Production Setup Guide

When using this meta-folder for actual MVP development (not improving the meta-folder itself):

### Files to Delete
These files are for **meta-development only** (improving the meta-folder structure):
- `AGENTS_meta.md` - Guide for agents working on the meta-folder
- `AGENTS.md` - Meta-folder entry point for Kimi
- `CLAUDE.md` - Meta-folder entry point for GLM-5

### Files to Keep/Rename
Choose based on which AI platform(s) you'll use:

| Setup | Action | Result |
|-------|--------|--------|
| **Kimi + GLM-5 (recommended)** | Keep both `AGENTS_Reserve.md` AND `CLAUDE_Reserve.md` | Use Kimi for Phases 0-4.2, GLM-5 for Phases 4.3-7.1 |
| **Kimi only** | Rename `AGENTS_Reserve.md` → `AGENTS.md` | Single entry point for concept through planning |
| **GLM-5 only** | Rename `CLAUDE_Reserve.md` → `CLAUDE.md` | Single entry point for implementation |

### Quick Setup Commands

```bash
# For hybrid usage (recommended):
rm AGENTS.md CLAUDE.md AGENTS_meta.md
# Keep both AGENTS_Reserve.md and CLAUDE_Reserve.md as-is
# Use Kimi for Phases 0-4.2, switch to GLM-5 at Phase 4.3

# For Kimi-only usage:
rm AGENTS.md CLAUDE.md AGENTS_meta.md CLAUDE_Reserve.md
mv AGENTS_Reserve.md AGENTS.md

# For GLM-5-only usage:
rm AGENTS.md CLAUDE.md AGENTS_meta.md AGENTS_Reserve.md
mv CLAUDE_Reserve.md CLAUDE.md
mv KIMI_Reserve.md KIMI.md
```

### After Setup

1. Initialize git: `git init && git add . && git commit -m "Initial MVP structure"`
2. Create an Overall Concept file with your MVP idea
3. Start with Phase 0.0 or 1.1 per the dependency tree above
4. Follow the platform selection guide (Claude for 1.2-1.5, Kimi for 2+)

---

*This slim process file focuses on orchestration. Detailed agent instructions are in phase-specific skills loaded on-demand.*

*Hybrid Architecture Note: Phase 1 creative work (brand, marketing) uses GLM-5's agent spawning capabilities. Phase 2+ implementation work uses Kimi Code CLI's Task tool with complexity indicators.*
