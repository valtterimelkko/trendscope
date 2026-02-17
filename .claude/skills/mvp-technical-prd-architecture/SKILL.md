---
name: mvp-technical-prd-architecture
description: Use when designing MVP technical architecture and writing technical PRDs. Use before implementation, after concept/UX design. Covers database schemas, API contracts, n8n workflows, Git strategies for AI agents.
---

# MVP Technical PRD & Architecture Design

## Overview

Design and document the technical architecture for an MVP SaaS/web application. Creates a Technical PRD that serves as both human alignment document and AI agent instruction set. Uses **Modular Monolith** pattern with **Supabase** (state layer) and **n8n** (logic layer).

**Core principle:** The PRD is not just documentation—it's the prompt engineering context for AI development agents. Ambiguity leads to hallucinations.

## When to Use

- After Master Concept and MVP User Experience are finalized
- Before any implementation begins
- When designing the technical approach for an MVP
- NOT for production-scale architecture (this is MVP-focused)

## Quick Reference

| Component | Role | When to Use |
|-----------|------|-------------|
| Supabase | State Layer (DB, Auth, RLS) | Always for MVP |
| n8n | Logic Layer (workflows, integrations) | When OAuth or complex async needed |
| Edge Functions | Synchronous low-latency logic | Webhook validation, fast operations |
| Modular Monolith | Architecture pattern | Default for MVP |

## The Process

### Step 1: Gather Inputs

Required files to review:
- Master Concept file
- Brand Kit & Brand Guide
- MVP User Experience file

Extract:
- Core value proposition
- Critical user journeys
- Data entities implied by UX

### Step 2: Define Steel Thread

The **Steel Thread** is the single unbroken path delivering core value.

**Separate into layers:**

| Layer | Contents | Priority |
|-------|----------|----------|
| Core Engine | Auth, DB, RLS, billing infra | Non-negotiable |
| Feature Layer | User-facing capabilities | Experimental, may pivot |

**Document Critical User Journeys (CUJs):**

```markdown
## [CUJ-01] User Registration

- **Trigger:** User clicks "Sign Up"
- **Frontend:** Submit form to Supabase Auth
- **Backend:** Auth trigger creates profile row
- **Workflow:** n8n webhook sends welcome email
- **Success:** User record in auth.users and public.users
```

### Step 3: Technical Specifications

**Database Schema:**
- Use declarative SQL definitions (not prose)
- Define RLS policies inline with tables
- Use UUID for PKs, TIMESTAMPTZ for dates
- JSONB for flexible/evolving fields
- SECURITY DEFINER functions must include `SET search_path = 'public'`; avoid SECURITY DEFINER views unless explicitly justified

See [database-patterns.md](database-patterns.md) for schemas and RLS examples.

**API Contract:**
- Define OpenAPI spec before coding
- Standardize error responses
- Enable parallel frontend/backend work

**n8n Workflow Definitions:**
- Document trigger, node sequence, failure modes
- Use Proxy Pattern for user OAuth (never store user creds in n8n)

See [n8n-patterns.md](n8n-patterns.md) for workflow patterns.

### Step 3A: Security Architecture (Supabase)

Document these **explicitly** in the PRD:
- Function classification: internal-only vs public RPC vs admin-only
- Exposure rules: which functions can be called from clients vs server-only
- SECURITY DEFINER usage policy and mandatory `SET search_path = 'public'` for any SECURITY DEFINER functions
- RLS matrix: table → policies for SELECT/INSERT/UPDATE/DELETE
- Avoid SECURITY DEFINER views; prefer SECURITY INVOKER defaults
- High-risk operations (billing/credits) require server-side enforcement (no direct RPC)

### Step 4: Git Strategy for AI Agents

Include a Git Workflow section in the PRD to guide AI agents:

