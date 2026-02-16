# TrendScope Git Branch Structure

**Project:** TrendScope - TikTok Trend Intelligence Platform  
**Strategy:** Linear with Stage Prefixes (Sequential Development)  
**Created:** 2026-02-16

---

## 1. Overview

This branch structure uses a **linear with stage prefixes** strategy suitable for 6 sequential implementation stages. Each stage builds upon the previous, minimizing merge conflicts while providing clear separation of concerns.

**Key Characteristics:**
- All work branches off `main`
- Stage prefixes in branch names (`S01`, `S02`, etc.)
- Sequential execution (Stage N+1 starts after Stage N merges)
- Squash-on-merge to maintain clean history

---

## 2. Branch Structure Diagram

```
main (protected)
│
├── ai/feat/coder/S01-TASK-101/trend-api-crud
│   └── [Stage 01: Backend API Core]
│   └── MERGE → main
│
├── ai/feat/coder/S02-TASK-201/stripe-webhook-handlers
│   └── [Stage 02: Stripe Integration]
│   └── MERGE → main
│
├── ai/feat/coder/S03-TASK-301/tiktok-scraper-producer
│   └── [Stage 03: Scraper Integration]
│   └── MERGE → main
│
├── ai/feat/coder/S04-TASK-401/trend-detection-engine
│   └── [Stage 04: Trend Detection]
│   └── MERGE → main
│
├── ai/feat/coder/S05-TASK-501/alert-pipeline
│   └── [Stage 05: Alert Delivery]
│   └── MERGE → main
│
└── ai/feat/coder/S06-TASK-601/monitoring-observability
    └── [Stage 06: Monitoring]
    └── MERGE → main
```

---

## 3. Branch Types

| Type | Pattern | Base | Merge Target | Purpose |
|------|---------|------|--------------|---------|
| **Main** | `main` | - | - | Production-ready code |
| **Feature** | `ai/feat/<agent>/S<stage>-<ticket>/<desc>` | `main` | `main` | New features |
| **Fix** | `ai/fix/<agent>/S<stage>-<ticket>/<desc>` | `main` | `main` | Bug fixes |
| **Docs** | `ai/docs/<agent>/<ticket>/<desc>` | `main` | `main` | Documentation |

---

## 4. Stage-to-Branch Mapping

| Stage | Name | Duration | Dependencies | Base Branch | AI Branch Pattern |
|-------|------|----------|--------------|-------------|-------------------|
| 01 | Backend API Core | 6-8 hrs | None | `main` | `ai/feat/coder/S01-*/desc` |
| 02 | Stripe Webhooks | 4-6 hrs | Stage 01 | `main` | `ai/feat/coder/S02-*/desc` |
| 03 | Scraper Integration | 8-10 hrs | Stage 01 | `main` | `ai/feat/coder/S03-*/desc` |
| 04 | Trend Detection | 8-10 hrs | Stage 03 | `main` | `ai/feat/coder/S04-*/desc` |
| 05 | Alert Pipeline | 6-8 hrs | Stage 02, 04 | `main` | `ai/feat/coder/S05-*/desc` |
| 06 | Monitoring | 4-6 hrs | Stage 03, 05 | `main` | `ai/feat/coder/S06-*/desc` |

---

## 5. Merge Flow

```
Stage 01: Backend API Core
    │
    ▼
MERGE to main
    │
    ▼
Stage 02: Stripe Webhooks ──────┐
    │                           │
    ▼                           │
MERGE to main                   │
    │                           │
    ▼                           │
Stage 03: Scraper Integration   │
    │                           │
    ▼                           │
MERGE to main                   │
    │                           │
    ▼                           │
Stage 04: Trend Detection       │
    │                           │
    ▼                           │
MERGE to main                   │
    │                           │
    ▼                           ▼
Stage 05: Alert Pipeline (needs 02 + 04)
    │
    ▼
MERGE to main
    │
    ▼
Stage 06: Monitoring
    │
    ▼
MERGE to main
```

---

## 6. Stage Sequencing

### Stage 01: Backend API Core
- **Parallel:** Can start immediately
- **Next:** Stage 02, Stage 03 can start after merge
- **Files:** `/backend/app/api/*`, `/backend/app/services/database.py`

### Stage 02: Stripe Webhooks
- **Depends on:** Stage 01 (database layer)
- **Parallel with:** Stage 03 (no file overlap)
- **Next:** Stage 05 (needs billing for tier-based alerts)
- **Files:** `/backend/app/api/webhooks/*`, `/backend/app/services/billing.py`

### Stage 03: Scraper Integration
- **Depends on:** Stage 01 (API structure)
- **Parallel with:** Stage 02 (different directories)
- **Next:** Stage 04 (needs scraper data), Stage 06 (needs metrics)
- **Files:** `/scraper/*`

