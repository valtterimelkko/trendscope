# Technical PRD Template

Copy and customize this template for your MVP project.

---

# [Product Name] Technical PRD

**Version:** 1.0.0 | **Status:** Draft | **Owner:** [Name]  
**Date:** YYYY-MM-DD  
**Related Epics:** [Links to issues/tickets]

---

## 1. Executive Summary

[One paragraph, max 100 words. Core value proposition and what makes this MVP viable.]

**Target Users:** [Primary user personas]

**Success Metric:** [One measurable outcome for MVP validation]

---

## 2. Steel Thread (MVP Scope)

### 2.1 Core Engine (Non-Negotiable)

| Component | Description | Status |
|-----------|-------------|--------|
| Authentication | Supabase Auth with email/password | Planned |
| Database | PostgreSQL via Supabase | Planned |
| Row Level Security | Tenant isolation on all tables | Planned |
| Organization Model | Multi-tenant with roles | Planned |

### 2.2 Feature Layer (MVP Features)

| Feature | Priority | Dependency |
|---------|----------|------------|
| [Feature 1] | P0 - Required | Core Engine |
| [Feature 2] | P0 - Required | Feature 1 |
| [Feature 3] | P1 - Nice to have | Feature 1 |

### 2.3 Critical User Journeys

#### [CUJ-01] User Registration & Onboarding

- **Trigger:** User clicks "Sign Up"
- **Frontend:** Submit email/password to Supabase Auth
- **Backend:** 
  - Auth trigger creates row in `public.profiles`
  - Auth trigger creates org and membership for solo user
- **Workflow (n8n):** Webhook sends welcome email
- **Success Criteria:** 
  - User record exists in `auth.users`
  - Profile exists in `public.profiles`
  - Organization exists with user as owner

#### [CUJ-02] [Primary Action Name]

- **Trigger:** [User action]
- **Frontend:** [API call or Supabase query]
- **Backend:** [Database operations]
- **Workflow (n8n):** [If async processing needed]
- **Success Criteria:** [Measurable outcome]

#### [CUJ-03] [Secondary Action Name]

[Same format as above]

---

## 3. Technical Specifications

### 3.1 Database Schema

#### Table: `public.organizations`

```sql
CREATE TABLE public.organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  tier TEXT DEFAULT 'free' CHECK (tier IN ('free', 'pro')),
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "org_member_read" ON public.organizations
FOR SELECT USING (
  id IN (SELECT organization_id FROM public.organization_members WHERE user_id = auth.uid())
);
```

#### Table: `public.organization_members`

```sql
CREATE TABLE public.organization_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(organization_id, user_id)
);

CREATE INDEX idx_org_members_user ON public.organization_members(user_id);
ALTER TABLE public.organization_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "member_read_own" ON public.organization_members
FOR SELECT USING (user_id = auth.uid());
```

#### Table: `public.profiles`

```sql
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profile_read_own" ON public.profiles
FOR SELECT USING (id = auth.uid());

CREATE POLICY "profile_update_own" ON public.profiles
FOR UPDATE USING (id = auth.uid());
```

#### Table: `public.{your_entity}` (Template)

```sql
-- TEMPLATE: Replace {your_entity} with your domain-specific table name
-- Example: projects, documents, tasks, etc.

CREATE TABLE public.{your_entity} (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
  -- Add your domain-specific fields here
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_{your_entity}_org ON public.{your_entity}(organization_id);
ALTER TABLE public.{your_entity} ENABLE ROW LEVEL SECURITY;

CREATE POLICY "tenant_isolation" ON public.{your_entity}
FOR ALL USING (
  organization_id IN (
    SELECT organization_id FROM public.organization_members WHERE user_id = auth.uid()
  )
);
```

### 3.2 API Contract

**Base URL:** `/api/v1`

#### POST /api/v1/[resource]

**Purpose:** Create a new [resource]

**Request:**
```json
{
  "name": "string (required)",
  "description": "string (optional)"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "name": "string",
  "created_at": "ISO8601"
}
```

**Errors:**
| Code | Condition | Response |
|------|-----------|----------|
| 400 | Invalid input | `{"error": "name is required"}` |
| 401 | Not authenticated | `{"error": "unauthorized"}` |
| 403 | Not authorized for org | `{"error": "forbidden"}` |

#### GET /api/v1/[resource]/{id}

[Same format]

### 3.3 n8n Workflow Definitions

#### Workflow: User Onboarding