**Required in PRD:**
```markdown
## X. Git Workflow for AI Agents

### Branch Naming
ai/<agent-name>/<ticket-id>/<description>
Example: ai/feat/copilot/TASK-102/calendar-sync

### Commit Strategy
- Conventional Commits (feat/fix/docs/refactor/test/chore)
- Squash-on-merge to main
- AI agents never push directly to main

### Module Assignment (Minimize Conflicts)
- Agent A: /src/auth/*, database migrations
- Agent B: /src/api/*, n8n workflows
- Agent C: /src/components/*, frontend

### Pull Request Checklist
- [ ] Tests passing
- [ ] RLS policies verified (if DB changes)
- [ ] No sensitive data exposed
- [ ] Links to PRD section implemented
```

See [git-ai-workflow.md](git-ai-workflow.md) for complete workflow patterns.

### Step 5: Write the PRD Document

Create `docs/Project-Technical-Architecture.md` with structure:

```markdown
# [Project] Technical PRD

Version: 1.0.0 | Status: Draft | Owner: [Name]
Date: YYYY-MM-DD

## 1. Executive Summary
[Core value proposition, <100 words]

## 2. Steel Thread (MVP Scope)
### 2.1 Critical User Journeys
[CUJ-01, CUJ-02, etc.]

## 3. Technical Specifications
### 3.1 Database Schema
[SQL definitions with RLS]
### 3.2 API Contract
[Endpoints, payloads, errors]
### 3.3 n8n Workflows
[Trigger, logic, failure modes]

## 4. Non-Functional Requirements
[Performance, security, scalability, API quotas]
### 4.1 Security Architecture (Supabase & Auth)
- Function classification (internal/public/admin) + RPC allowlist/denylist
- Mandatory `SET search_path = 'public'` on any SECURITY DEFINER functions; avoid SECURITY DEFINER views
- RLS policy matrix per table and ownership checks for multi-tenant data
- High-risk operations (billing/credits/feature flags) enforced server-side (no direct client RPC)
- Secrets handling (service role key server-side only)

## 5. Implementation Stages
[Ordered list of stages with dependencies]

## 6. Operations & Monitoring
[Monitoring, backups, retention policies]

## 7. Git Workflow for AI Agents
[Branch naming, commits, module assignment]

## 8. Open Questions
[Decisions pending user input]

## 9. Architecture Decision Records
[ADR-001, ADR-002, etc.]
```

### Step 6: Define Implementation Stages

**IMPORTANT - TEMPLATE-AWARE STAGING:**
Phase 4.3 (Template Integration) will deploy significant infrastructure before implementation:
- ✅ Complete frontend UI (personalized with brand and content)
- ✅ Database schema with RLS policies (via Supabase migrations)
- ✅ Authentication (Google OAuth configured)
- ✅ Stripe products/prices (billing infrastructure)
- ✅ Stripe webhook endpoint registered (but handlers need implementation)

**Therefore, focus stages on:**
- Backend API endpoint logic (connecting frontend to database)
- Stripe webhook handler implementation (subscription lifecycle events)
- Business logic and processing
- Custom integrations beyond template scope

**Do NOT plan stages for infrastructure already handled by templates:**
- "Set up authentication" → Template + Phase 4.3.4
- "Create database schema" → Template + Phase 4.3.4
- "Build frontend components" → Template + Phase 4.3.1/4.3.2
- "Create Stripe products" → Template + Phase 4.3.3

Break architecture into stages:

1. **Backend API Core** - API endpoint logic, database queries, auth middleware
2. **Stripe & Billing** - Webhook handlers, subscription management (use stripe-webhook-checker to validate)
3. **Business Logic** - Project-specific features, n8n workflows for external integrations
4. **Frontend Customization** (only if needed) - Features beyond template scope

Each stage should be:
- Independently testable
- Executable by an Agent
- 2-8 hours of autonomous work
- Focused on backend/logic, not infrastructure deployment

## AI-Native Writing Guidelines

