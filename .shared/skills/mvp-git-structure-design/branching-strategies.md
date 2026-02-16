# Git Branching Strategies for Multi-Stage MVPs

## VS Code Environment Constraint

**Important:** When using GLM-5 in VS Code, all spawned agents share the same working directory. This fundamentally limits true parallel execution:

- Multiple agents cannot work on different branches simultaneously (they share one working directory)
- Git worktrees don't help (agents can't be directed to work in different directories)
- Branch switching while an agent is running causes state inconsistency

**What this means for strategy selection:**
- Branch structures still provide **organizational value** (isolation, rollback, clean history)
- But branches do NOT enable **concurrent agent execution**
- The Co-CEO must orchestrate **sequential execution** with branch switching between stages
- "Parallel work" in this document refers to the **branch structure design**, not actual concurrent agent execution

For implementation details, see `slimmed-strategic-co-ceo-process.md` Phase 6.1 Git Workflow Orchestration.

## Decision Tree

Use this decision tree to choose the right branching strategy:

```
How many implementation stages?
├─ 1-2 stages
│  └─ Use: Simple Trunk-Based
│     - All work off main
│     - Direct merge when complete
│
├─ 3-4 stages
│  ├─ Are stages sequential (each depends on previous)?
│  │  └─ Yes → Use: Linear with Stage Prefixes
│  │     - All work off main
│  │     - Tag AI branches with stage number
│  │     - Complete stage N before starting N+1
│  │
│  └─ No (parallel or independent)
│     └─ Use: Stage Branches with Integration
│        - Create stage branches
│        - Use integration branch for testing
│        - Merge to main when all tests pass
│
├─ Exactly 5 stages
│  ├─ Simple/low-complexity stages?
│  │  └─ Yes → Use: Stage Branches with Integration
│  │     - Treat as extended 4-stage project
│  │
│  └─ Complex/high-conflict stages?
│     └─ Yes → Use: Modular with Integration Branches
│        - Group into logical modules
│
└─ 6+ stages
   └─ Use: Modular with Integration Branches
      - Group related stages
      - Integration branch per group
      - Phased merging to main
```

## Strategy 1: Simple Trunk-Based

**Best for:** 1-2 stages, simple MVPs, single developer/agent

### Structure

```
main (protected)
├─ ai/feat/agent1/S01-TASK-101/setup-auth
├─ ai/feat/agent2/S01-TASK-102/db-schema
├─ ai/feat/agent3/S02-TASK-201/user-api
└─ ai/feat/agent4/S02-TASK-202/admin-api
```

### Workflow

1. Create AI branch off `main` for each task
2. Implement task
3. Run tests
4. Create PR to `main`
5. Merge when approved
6. When all Stage 01 tasks merged → Stage 01 complete
7. Start Stage 02 tasks

### Branch Naming

- AI branches: `ai/<type>/<agent>/S<stage#>-<ticket>/<desc>`
- Example: `ai/feat/copilot/S01-TASK-101/supabase-auth-setup`

**⚠️ Important:** Stage prefix `S01-`, `S02-` is ONLY for trunk-based and linear strategies. Do NOT use when using stage branches (redundant since base branch already indicates stage).

### Merge Strategy

- Squash and merge to `main`
- Delete feature branch after merge
- No long-lived branches besides `main`

### Pros & Cons

**Pros:**
- Simplest to understand and manage
- No merge complexity
- Clear linear history

**Cons:**
- Stages must complete sequentially
- Can't test integration of parallel work
- Potential conflicts if stages overlap

## Strategy 2: Linear with Stage Prefixes

**Best for:** 3-4 sequential stages, low conflict risk

### Structure

```
main (protected)
├─ [Stage 01 branches - all merged]
├─ [Stage 02 branches - in progress]
│  ├─ ai/feat/agent1/S02-TASK-201/user-endpoints
│  └─ ai/feat/agent2/S02-TASK-202/auth-middleware
└─ [Stage 03 branches - not started]
```

### Workflow

1. Complete all Stage 01 tasks → merge all to `main`
2. **Verify Stage 01:** Run full test suite on `main`
3. Start Stage 02 tasks (branch off `main`)
4. Complete all Stage 02 tasks → merge all to `main`
5. **Verify Stage 02:** Run full test suite
6. Repeat for remaining stages

