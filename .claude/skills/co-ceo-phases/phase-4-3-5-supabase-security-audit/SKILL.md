---
name: phase-4-3-5-supabase-security-audit
description: Co-CEO Phase 4.3.5 - Run a blocking Supabase database security audit immediately after migrations deploy. Halts progression if search_path/RLS/security-definer issues are found.
---

# Phase 4.3.5: Supabase Post-Deployment Security Audit

**Mode:** Agent  
**Skill to use:** `supabase-security-audit`  
**Model:** Opus (security-critical)  
**Depends on:** Phase 4.3 complete (Supabase deployed)

## Status Communication

Announce:
> "Running Supabase post-deployment security audit (search_path, SECURITY DEFINER, RLS). This is a **blocking gate**—we will not proceed until it passes."

## Agent Instructions

```
You are a Supabase Security Auditor. Use the supabase-security-audit skill.

TASK:
1) Run ./.shared/scripts/supabase/security-audit.sh
2) If the script fails, fix the reported issues or document the blockers.
3) Save the report to docs/supabase-security-audit.md (script does this).
4) Only mark phase complete when audit passes with exit code 0.

INPUTS:
- Linked Supabase project (same one used in 4.3.4)
- templates/[selected]/supabase/migrations already applied

CONSTRAINTS:
- Do NOT proceed to Phase 4.4 or implementation if audit fails.
- Escalate with exact failing queries and file paths if fixes exceed 3 attempts.
```

## Completion Criteria

- [ ] `.shared/scripts/supabase/security-audit.sh` executed
- [ ] `docs/supabase-security-audit.md` present with PASS status
- [ ] No SECURITY DEFINER functions missing `SET search_path = 'public'`
- [ ] All public tables have RLS enabled
- [ ] Any lint ERROR/WARNING findings resolved or escalated

## After Agent Completes

```bash
.shared/scripts/co-ceo/git-commit-phase.sh "4.3.5" "Supabase security audit complete"
```

## Verify

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 4.3.5
```