| Do | Don't |
|----|-------|
| "Create table users with..." | "We might want a users table" |
| "RLS: Users SELECT only own rows" | "Security should be handled" |
| "Do NOT expose email in API" | [Assume agent won't expose data] |
| Link to specific sections | Write prose without structure |

**Imperative mood** - Commands, not suggestions
**Negative constraints** - State what NOT to do explicitly
**Cross-reference sections** - "(See Section 3.2: RLS Policies)"

### Negative Constraints Template

Add explicit "DO NOT" sections to guide AI agents away from common mistakes:

```markdown
### 3.1 Database Schema - Critical Constraints

**DO NOT:**
- Remove `organization_id` from WHERE clauses on tenant tables
- Use `SELECT *` without WHERE on multi-tenant tables
- Expose `private.*` tables to client code
- Store PII in JSONB `metadata` fields without encryption

### 3.3 n8n Workflows - Critical Constraints

**NEVER:**
- Store user OAuth tokens in n8n credential manager (use Proxy Pattern)
- Skip retry logic on external API calls (use 3x exponential backoff)
- Log full token strings (log only last 4 chars)
- Update job status to 'completed' if external sync failed
```

## Backend Decision Tree

```
Need OAuth for user's external services (Gmail, Drive)?
├─ Yes → Use n8n with Proxy Pattern
│         (Store tokens in Supabase, use HTTP Request node)
└─ No → Does operation need async processing?
        ├─ Yes → Use n8n (triggered by Supabase webhook)
        └─ No → Use Supabase Edge Functions or direct RPC
```

## Multi-Tenancy Pattern

All tenant-specific tables must have:
- `organization_id` column
- RLS policy checking membership

```sql
CREATE POLICY "Tenant Isolation" ON public.documents
FOR ALL USING (
  organization_id IN (
    SELECT organization_id FROM public.organization_members
    WHERE user_id = auth.uid()
  )
);
```

## Environment Strategy

| Environment | Purpose | Access |
|-------------|---------|--------|
| Local | AI agent sandbox | Supabase CLI, local n8n |
| Staging | Integration testing | Anonymized data |
| Production | Live users | CI/CD only, no direct access |

## PRD Validation Checklist

Before finalizing the PRD, verify completeness:

**Structure:**
- [ ] All 9 sections present (Executive → ADRs)
- [ ] Git Workflow section included
- [ ] Operations & Monitoring section included
- [ ] Every CUJ has clear trigger, flow, and success criteria

**Database:**
- [ ] All tables have `updated_at` trigger applied
- [ ] All `organization_id` columns indexed
- [ ] RLS enabled on all public tables
- [ ] `private.*` tables documented (if OAuth used)
- [ ] Security architecture section documents function exposure, mandatory `search_path = 'public'` on SECURITY DEFINER functions, RPC allowlist/denylist, and RLS matrix

**Cross-References:**
- [ ] CUJs reference specific workflows by name
- [ ] Security requirements reference RLS policies
- [ ] Implementation stages reference CUJs

**Negative Constraints:**
- [ ] Each technical section has "DO NOT" statements
- [ ] Security-critical operations explicitly called out

**AI Agent Readiness:**
- [ ] Module assignment defined (who works on what)
- [ ] Branch naming examples provided
- [ ] Implementation stages are independently testable

## Outputs

This skill produces:
1. `docs/Project-Technical-Architecture.md` - The Technical PRD
2. Git branch structure plan
3. Implementation stages breakdown
4. Architecture Decision Records (ADRs) for key choices

## Reference Files

For detailed patterns and examples:
- [database-patterns.md](database-patterns.md) - Schema patterns, RLS, multi-tenancy
- [n8n-patterns.md](n8n-patterns.md) - Workflow patterns, OAuth proxy
- [git-ai-workflow.md](git-ai-workflow.md) - Branching, commits, merge strategy
- [prd-template.md](prd-template.md) - Full PRD template

## Integration with Other Skills

**Before this skill:**
- Master Concept file completed
- MVP User Experience design completed
- Brand Kit finalized

**After this skill:**
- Use **writing-plans** for detailed implementation plans per stage
- Use **subagent-driven-development** or **executing-plans** for implementation
