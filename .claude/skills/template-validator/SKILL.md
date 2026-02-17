---
name: template-validator
description: Validates that MVP templates meet all integration requirements before deployment. Checks structure, content slots, brand tokens, Supabase schemas, Stripe config, auth flows, and code quality. Use after running template-scaffolding.
---

# Template Validator

## Overview

Ensure templates meet all integration requirements and quality standards before they can be used by the Co-CEO template integration skills. Validates structure, content slots, brand tokens, database schemas, payment config, authentication flows, and code quality.

**Core principle:** Templates must be integration-ready. A missing content slot breaks the copywriter skill. A missing RLS policy creates security vulnerabilities.

## When to Use

- After `template-scaffolding` skill creates templates
- After modifying any template
- Before committing template changes to git
- During template development iteration

## Pre-Requisites

```bash
# Check templates directory exists
ls -la templates/

# Expected templates:
# - templates/analytics-dashboard/
# - templates/productivity-tool/
# - templates/content-creator/
# - templates/utility-processor/
# - templates/digital-download/
```

## Validation Categories

### 0. Template Integrity Validation (BLOCKER)

**CRITICAL:** Before validating structure, verify the template has not been contaminated with features from other templates.

**Check against:** `docs/template-integrity-checklist.md`

**Validation Steps:**

1. **Verify Dashboard Pages Match Template Type:**
```bash
# For digital-download - should only have main dashboard page:
ls -la templates/digital-download/frontend/app/\(dashboard\)/dashboard/
# Expected: page.tsx only
# ❌ CONTAMINATION if: calendar/, queue/, media/, connect/, analytics/ exist

# For content-creator - should have full content suite:
ls -la templates/content-creator/frontend/app/\(dashboard\)/dashboard/
# Expected: page.tsx, queue/, calendar/, media/, connect/, analytics/

# For analytics-dashboard - should have analytics pages only:
ls -la templates/analytics-dashboard/frontend/app/\(dashboard\)/dashboard/
# Expected: page.tsx, public/ (for public dashboards)
# ❌ CONTAMINATION if: queue/, calendar/, media/, connect/ exist
```

2. **Check for Cross-Template Component Contamination:**
```bash
# Check digital-download for content-creator components:
find templates/digital-download -name "*.tsx" | xargs grep -l "RichTextEditor\|MediaUploader\|ContentCalendar\|workspace"
# Expected: no results
# ❌ CONTAMINATION if any matches found

# Check analytics-dashboard for content components:
find templates/analytics-dashboard -name "*.tsx" | xargs grep -l "RichTextEditor\|MediaUploader\|ContentCalendar"
# Expected: no results
```

3. **Verify Data Model Matches Template:**
```bash
# Digital-download should be single-user (no workspaces/teams):
grep -r "workspace\|team_member" templates/digital-download/supabase/migrations/
# Expected: no results (except in comments)

# Content-creator should have multi-tenant:
grep -r "workspace\|team_member" templates/content-creator/supabase/migrations/
# Expected: migrations defining these tables
```

4. **Check Sidebar Navigation:**
```bash
# Review sidebar to ensure navigation matches template type
grep -A 20 "const navigation" templates/{template-name}/frontend/components/dashboard/Sidebar.tsx
```

**Validation Rules:**
- [ ] Template has ONLY features listed in its feature matrix (docs/template-integrity-checklist.md)
- [ ] No dashboard pages from other templates
- [ ] No components from other templates
- [ ] Data model matches template type (single-user vs multi-tenant)
- [ ] Sidebar navigation shows only appropriate pages

**If contamination found:**
1. Remove contaminated pages/components
2. Update Sidebar.tsx to remove navigation items
3. Update data model if needed
4. Re-run this validation

### 1. Structure Validation (BLOCKER)

Every template must have the exact directory structure. Missing directories or files are blockers.