### Stage 04: Trend Detection
- **Depends on:** Stage 03 (scraper produces data)
- **Parallel:** None (hard dependency)
- **Next:** Stage 05 (needs trends to alert on)
- **Files:** `/backend/app/services/trend_detector.py`

### Stage 05: Alert Pipeline
- **Depends on:** Stage 02 (billing/tier data), Stage 04 (trends to alert on)
- **Parallel:** None (requires both dependencies)
- **Next:** Stage 06 (needs alert metrics)
- **Files:** `/backend/app/services/alert_pipeline.py`

### Stage 06: Monitoring
- **Depends on:** Stage 03 (scraper metrics), Stage 05 (alert metrics)
- **Parallel:** None
- **Next:** None (final stage)
- **Files:** `/backend/app/monitoring/*`

---

## 7. Branch Protection Rules

### `main` Branch

```yaml
Protection Rules:
  - Require pull request reviews before merging: 1
  - Dismiss stale PR approvals when new commits are pushed: true
  - Require status checks to pass before merging:
      - pytest (unit tests)
      - ruff (linting)
      - mypy (type checking)
  - Require branches to be up to date before merging: true
  - Restrict pushes that create files larger than 100MB: true
  - Do not allow bypassing the above settings: true
```

### AI Feature Branches

- No direct push restrictions
- Status checks recommended but not required
- Force push allowed for agent experimentation

---

## 8. Git Commands Reference

### Starting a New Stage

```bash
# Ensure you're on main and up to date
git checkout main
git pull origin main

# Create feature branch for Stage 01
git checkout -b ai/feat/coder/S01-TASK-101/trend-api-crud

# Work on feature...
# ...

# Push branch
git push -u origin ai/feat/coder/S01-TASK-101/trend-api-crud
```

### Creating PR and Merging

```bash
# After pushing feature branch, create PR via GitHub/GitLab
# PR title format: "[S01] Backend API Core - Trend CRUD endpoints"

# After PR approval, squash merge to main
git checkout main
git pull origin main

# Delete local branch
git branch -d ai/feat/coder/S01-TASK-101/trend-api-crud
```

### Starting Next Stage (After Merge)

```bash
# Stage 02 can start after Stage 01 merges to main
git checkout main
git pull origin main

# Create Stage 02 branch
git checkout -b ai/feat/coder/S02-TASK-201/stripe-webhook-handlers
```

### Handling Conflicts

```bash
# If conflict during merge
git checkout main
git pull origin main
git checkout ai/feat/coder/S01-TASK-101/trend-api-crud
git rebase main

# Resolve conflicts...
git add .
git rebase --continue
git push --force-with-lease
```

---

## 9. Conflict Resolution Strategy

### Expected Conflict Areas

| Area | Stages | Mitigation |
|------|--------|------------|
| Database migrations | All stages | Sequential numbering (001_, 002_, etc.) |
| API routes | Stage 01, 02, 05 | Different route prefixes |
| Service layer | Stage 04, 05 | Clear module boundaries |
| Dependencies | All stages | Pin versions in requirements.txt |

### Conflict Resolution Priority

1. **Database migrations:** Always keep both, rename if numbering conflicts
2. **API routes:** Merge both route definitions
3. **Service imports:** Add all required imports
4. **Tests:** Keep all tests, ensure they pass

---

## 10. CI/CD Integration

### GitHub Actions Workflow

```yaml
name: CI

on:
  push:
    branches: [main, 'ai/**']
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Lint
        run: ruff check .
      
      - name: Type check
        run: mypy backend/
      
      - name: Test
        run: pytest --cov=backend --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 11. Automation Scripts

### Create Branch Structure Script

```bash
#!/bin/bash
# scripts/create-branch-structure.sh
# Usage: ./create-branch-structure.sh

set -e

STAGES=(
    "S01-TASK-101/trend-api-crud"
    "S02-TASK-201/stripe-webhook-handlers"
    "S03-TASK-301/tiktok-scraper-producer"
    "S04-TASK-401/trend-detection-engine"
    "S05-TASK-501/alert-pipeline"
    "S06-TASK-601/monitoring-observability"
)

echo "Creating TrendScope feature branches..."

# Ensure on main
git checkout main
git pull origin main

# Create feature branches
for stage in "${STAGES[@]}"; do
    branch="ai/feat/coder/$stage"
    echo "Creating branch: $branch"
    git branch "$branch" main
done

echo ""
echo "Branches created:"
git branch --list 'ai/feat/coder/S*'
echo ""
echo "To push all branches: git push origin 'ai/feat/coder/S*'"
```

### Stage Completion Script

```bash
#!/bin/bash
# scripts/complete-stage.sh
# Usage: ./complete-stage.sh S01

STAGE=$1

if [ -z "$STAGE" ]; then
    echo "Usage: ./complete-stage.sh S01"
    exit 1
fi

# Find current branch for stage
current_branch=$(git branch --show-current)

