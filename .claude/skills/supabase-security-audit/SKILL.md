---
name: supabase-security-audit
description: Use after Supabase migrations are deployed to run mandatory database security checks (search_path immutability, SECURITY DEFINER misuse, and RLS enablement). Blocks implementation until issues are resolved.
---

# Supabase Security Audit

## Overview

Run a **blocking** database security audit immediately after deploying Supabase migrations. This catches structural issues (missing `SET search_path`, SECURITY DEFINER misuse, missing RLS) before any implementation work begins.

## When to Use

- After Phase 4.3.4 (Supabase deployment) and before any stage planning or execution
- Whenever migrations are modified
- Before handing off to implementation agents

## Inputs

- Linked Supabase project (or `SUPABASE_PROJECT_REF` + `SUPABASE_ACCESS_TOKEN` configured)
- Template migrations already applied

## What to Run

```bash
# Run the automated audit (writes docs/supabase-security-audit.md)
./.shared/scripts/supabase/security-audit.sh
```

### What the script checks
- **Supabase DB lint** output for errors/warnings
- **SECURITY DEFINER functions** missing `SET search_path = 'public'`
- **Public tables with RLS disabled**

If the script exits non-zero, treat it as a **blocker**.

## Manual Verification (if automation fails)

Run these queries via Supabase CLI:

```bash
# SECURITY DEFINER functions missing immutable search_path
npx supabase db remote query "
SELECT n.nspname || '.' || p.proname AS function_name
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.prosecdef = true
  AND (
    p.proconfig IS NULL OR
    NOT EXISTS (SELECT 1 FROM unnest(p.proconfig) conf WHERE conf ~* '^[[:space:]]*search_path[[:space:]]*=[[:space:]]*\"?public\"?[[:space:]]*$')
  )
ORDER BY 1;
"

# Public tables without RLS
npx supabase db remote query "
SELECT tablename FROM pg_tables
WHERE schemaname = 'public' AND rowsecurity = false
ORDER BY tablename;
"
```

## Fix Patterns

- **Missing search_path on SECURITY DEFINER function**  
  ```sql
  CREATE OR REPLACE FUNCTION public.fn(...)
  RETURNS ...
  SET search_path = 'public'
  LANGUAGE plpgsql
  SECURITY DEFINER
  AS $$ ... $$;
  ```
- **Avoid SECURITY DEFINER views** unless absolutely required; prefer SECURITY INVOKER (default).
- **RLS disabled**: `ALTER TABLE public.<table> ENABLE ROW LEVEL SECURITY;` then add SELECT/INSERT/UPDATE/DELETE policies.

## Outputs

- `docs/supabase-security-audit.md` capturing lint output, failing queries, and pass/fail status
- A **pass** (exit 0) is required before moving to implementation

## Completion Criteria

- [ ] Audit script executed and report saved
- [ ] No SECURITY DEFINER functions missing immutable `search_path`
- [ ] No public tables with RLS disabled
- [ ] Lint shows no ERROR findings
- [ ] Blocking issues resolved or escalated before proceeding
