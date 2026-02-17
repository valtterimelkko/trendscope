---
name: phase-0-0-api-prerequisites
description: Co-CEO pre-phase gate to verify required API keys and Supabase PAT are present before starting Phase 1. Blocks progression until credentials are confirmed.
---

# Phase 0.0: API & Infrastructure Prerequisites

**Mode:** Conversational with main user  
**Model:** Opus (Co-CEO Session)  
**Depends on:** None (runs before Phase 1.1)

## Purpose

Block progression until all required credentials exist locally or in the expected global Supabase config. Ensures later phases (domain search, browserless scraping, Stripe, Google Ads, Supabase) can run without stopping.

## Credentials to Verify

- `.env` contains (non-empty):
  - `PORKBUN_API_KEY`
  - `PORKBUN_API_SECRET`
  - `BROWSERLESS_API_KEY`
  - `STRIPE_SECRET_KEY`
  - `STRIPE_PUBLISHABLE_KEY`
  - `GOOGLE_ADS_DEVELOPER_TOKEN`
- Supabase Management PAT configured at `/etc/supabase/config.conf` (no project required yet)
- Supabase saved projects file exists (may be empty): `/etc/supabase/projects.json`

## Status Communication

Announce:
> "Phase 0.0: Verifying required API keys and Supabase PAT before starting Master Concept. We pause here until everything is set."

## Process

1. **Load environment variables**
   - Read `.env` and `.env.local` if present (never print full secrets).
   - Confirm each required key is non-empty; for missing keys, pause and request the user to add them, showing examples only.

2. **Supabase PAT check**
   - Confirm `/etc/supabase/config.conf` exists and contains `SUPABASE_ACCESS_TOKEN`. If missing, instruct the user to create a PAT at https://supabase.com/dashboard/account/tokens and save it to that file (with `chmod 600`).
   - Confirm `/etc/supabase/projects.json` exists (create empty `{}` if absent; do not write secrets into the repo).

3. **Record verification**
   - Create/update `docs/api-keys-verified.json`:
     ```bash
     mkdir -p docs
     cat > docs/api-keys-verified.json <<'EOF'
     {
       "phase": "0.0",
       "verified_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
       "env_keys": ["PORKBUN_API_KEY","PORKBUN_API_SECRET","BROWSERLESS_API_KEY","STRIPE_SECRET_KEY","STRIPE_PUBLISHABLE_KEY","GOOGLE_ADS_DEVELOPER_TOKEN"],
       "supabase_pat": true,
       "notes": "Values stored outside git; only presence was verified."
     }
     EOF
     ```
   - Add the file to git.

4. **Gate**
   - If any key or PAT is missing, STOP and do not proceed to Phase 1.1.
   - Once all are present and `docs/api-keys-verified.json` is written, announce readiness to start Phase 1.1.

## Completion Criteria

- [ ] All required `.env` keys confirmed present (without revealing values)
- [ ] Supabase PAT present at `/etc/supabase/config.conf`
- [ ] `docs/api-keys-verified.json` created
- [ ] User explicitly confirms readiness to start Phase 1.1

## Troubleshooting

- If `.env` is missing: create one in project root with the required keys.
- If Supabase PAT missing: guide user through creating PAT and saving to `/etc/supabase/config.conf`.
- If permissions prevent reading `/etc/supabase/config.conf`: ask the user to fix permissions or provide the needed values.