**Required Structure:**
```
templates/{template-name}/
├── manifest.json           # REQUIRED
├── README.md               # REQUIRED
├── frontend/               # REQUIRED
│   ├── package.json        # REQUIRED
│   ├── next.config.js      # REQUIRED
│   ├── tsconfig.json       # REQUIRED
│   ├── tailwind.config.js  # REQUIRED
│   ├── app/                # REQUIRED
│   │   ├── layout.tsx      # REQUIRED
│   │   ├── page.tsx        # REQUIRED
│   │   ├── (auth)/         # REQUIRED
│   │   │   ├── login/      # REQUIRED
│   │   │   ├── signup/     # REQUIRED
│   │   │   └── callback/   # REQUIRED
│   │   ├── (dashboard)/    # REQUIRED
│   │   │   ├── layout.tsx  # REQUIRED
│   │   │   ├── page.tsx    # REQUIRED
│   │   │   └── settings/   # REQUIRED
│   │   └── api/            # REQUIRED
│   │       └── stripe/     # REQUIRED
│   ├── components/         # REQUIRED
│   ├── lib/                # REQUIRED
│   │   ├── supabase/       # REQUIRED
│   │   └── stripe/         # REQUIRED
│   └── styles/             # REQUIRED
│       └── tokens.css      # REQUIRED
├── supabase/               # REQUIRED
│   ├── config.toml         # REQUIRED
│   └── migrations/         # REQUIRED
├── stripe/                 # REQUIRED
│   └── products.json       # REQUIRED
└── content/                # REQUIRED
    └── slots.json          # REQUIRED
```

**Validation Command:**
```bash
.shared/scripts/templates/check-structure.py templates/{template-name}
```

### 2. Manifest Validation (BLOCKER)

The `manifest.json` must contain all required fields:

```json
{
  "name": "string (required) - lowercase, hyphenated",
  "displayName": "string (required) - human-readable",
  "description": "string (required) - 50-200 chars",
  "version": "string (required) - semver format",
  "category": "string (required) - analytics|productivity|content",
  "techStack": {
    "frontend": "string (required)",
    "database": "string (required)",
    "auth": "string (required)",
    "payments": "string (required)"
  },
  "features": "array (required) - min 3 items",
  "brandTokens": "array (required) - CSS variable names",
  "contentSlots": "number (required) - count of slots"
}
```

**Validation Rules:**
- [ ] `name` matches directory name
- [ ] `version` follows semver (X.Y.Z)
- [ ] `category` is one of allowed values
- [ ] `techStack` has all 4 required fields
- [ ] `features` has at least 3 items
- [ ] `brandTokens` includes minimum tokens: `--color-primary`, `--font-display`
- [ ] `contentSlots` count matches actual slots in `slots.json`

### 3. Content Slots Validation (BLOCKER)

The `content/slots.json` must be valid and complete:

**Required Slot Categories:**
- [ ] `landing` - Hero headline, subheadline, CTA, features
- [ ] `dashboard` - Empty states
- [ ] `errors` - Error messages (generic, network)
- [ ] `auth` - Login/signup titles

**Validation Rules:**
- [ ] Valid JSON syntax
- [ ] All slots have `type` field
- [ ] All slots have `maxLength` field
- [ ] Array slots have `itemType` definition
- [ ] No duplicate slot keys
- [ ] Slot count matches manifest `contentSlots`

**Validation Command:**
```bash
.shared/scripts/templates/check-content-slots.py templates/{template-name}/content/slots.json
```

### 4. Brand Token Validation (BLOCKER)

The `styles/tokens.css` must define all required CSS variables:

**Required Tokens:**
```css
:root {
  /* Colors - REQUIRED */
  --color-primary: ...;
  --color-secondary: ...;
  --color-accent: ...;
  --color-background: ...;
  --color-foreground: ...;
  --color-muted: ...;
  
  /* Semantic Colors - REQUIRED */
  --color-success: ...;
  --color-warning: ...;
  --color-error: ...;
  --color-info: ...;
  
  /* Typography - REQUIRED */
  --font-display: ...;
  --font-body: ...;
  --font-mono: ...;
  
  /* Spacing Scale - REQUIRED */
  --spacing-xs: ...;
  --spacing-sm: ...;
  --spacing-md: ...;
  --spacing-lg: ...;
  --spacing-xl: ...;
  
  /* Border Radius - REQUIRED */
  --radius-sm: ...;
  --radius-md: ...;
  --radius-lg: ...;
}

/* Dark Mode - REQUIRED */
.dark {
  --color-background: ...;
  --color-foreground: ...;
  /* ... all color tokens must have dark variants */
}
```

**Validation Rules:**
- [ ] All required tokens present
- [ ] No hard-coded colors in component files (only token references)
- [ ] Dark mode variants defined
- [ ] Tokens match manifest `brandTokens` array

**Validation Command:**
```bash
.shared/scripts/templates/check-brand-tokens.py templates/{template-name}
```

### 5. Supabase Schema Validation (BLOCKER)

Migration files must be valid and complete:

**Required Tables:**
- [ ] `profiles` - User profiles extending auth.users
- [ ] `teams` - Multi-tenant support
- [ ] `team_members` - Team membership
- [ ] `customers` - Stripe customer mapping
- [ ] `subscriptions` - Subscription tracking
- [ ] Template-specific tables (varies by template)

**Required RLS Policies:**
Every table with user data MUST have Row Level Security:
```sql
ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;
CREATE POLICY "..." ON public.{table} FOR SELECT USING (...);
CREATE POLICY "..." ON public.{table} FOR INSERT WITH CHECK (...);
CREATE POLICY "..." ON public.{table} FOR UPDATE USING (...);
CREATE POLICY "..." ON public.{table} FOR DELETE USING (...);
```

**Validation Rules:**
- [ ] All migration files are valid SQL
- [ ] Migration files are numbered sequentially (00001, 00002, ...)
- [ ] RLS enabled on all user-data tables
- [ ] Foreign keys reference correct tables
- [ ] No destructive operations without safeguards
- [ ] SECURITY DEFINER functions include `SET search_path = 'public'`
- [ ] Avoid SECURITY DEFINER views; prefer SECURITY INVOKER defaults

**Validation Command:**
```bash
.shared/scripts/templates/check-supabase-schema.py templates/{template-name}/supabase/migrations/
```

### 6. Stripe Configuration Validation (WARNING)

The `stripe/products.json` must follow best practices:

**Required Structure:**
```json
{
  "products": [
    {
      "id": "string (required)",
      "name": "string (required)",
      "description": "string (required)",
      "features": ["array (required)"],
      "prices": {
        "monthly": { "amount": "number", "currency": "string" },
        "yearly": { "amount": "number", "currency": "string" }
      }
    }
  ]
}
```

**Validation Rules:**
- [ ] At least 2 products defined (free tier optional)
- [ ] Product IDs are URL-safe (lowercase, alphanumeric, hyphens)
- [ ] Prices are in cents (not dollars)
- [ ] Currency is valid ISO code
- [ ] Yearly discount is reasonable (10-30% savings)
- [ ] One product marked as `highlighted: true`

**Portal Config (`stripe/portal-config.json`):**
- [ ] Valid JSON
- [ ] Contains `features` object
- [ ] Subscription update/cancel enabled

### 7. Authentication Flow Validation (BLOCKER)

Auth implementation must be complete and secure:

**Required Files:**
- [ ] `app/(auth)/login/page.tsx` - Login page exists
- [ ] `app/(auth)/signup/page.tsx` - Signup page exists
- [ ] `app/(auth)/callback/route.ts` - OAuth callback handler
- [ ] `lib/supabase/client.ts` - Browser client
- [ ] `lib/supabase/server.ts` - Server client
- [ ] `lib/supabase/middleware.ts` - Auth middleware

**Required Auth Features:**
- [ ] Google OAuth button component exists
- [ ] Magic link email option exists
- [ ] Logout functionality implemented
- [ ] Protected routes use middleware
- [ ] Session refresh handling

**Validation Rules:**
- [ ] No hardcoded secrets in code
- [ ] Environment variables used for all keys
- [ ] Callback URL is configurable (not hardcoded)
- [ ] Error handling for auth failures

### 8. Code Quality Validation (WARNING)

TypeScript and accessibility checks:

**TypeScript:**
```bash
cd templates/{template-name}/frontend && npx tsc --noEmit
```
- [ ] No TypeScript errors
- [ ] Strict mode enabled in tsconfig.json
- [ ] No `any` types without justification

**Accessibility:**
- [ ] All interactive elements have accessible names
- [ ] Color contrast meets WCAG AA (4.5:1 for text)
- [ ] Focus states visible
- [ ] Images have alt text
- [ ] Form inputs have labels

**Linting:**
```bash
cd templates/{template-name}/frontend && npx eslint app/ components/ --max-warnings 0
```

### 9. Component Completeness (WARNING)

Template-specific components must exist:

**Analytics Template:**
- [ ] BigNumberCard component
- [ ] DateRangeController component
- [ ] BreakdownList component
- [ ] ActivityTicker component
- [ ] MetricChart component

**Productivity Template:**
- [ ] CommandPalette component
- [ ] KanbanBoard component
- [ ] SidePeek component
- [ ] RichTextEditor component
- [ ] ViewSwitcher component

**Content Template:**
- [ ] SplitComposer component
- [ ] ThreadEditor component
- [ ] CalendarGrid component
- [ ] ChannelToggle component
- [ ] PostPreview component