- **Trigger:** Webhook POST `/webhooks/user-created`
- **Payload:** `{ "user_id": "uuid", "email": "string" }`
- **Logic:**
  1. Validate webhook signature
  2. Fetch user profile from Supabase
  3. Add user to email marketing list (if consented)
  4. Send welcome email via Resend/SendGrid
  5. Log completion to `audit_logs`
- **Failure Modes:**
  - Email service down: Retry 3x, then log for manual follow-up
  - Invalid user_id: Log error, do not retry

#### Workflow: [Async Process Name]

[Same format]

---

## 4. Non-Functional Requirements

### 4.1 Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (p95) | < 500ms | Supabase dashboard |
| Page Load Time | < 3s | Lighthouse |
| Database Queries | < 50ms | RLS-optimized |

### 4.2 Security

- [ ] All tables have RLS enabled
- [ ] No PII in application logs
- [ ] Storage buckets private by default
- [ ] Service role key never in client code
- [ ] HTTPS only

### 4.3 Scalability

- **Target:** 1,000 concurrent users for MVP
- **Approach:** Serverless (Supabase) + queue-based async (n8n)
- **Bottleneck Watch:** RLS policy performance on large tables

---

## 5. Implementation Stages

### Stage 1: Core Engine (Autonomous)
- Database schema and migrations
- RLS policies
- Auth configuration
- Profile trigger

**Estimated:** 4-6 hours  
**Dependencies:** None  
**Testable Output:** User can sign up, profile created automatically

### Stage 2: Backend Features (Autonomous)
- API endpoints for [domain entities]
- n8n workflows setup
- Webhook integrations

**Estimated:** 6-8 hours  
**Dependencies:** Stage 1  
**Testable Output:** Full CRUD via API

### Stage 3: Frontend - Landing (User Collaboration)
- Landing page design and implementation
- Sign up / login flows
- Marketing copy integration

**Estimated:** 4-6 hours  
**Dependencies:** Stage 1  
**Testable Output:** User can access and sign up

### Stage 4: Frontend - Dashboard (User Collaboration)
- Authenticated user interface
- [Domain entity] management UI
- Settings page

**Estimated:** 8-12 hours  
**Dependencies:** Stage 2, Stage 3  
**Testable Output:** User can perform primary actions

---

## 6. Operations & Monitoring

### 6.1 Monitoring Strategy

| What | Tool | Alert Threshold |
|------|------|-----------------|
| n8n workflow failures | Slack/Email | Any failure |
| API quota usage | Custom dashboard | > 80% daily quota |
| RLS policy errors | Sentry | Any 403 error spike |
| Database performance | Supabase dashboard | Query time p95 > 500ms |

### 6.2 Backup & Recovery

- **Database:** Supabase automatic daily backups (7-day retention for free, 30-day for pro)
- **Workflows:** n8n workflows exported to Git on every change (via CI/CD)
- **Secrets:** OAuth tokens NOT backed up (users re-authenticate on restore)
- **Recovery Time Objective (RTO):** 4 hours for MVP

### 6.3 Data Retention

| Data Type | Retention Policy | Reason |
|-----------|------------------|--------|
| Soft-deleted records | 30 days | Allow user recovery |
| Completed async jobs | 7 days | Debugging, audit |
| Failed async jobs | 30 days | Analysis, retry |
| Audit logs | 90 days (free), 1 year (pro) | Compliance |

---

## 7. Open Questions / Decisions Needed

| Question | Options | Decision | Date |
|----------|---------|----------|------|
| Email provider? | Resend, SendGrid | TBD | |
| Rate limits for API? | 100/min, 1000/min | TBD | |
| Free tier limits? | [Options] | TBD | |

---

## 8. Architecture Decision Records (ADRs)

### ADR-001: Use Supabase over Firebase

**Status:** Accepted  
**Date:** YYYY-MM-DD

**Context:** Need a BaaS for MVP with good PostgreSQL support.

**Decision:** Use Supabase.

**Consequences:**
- (+) Native PostgreSQL with full SQL capability
- (+) Built-in RLS for security
- (-) Smaller ecosystem than Firebase

### ADR-002: [Next Decision]

[Same format]

---

## 9. Glossary

| Term | Definition |
|------|------------|
| Steel Thread | The minimal end-to-end path that delivers core value |
| RLS | Row Level Security - database-level access control |
| CUJ | Critical User Journey - documented user flow |
| Tenant | An organization in multi-tenant SaaS |