### Branch Naming

Same as Simple Trunk-Based: `ai/<type>/<agent>/S<stage#>-<ticket>/<desc>`

### Verification Points

After each stage completes:
```bash
# Verify all stage N tasks merged
git log --oneline --grep="S0N-" main

# Run full test suite
npm test  # or appropriate test command

# Tag the stage completion
git tag -a stage-01-complete -m "Stage 01: Core Engine complete"
```

### Pros & Cons

**Pros:**
- Clear stage boundaries
- Each stage verified before next starts
- Good for dependent stages

**Cons:**
- Strictly sequential (can't parallelize)
- Slower overall (no concurrent work)
- Stage must fully complete before next starts

## Strategy 3: Stage Branches with Integration

**Best for:** 3-4 stages that benefit from isolation, organized parallel branch structure

**Note:** "Parallel" here refers to the branch structure design. Due to VS Code constraints, actual agent execution is typically sequential. The Co-CEO switches branches between spawning agents.

### Structure

```
main (protected)
│
├─ integration/backend (integration testing)
│  │
│  ├─ stage/01-core-engine
│  │  ├─ ai/feat/agent1/TASK-101/supabase-setup
│  │  └─ ai/feat/agent2/TASK-102/rls-policies
│  │
│  └─ stage/02-api-endpoints
│     ├─ ai/feat/agent3/TASK-201/user-crud
│     └─ ai/feat/agent4/TASK-202/project-crud
│
└─ integration/frontend
   │
   └─ stage/03-ui
      └─ (human-led with AI assist)
```

### Workflow

1. **Create stage branches** off `main`:
   ```bash
   git branch stage/01-core-engine main
   git branch stage/02-api-endpoints main
   git branch integration/backend main
   ```

2. **Stage development (sequential in VS Code):**
   - Agent A works on Stage 01 tasks (branches off `stage/01-core-engine`)
   - After Agent A completes, Agent B works on Stage 02 tasks (branches off `stage/02-api-endpoints`)
   - Note: In VS Code, agents run sequentially; the branch structure provides isolation

3. **Merge to stage branches:**
   ```bash
   # Agent A completes task
   git checkout stage/01-core-engine
   git merge ai/feat/agent1/TASK-101/supabase-setup --squash
   ```

4. **Integration testing:**
   ```bash
   # When stages ready to integrate
   git checkout integration/backend
   git merge stage/01-core-engine --no-ff
   git merge stage/02-api-endpoints --no-ff

   # Run integration tests
   npm test
   ```

5. **Merge to main:**
   ```bash
   # After integration tests pass
   git checkout main
   git merge integration/backend --squash
   ```

### Branch Naming

- Stage branches: `stage/<stage#>-<name>`
- Integration branches: `integration/<group>`
- AI branches: `ai/<type>/<agent>/TASK-<#>/<desc>` (**NO** stage prefix - implied by base branch)

**⚠️ Critical:** When using stage branches, DO NOT add `S01-`, `S02-` prefixes to AI branch names. The stage is already indicated by which stage branch you branched from. Adding the prefix is redundant and confusing.

### Branch Lifecycle

| Branch Type | Base | Merge To | Lifetime | Delete When |
|-------------|------|----------|----------|-------------|
| `ai/feat/...` | Stage branch | Stage branch | Short (hours-days) | After merge |
| `stage/*` | `main` | Integration branch | Medium (days-weeks) | After integration merge |
| `integration/*` | `main` | `main` | Short (hours-days) | After main merge |

### Pros & Cons

**Pros:**
- Clean stage isolation for rollback
- Integration testing before main
- Clear organizational structure
- Isolated stage failures

**Cons:**
- More complex merge flow
- Requires Co-CEO branch orchestration
- Potential integration conflicts
- No actual parallel execution in VS Code (sequential with branch switching)

## Strategy 4: Modular with Integration Branches

**Best for:** 5+ stages, large MVPs, multiple agent teams

### Structure

```
main (protected)
│
├─ integration/core (Stages 01-02)
│  ├─ stage/01-auth
│  │  └─ ai/feat/.../...
│  └─ stage/02-database
│     └─ ai/feat/.../...
│
├─ integration/features (Stages 03-05)
│  ├─ stage/03-analytics
│  │  └─ ai/feat/.../...
│  ├─ stage/04-notifications
│  │  └─ ai/feat/.../...
│  └─ stage/05-integrations
│     └─ ai/feat/.../...
│
└─ integration/frontend (Stage 06)
   └─ stage/06-ui
      └─ ai/feat/.../...
```

### Grouping Stages

Group by:
1. **Technical layer:** Backend, frontend, workers
2. **Dependency cluster:** Core vs features vs UI
3. **Agent team assignment:** Team A = auth+db, Team B = features

### Workflow

1. **Create grouped integration branches:**
   ```bash
   git branch integration/core main
   git branch integration/features main
   git branch integration/frontend main
   ```

2. **Develop within groups:**
   - Stages 01-02 merge to `integration/core` → test → merge to `main`
   - Stages 03-05 merge to `integration/features` → test → merge to `main`
   - Stage 06 merges to `integration/frontend` → test → merge to `main`

3. **Phased integration:**
   ```bash
   # Phase 1: Core complete
   git checkout main
   git merge integration/core --squash
   git tag phase-1-core-complete

   # Phase 2: Features (depends on core)
   git checkout integration/features
   git merge main  # Get Phase 1 changes
   # ... develop features ...
   git checkout main
   git merge integration/features --squash
   git tag phase-2-features-complete

   # Phase 3: Frontend (depends on features)
   # ... similar flow ...
   ```

### Pros & Cons

**Pros:**
- Highly organized for large projects
- Clear phase boundaries
- Parallel work within phases
- Scalable to many agents/teams

**Cons:**
- Most complex strategy
- Requires careful coordination
- Longer overall timeline due to phases
- Potential for integration issues between phases

## Choosing Based on Complexity

**Note:** In VS Code, agents execute sequentially regardless of strategy. Choose based on organizational needs, not parallelization hopes.

| Project Complexity | Recommended Strategy | Why |
|--------------------|---------------------|-----|
| Simple (1-2 stages) | Simple Trunk-Based | Minimal overhead |
| Medium (3-4 sequential stages) | Linear with Prefixes | Clear stage boundaries |
| Medium (3-4 stages needing isolation) | Stage Branches | Better rollback capability |
| Complex (5+ stages) | Modular with Integration | Organized phase structure |

## Conflict Resolution Patterns

### Low Conflict Risk
- Stages touch different files
- Clear module boundaries
- → Use simpler strategies (1 or 2)

### Medium Conflict Risk
- Stages may touch shared files
- Some module overlap
- → Use Stage Branches (Strategy 3)

### High Conflict Risk
- Stages likely to conflict
- Shared files across stages
- → Use Modular with careful grouping (Strategy 4)
- → Or: Consider revising PRD to better separate stages

## Migration Between Strategies

If you start with one strategy and need to change:

### Trunk-Based → Stage Branches
```bash
# Create stage branches from main
git branch stage/01-core-engine main
git branch stage/02-api-endpoints main

# Rebase existing AI branches onto stage branches
git rebase --onto stage/01-core-engine main ai/feat/agent1/S01-TASK-101/auth
```

### Stage Branches → Modular
```bash
# Create integration branches
git branch integration/backend main

# Merge existing stage branches into integration
git checkout integration/backend
git merge stage/01-core-engine --no-ff
git merge stage/02-api-endpoints --no-ff
```

## Summary Table

| Strategy | Stages | Isolation | Complexity | Best For |
|----------|--------|-----------|------------|----------|
| Simple Trunk-Based | 1-2 | Low | Low | Small MVPs, minimal overhead |
| Linear with Prefixes | 3-4 | Medium | Low | Sequential stages, clear boundaries |
| Stage Branches | 3-4 | High | Medium | Stages needing rollback capability |
| Modular Integration | 5+ | High | High | Large MVPs, phased delivery |

**Note:** All strategies involve sequential agent execution in VS Code. "Isolation" refers to branch structure organization, not concurrent execution.
