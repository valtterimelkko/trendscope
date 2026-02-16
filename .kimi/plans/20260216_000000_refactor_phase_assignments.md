---
task: "Refactor: Swap phase assignments between Kimi and GLM-5, rename entry point files"
created: "2026-02-16T00:00:00Z"
status: pending
risk_level: high
estimated_effort: large
---

## Summary

This plan outlines a major refactor to swap the phase assignments between Kimi Code CLI and GLM-5:
- **NEW**: Phases 0-4.2 → Kimi Code CLI (was GLM-5)
- **NEW**: Phases 4.3-7.1 → GLM-5 (was Kimi)

Additionally, rename the entry point files:
- KIMI.md → AGENTS.md (and KIMI_Reserve.md → AGENTS_Reserve.md)
- GLM5.md → CLAUDE.md (and GLM5_Reserve.md → CLAUDE_Reserve.md)

Update agent definitions to use real model names:
- Kimi agents: `model: kimi-k2.5`
- GLM-5 agents: `model: GLM-5`

## Analysis

### Current State
- Phases 1.2-1.5: GLM-5 (creative brand work)
- Phases 2.1-7.1: Kimi Code CLI (implementation)
- Entry points: GLM5.md, GLM5_Reserve.md, KIMI.md, KIMI_Reserve.md
- Agent folders: .glm5/agents/ (20 agents)

### Target State
- Phases 0-4.2: Kimi Code CLI (up to template selection)
- Phases 4.3-7.1: GLM-5 (template integration through completion)
- Entry points: AGENTS.md, AGENTS_Reserve.md, CLAUDE.md, CLAUDE_Reserve.md
- Agent folders: .kimi/agents/ (Kimi agents), .glm5/agents/ (GLM-5 agents)

### Files to Modify

#### Entry Point Files (Rename + Content Update)
| From | To | Changes |
|------|-----|---------|
| KIMI.md | AGENTS.md | Content for Kimi as primary agent platform |
| KIMI_Reserve.md | AGENTS_Reserve.md | Production entry for Kimi |
| GLM5.md | CLAUDE.md | Content for GLM-5 as secondary platform |
| GLM5_Reserve.md | CLAUDE_Reserve.md | Production entry for GLM-5 |

#### Process Documentation
- slimmed-strategic-co-ceo-process.md - Update phase/platform assignments
- README.md - Update architecture description
- AGENTS.md (meta-dev guide) - Update file references

#### Phase Skills (Update platform references)
All 21 phase skills in .shared/skills/co-ceo-phases/ need updates:
- Phase 0-4.2: Change platform from GLM-5/Either → Kimi
- Phase 4.3-7.1: Change platform from Kimi → GLM-5

#### Agent Definitions
- Move/rename .glm5/agents/ → .kimi/agents/ (for Kimi phases 0-4.2)
- Update agent YAML frontmatter with `model: kimi-k2.5`
- Create/keep .glm5/agents/ for GLM-5 phases 4.3-7.1
- Update agent YAML frontmatter with `model: GLM-5`

## Implementation Plan

### Step 1: Rename Entry Point Files
**Files**: KIMI.md → AGENTS.md, KIMI_Reserve.md → AGENTS_Reserve.md, GLM5.md → CLAUDE.md, GLM5_Reserve.md → CLAUDE_Reserve.md
**Description**: Rename the four main entry point files and update internal cross-references
**Expected Outcome**: All four files renamed with updated content
**Rollback**: `git mv` operations can be reversed

### Step 2: Create .kimi/agents/ Folder Structure
**Files**: Move/rename .glm5/agents/ → .kimi/agents/ 
**Description**: Create Kimi-specific agent folder and move appropriate agents there. Kimi will handle phases 0-4.2 which includes: brand-kit, marketing, UX design, technical PRD, quality gates, notion sync, user approval, infrastructure, template integration planning.
**Expected Outcome**: .kimi/agents/ folder with agents for phases 0-4.2
**Rollback**: git operations reversible

