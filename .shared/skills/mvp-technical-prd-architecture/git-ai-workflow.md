# Git Workflow for AI Development Agents

## Core Principle

AI agents are "Junior Developers" with infinite typing speed but limited architectural judgment. They should never push directly to main.

## Branch Naming Convention

```
ai/<agent-name>/<ticket-id>/<short-description>
```

| Prefix | Use Case | Example |
|--------|----------|---------|
| `feat/` | Human-led feature | `feat/user-profile-page` |
| `fix/` | Human-led bugfix | `fix/header-alignment` |
| `ai/feat/` | AI-generated feature | `ai/feat/copilot/FE-102/dashboard-widgets` |
| `ai/fix/` | AI-generated fix | `ai/fix/copilot/BUG-45/null-check` |
| `ai/refactor/` | AI code cleanup | `ai/refactor/claude/TECH-10/auth-service` |
| `ai/docs/` | AI documentation | `ai/docs/copilot/DOC-5/api-specs` |

**Why structured names:**
- Filter branches: `git branch --list 'ai/*'`
- CI rules for AI-generated code
- Auto-label PRs
- Audit trail

## The Human-in-the-Loop Workflow

```
1. Human creates detailed Issue/Ticket
   └── Links to PRD section
   └── Links to relevant ADRs
   
2. AI agent creates branch: ai/feat/...

3. AI implements on feature branch
   └── Runs local tests
   └── Commits with Conventional Commits
   
4. CI runs automated checks
   └── Linting
   └── Unit tests
   └── Security scans
   
5. Human reviews PR
   └── Focus: Logic, security, business rules
   └── (Syntax checking is AI's strength, not review focus)
   
6. Human merges to main
   └── Squash commits
```

## Commit Message Format

Use Conventional Commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation |
| `style` | Formatting (no code change) |
| `refactor` | Code restructure (no feature change) |
| `test` | Adding tests |
| `chore` | Maintenance tasks |

**Examples:**
```
feat(auth): implement JWT-based login

Add login endpoint with token generation and validation middleware.
Includes rate limiting per RFC-6585.

Closes #102
```

```
fix(reports): correct timezone handling in date filters

Use UTC timestamps consistently across report generation.
```

## Squash-on-Merge Policy

AI agents create many micro-commits. Always squash on merge to main:

```bash
# PR merge settings (GitHub/GitLab)
Merge method: Squash and merge
```

**Benefits:**
- Clean git history
- `git bisect` remains usable
- One atomic commit per feature

## Merge Conflict Resolution

**Priority order when conflicts occur:**

1. Human code wins over AI code (unless AI change is verified necessary)
2. Newer PRD requirements win over older code
3. When in doubt, preserve human architectural decisions

**For AI agents:**
- Stop and escalate merge conflicts to human
- Do not attempt automatic resolution of substantive conflicts
- Simple conflicts (import order, formatting) may be auto-resolved

## Module Assignment Strategy

Minimize conflicts by assigning AI agents to distinct modules:

```
Agent A: /src/auth/*
Agent B: /src/billing/*
Agent C: /src/projects/*
```

If agents must work on same module:
- Sequence tasks (not parallel)
- Or split by file

## Pull Request Template

```markdown
## Summary
[One sentence describing the change]

## Type
- [ ] Feature
- [ ] Bug fix
- [ ] Refactor
- [ ] Documentation

## AI Generated
- [ ] Yes - Agent: [name], Branch: [branch]
- [ ] No - Human authored

## Testing
- [ ] Unit tests added/updated
- [ ] Tested locally
- [ ] CI passing

## PRD Reference
[Link to PRD section this implements]

## Checklist
- [ ] Code follows project style
- [ ] Self-reviewed for logic errors
- [ ] No sensitive data exposed
- [ ] RLS policies verified (if DB changes)
```

## CI Pipeline for AI Code

```yaml
# Example: Stricter rules for AI branches
on:
  pull_request:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Standard checks
      - name: Lint
        run: npm run lint
        
      - name: Test
        run: npm run test
      
      # Extra checks for AI branches
      - name: Security scan (AI branches)
        if: startsWith(github.head_ref, 'ai/')
        run: npm run security-scan
        
      - name: Label PR
        if: startsWith(github.head_ref, 'ai/')
        run: gh pr edit ${{ github.event.number }} --add-label "ai-generated"
```

## Protected Branch Rules

```yaml
main:
  required_reviews: 1
  dismiss_stale_reviews: true
  require_code_owner_review: true
  restrict_pushes:
    - CI bot only
  required_status_checks:
    - lint
    - test
    - build
```

## Tag and Release Strategy

```bash
# Semantic versioning
git tag -a v1.2.0 -m "Release 1.2.0: [summary]"
git push origin v1.2.0
```

**Version bumping:**
- `feat` → minor bump (1.x.0)
- `fix` → patch bump (1.0.x)
- Breaking changes → major bump (x.0.0)

## Rollback Procedure

```bash
# Identify problematic commit
git log --oneline

# Revert (creates new commit, preserves history)
git revert <commit-hash>
git push origin main

# For emergencies only: force rollback
# (Requires elevated permissions)
```

## Agent Instructions Template

When dispatching an agent:

```markdown
## Task
[Clear description of what to build]

## Branch
Create: ai/feat/[agent]/[ticket]/[description]

## Context
- PRD Section: [link]
- Related ADRs: [links]
- Files to modify: [list]

## Constraints
- Follow TDD (test first)
- Use Conventional Commits
- Do not modify files outside scope
- Escalate if blocked

## Verification
- Tests must pass
- Lint must pass
- Self-review before PR

## On Completion
- Create PR to main
- Request human review
- Do not merge
```