### 10. Integration Tests (SUGGESTION)

Key flows should have tests:

**Recommended Tests:**
- [ ] User can sign up with Google OAuth
- [ ] User can sign in with magic link
- [ ] Dashboard loads for authenticated user
- [ ] Subscription flow works
- [ ] Settings can be updated

---

## Validation Process

### Step 1: Run Structure Check

```bash
.shared/scripts/templates/validate-template.sh templates/analytics-dashboard
```

This master script runs all checks in sequence and reports:
- BLOCKERS (must fix before use)
- WARNINGS (should fix, non-blocking)
- SUGGESTIONS (nice-to-have)

### Step 2: Review Report

**Output Format:**
```markdown
# Template Validation Report

**Template:** analytics-dashboard
**Date:** 2025-12-30
**Overall Status:** ⚠️ WARNINGS (2 blockers, 3 warnings, 1 suggestion)

## ❌ Blockers (Must Fix)

### 1. Missing RLS policy on `analytics_events` table
- **Location:** supabase/migrations/00003_app_schema.sql
- **Issue:** Table has RLS enabled but no policies defined
- **Fix:** Add SELECT/INSERT policies with user_id check

### 2. Content slot count mismatch
- **Location:** content/slots.json, manifest.json
- **Issue:** Manifest says 42 slots, slots.json has 38
- **Fix:** Update manifest.contentSlots to 38

## ⚠️ Warnings (Should Fix)

### 1. No yearly discount badge
- **Location:** stripe/products.json
- **Issue:** Yearly pricing exists but no "Save X%" calculated
- **Suggestion:** Add `yearlyDiscount` field

...

## 💡 Suggestions (Optional)

### 1. Add loading skeleton for MetricChart
- Components would benefit from Suspense boundaries
```

### Step 3: Fix Issues

Address blockers first, then warnings. Re-run validation after fixes.

### Step 4: Final Verification

All templates must pass with no blockers:
```bash
.shared/scripts/templates/validate-template.sh templates/analytics-dashboard
.shared/scripts/templates/validate-template.sh templates/productivity-tool
.shared/scripts/templates/validate-template.sh templates/content-creator

# Expected: All pass with "✅ PASS" status
```

---

## Helper Scripts

Location: `.shared/scripts/templates/`

| Script | Purpose | Exit Codes |
|--------|---------|------------|
| `validate-template.sh` | Master validation runner | 0=pass, 1=warnings, 2=blockers |
| `check-structure.py` | Directory structure validation | 0=pass, 1=missing files |
| `check-content-slots.py` | Content slots JSON validation | 0=pass, 1=invalid |
| `check-brand-tokens.py` | CSS token validation | 0=pass, 1=missing tokens |
| `check-supabase-schema.py` | SQL migration validation | 0=pass, 1=invalid SQL |
| `check-stripe-config.py` | Stripe products validation | 0=pass, 1=invalid config |

---

## Severity Definitions

| Severity | Meaning | Action |
|----------|---------|--------|
| **BLOCKER** | Template cannot be used | Must fix before any integration |
| **WARNING** | Template works but has issues | Fix before production use |
| **SUGGESTION** | Improvement opportunity | Optional enhancement |

---

## Auto-Fix Rules

**Safe to auto-fix:**
- Missing trailing newlines
- Incorrect slot count in manifest (update to match)
- Formatting issues in JSON files

**Never auto-fix:**
- Missing RLS policies (security risk)
- Missing components (requires implementation)
- TypeScript errors (requires code changes)

---

## Integration Points

**Inputs:**
- Templates created by `template-scaffolding` skill
- Templates directory at `templates/`

**Outputs:**
- Validation report
- Pass/fail status for each template
- Specific fix instructions for blockers

**Used by:**
- Co-CEO before proceeding to Phase 4.4 (Template Integration)
- Developers when modifying templates

---

## Common Issues and Fixes

| Issue | Common Cause | Fix |
|-------|--------------|-----|
| Structure validation fails | Missing nested directory | Create missing dirs with proper files |
| Content slots mismatch | Added slots without updating manifest | Run `check-content-slots.py --update-manifest` |
| RLS policy missing | Forgot to add after table creation | Add policy in same migration file |
| TypeScript errors | Missing type definitions | Add proper interfaces |
| Hard-coded colors | Copied code without tokenizing | Replace with `var(--color-*)` |
| Auth callback fails | Wrong redirect URL | Use environment variable |