echo "Completing stage: $STAGE"
echo "Current branch: $current_branch"

# Push changes
git push origin "$current_branch"

echo ""
echo "Next steps:"
echo "1. Create Pull Request on GitHub/GitLab"
echo "2. Get code review approval"
echo "3. Squash merge to main"
echo "4. Run: git checkout main && git pull origin main"
echo "5. Create next stage branch"
```

---

## 12. Module Assignment

### Agent Responsibilities

| Agent | Primary Module | Secondary | Stages |
|-------|---------------|-----------|--------|
| **Agent 1** | `/backend/app/api/*` | `/backend/app/services/database.py` | S01 |
| **Agent 2** | `/backend/app/api/webhooks/*` | `/backend/app/services/billing.py` | S02 |
| **Agent 3** | `/scraper/*` | - | S03 |
| **Agent 4** | `/backend/app/services/trend_detector.py` | `/backend/app/services/velocity_engine.py` | S04 |
| **Agent 5** | `/backend/app/services/alert_pipeline.py` | `/backend/app/services/*_service.py` | S05 |
| **Agent 6** | `/backend/app/monitoring/*` | `/backend/app/api/health.py` | S06 |

### Directory Ownership

| Directory | Owner | Description |
|-----------|-------|-------------|
| `/backend/app/api/v1/` | Agent 1 | REST API endpoints |
| `/backend/app/api/webhooks/` | Agent 2 | Webhook handlers |
| `/backend/app/services/` | Agents 1, 2, 4, 5 | Business logic |
| `/scraper/` | Agent 3 | TikTok scraper |
| `/backend/app/monitoring/` | Agent 6 | Observability |
| `/backend/app/models/` | Shared | Pydantic models |
| `/backend/migrations/` | Shared | Database migrations |

---

## 13. Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Use For | Example |
|------|---------|---------|
| `feat` | New features | `feat(api): add trend filtering by niche` |
| `fix` | Bug fixes | `fix(scraper): handle rate limit errors` |
| `docs` | Documentation | `docs(api): add OpenAPI spec` |
| `test` | Tests | `test(detection): add velocity unit tests` |
| `refactor` | Code restructuring | `refactor(db): optimize trend queries` |
| `chore` | Maintenance | `chore(deps): update requirements.txt` |

### Scopes

| Scope | Description |
|-------|-------------|
| `api` | API endpoints |
| `db` | Database queries/models |
| `scraper` | TikTok scraper |
| `detection` | Trend detection |
| `alerts` | Alert pipeline |
| `billing` | Stripe integration |
| `auth` | Authentication |

### Examples

```
feat(api): add paginated trend list endpoint

Implement cursor-based pagination for /api/v1/trends
with filtering by status and niche.

Closes TASK-101
```

```
fix(scraper): add exponential backoff for rate limits

Use tenacity library to retry failed requests with
exponential backoff. Prevents IP blocks during
high-traffic periods.

Fixes TASK-301
```

---

## 14. Checklists

### Before Starting a Stage

- [ ] Previous stage merged to `main` (if applicable)
- [ ] Pulled latest `main`
- [ ] Created feature branch with correct naming
- [ ] Read relevant PRD section
- [ ] Understood module boundaries

### Before Creating PR

- [ ] All tests passing (`pytest`)
- [ ] Linting passing (`ruff check .`)
- [ ] Type checking passing (`mypy backend/`)
- [ ] No sensitive data in code
- [ ] Branch is up to date with `main`
- [ ] Commits follow conventional format

### PR Review Checklist

- [ ] Code follows project patterns
- [ ] RLS policies correct (if DB changes)
- [ ] API documented (if new endpoints)
- [ ] Error handling appropriate
- [ ] No hardcoded credentials
- [ ] Tests cover new functionality

---

## 15. Troubleshooting

### Common Issues

**Q: Branch naming conflict (stage already exists)**  
A: Use task number suffix: `ai/feat/coder/S01-TASK-102/additional-endpoints`

**Q: Merge conflict in migrations**  
A: Rename migration files to maintain sequence: `001_initial.py`, `002_add_trends.py`, etc.

**Q: Need to fix bug in already-merged stage**  
A: Create fix branch: `ai/fix/coder/S01-TASK-150/trend-query-fix`

**Q: Two stages need same file changes**  
A: Coordinate through main branch - complete first stage, merge, then start second

---

## 16. Summary

| Item | Value |
|------|-------|
| **Total Stages** | 6 |
| **Strategy** | Linear with Stage Prefixes |
| **Base Branch** | `main` |
| **Merge Strategy** | Squash merge |
| **Branch Pattern** | `ai/feat/coder/S<stage>-<ticket>/<desc>` |
| **Parallel Stages** | 01 & 02 can be parallel (different directories) |
| **Expected Duration** | 36-48 hours total |

---

*Generated from Technical PRD Section 7*  
*Last Updated: 2026-02-16*