### Step 3: Update Agent Model Specifications
**Files**: All 20 agent files in .kimi/agents/ and .glm5/agents/
**Description**: 
- For .kimi/agents/*: Add `model: kimi-k2.5` to YAML frontmatter
- For .glm5/agents/*: Add `model: GLM-5` to YAML frontmatter
**Expected Outcome**: All agents specify their target model
**Rollback**: Restore from git

### Step 4: Update slimmed-strategic-co-ceo-process.md
**Files**: slimmed-strategic-co-ceo-process.md
**Description**: 
- Update dependency tree: [G] → [K] for phases 0-4.2, [K] → [G] for phases 4.3-7.1
- Update AI Platform Selection Guide table
- Update Agent Spawning by Platform section
- Update Phase Skills Reference table
**Expected Outcome**: Process file reflects new phase assignments
**Rollback**: Restore from git

### Step 5: Update Phase Skills Platform References
**Files**: All 21 phase skills in .shared/skills/co-ceo-phases/
**Description**: Update platform field in each phase skill:
- Phases 0.0, 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 3.1, 4.1, 4.2, 4.2.5: Platform → Kimi
- Phases 4.3, 4.3.5, 4.4, 5.1, 6.1, 6.2, 6.9, 7.1: Platform → GLM-5
**Expected Outcome**: All phase skills have correct platform
**Rollback**: Restore from git

### Step 6: Update README.md
**Files**: README.md
**Description**: Update hybrid architecture description and platform guide
**Expected Outcome**: README reflects new architecture
**Rollback**: Restore from git

### Step 7: Update AGENTS.md (meta-dev guide)
**Files**: AGENTS.md
**Description**: Update file references (KIMI.md → AGENTS.md, GLM5.md → CLAUDE.md)
**Expected Outcome**: Meta-dev guide has correct file references
**Rollback**: Restore from git

### Step 8: Update .glm5/skills/ References
**Files**: 7 skill files in .glm5/skills/
**Description**: Update any references to entry point files
**Expected Outcome**: Skills reference correct files
**Rollback**: Restore from git

### Step 9: Update Shared Skills References
**Files**: Various .shared/skills/ files
**Description**: Update references to entry point files and platforms
**Expected Outcome**: Shared skills have correct references
**Rollback**: Restore from git

### Step 10: Verify and Commit
**Files**: All modified files
**Description**: Run verification checks, commit all changes, push to GitHub
**Expected Outcome**: Clean commit with all changes
**Rollback**: git reset if needed

## Verification Plan

- [ ] All four entry point files exist with correct names (AGENTS.md, AGENTS_Reserve.md, CLAUDE.md, CLAUDE_Reserve.md)
- [ ] .kimi/agents/ folder exists with agents for phases 0-4.2
- [ ] .glm5/agents/ folder exists with agents for phases 4.3-7.1
- [ ] All agents have `model: kimi-k2.5` or `model: GLM-5` in frontmatter
- [ ] slimmed-strategic-co-ceo-process.md has correct phase assignments
- [ ] All phase skills have correct platform
- [ ] README.md reflects new architecture
- [ ] No references to old file names (KIMI.md, GLM5.md)
- [ ] Git status shows clean rename operations

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Broken cross-references | High | Medium | Systematic search/replace, verification step |
| Confusion during rename | Medium | Medium | Use git mv for atomic operations |
| Model specification errors | Medium | High | Review each agent file individually |
| Phase assignment mistakes | Medium | High | Double-check against dependency tree |

## Alternative Approaches Considered

### Option A: Keep current file names
**Pros**: Less disruptive, fewer file changes
**Cons**: User specifically requested AGENTS.md/CLAUDE.md naming
**Why Not Selected**: User requirement takes precedence

### Option B: One giant commit
**Pros**: Single atomic operation
**Cons**: Harder to review, higher risk
**Why Not Selected**: Breaking into steps allows verification between changes
