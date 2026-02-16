---
name: phase-4-2-5-infrastructure-prerequisites
description: Co-CEO Phase 4.2.5 - Verify Stripe and Supabase are properly configured before deployment. BLOCKING GATE - infrastructure must be verified before Phase 4.3.
---

# Phase 4.2.5: Infrastructure Prerequisites

**Mode:** Conversational with main user
**Model:** Opus (Co-CEO Session)
**Depends on:** Phase 4.2 (template selected) and Phase 0.0 (API keys verified)

## BLOCKING GATE

This phase **MUST complete successfully** before Phase 4.3. Do not proceed with infrastructure deployment until both Stripe and Supabase connections are verified.

## Purpose

Phase 4.3 will execute deployment scripts that:
- Create real products/prices in Stripe
- Run database migrations in Supabase
- Configure webhook endpoints

These operations require **live service connections**. This phase ensures:
1. User has created accounts at Stripe and Supabase
2. API credentials are valid and properly configured
3. Connection to both services works
4. User understands the difference between test and live modes

## Status Communication

Announce:
> "Before deploying infrastructure, I need to verify your Stripe and Supabase connections. This ensures the deployment scripts can create real resources in your accounts."

## Process

### 1. Load Supabase Project Metadata

- Look for `docs/supabase-project.json`. If present, read `project_ref`, `project_name`, and `supabase_url` for reuse.
- If missing, plan to create a Supabase project now using `supabase-project-manage` (see Step 4) and persist metadata after creation.

### 2. Run Infrastructure Check

Execute the prerequisites checker:

```bash
.shared/scripts/co-ceo/check-infrastructure-prerequisites.sh
```

Interpret the results:
- **READY**: Both services connected - proceed to Step 5
- **PARTIAL**: One service needs setup - guide user through missing setup
- **NOT READY**: Both services need setup - guide user through both

### 3. Guide Stripe Setup (if needed)

If Stripe is not connected, present:

```
To set up Stripe:

1. **Create or access your Stripe account:**
   https://dashboard.stripe.com

2. **Get your API keys:**
   - Go to Developers → API keys
   - Copy your Secret key (starts with sk_test_ or sk_live_)

3. **Add to your .env file:**
   ```
   STRIPE_SECRET_KEY=sk_test_xxx
   ```

4. **For LIVE mode (real payments):**
   - Complete business verification at Account → Business profile
   - Get live API key (sk_live_xxx)
   - Business verification can take 1-3 days

**Which mode do you want to use?**
- **Test mode** (sk_test_): For development and testing. No real money.
- **Live mode** (sk_live_): For production. Requires business verification.
```

### 4. Create or Reuse Supabase Project

- **Reuse path:** If `docs/supabase-project.json` exists, confirm the user wants to reuse it. Skip creation and proceed to verification.
- **Create path:** If no project exists, use `supabase-project-manage` to create one now:
  ```
  python3 ~/.shared/scripts/supabase/create_project.py \
      --name "<project-name-from-master-concept>" \
      --region "eu-central-1" \
      --wait \
      --save-credentials
  ```
  - Project name: derive from Master Concept title, sanitized to Supabase rules.
  - Credentials are stored globally at `/etc/supabase/projects.json` (not in git).
  - Capture returned `project_ref`, `supabase_url`, `anon_key`, `service_role_key`.
- **Persist metadata (no secrets) locally for reuse:**
  ```
  cat > docs/supabase-project.json <<'EOF'
  {
    "project_name": "<derived-name>",
    "project_ref": "<ref>",
    "supabase_url": "https://<ref>.supabase.co",
    "credentials_location": "/etc/supabase/projects.json",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  }
  EOF
  git add docs/supabase-project.json
  ```

### 5. Re-verify After Setup

After user confirms setup, re-run the check:

```bash
.shared/scripts/co-ceo/check-infrastructure-prerequisites.sh
```

Repeat until status is **READY**.

### 6. Confirm Stripe Mode Understanding

Once connected, confirm the user understands their Stripe mode:

**If TEST mode (sk_test_):**
```
Your Stripe is in TEST mode. This means:
- You can test the full payment flow
- No real money is charged
- Use test card: 4242 4242 4242 4242

For production with real payments:
- You'll need to complete business verification
- Switch to a live API key (sk_live_xxx)

Is TEST mode acceptable for now, or do you need LIVE mode?
```

**If LIVE mode (sk_live_):**
```
Your Stripe is in LIVE mode. This means:
- Real payments will be processed
- Business verification should be complete
- Any test transactions will charge real money

Please confirm:
1. Have you completed Stripe business verification?
2. Are you ready to process real payments?

If not, consider using a test key (sk_test_xxx) during development.
```

### 7. Record Verification Status

Create or update the infrastructure verification record:

```bash
mkdir -p docs
cat > docs/infrastructure-verified.json << 'EOF'
{
  "phase": "4.2.5",
  "verified_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "stripe": {
    "connected": true,
    "mode": "[test|live]",
    "account_id": "[from check output]"
  },
  "supabase": {
    "connected": true,
    "project_ref": "[from check output]"
  },
  "ready_for_deployment": true
}
EOF
git add docs/infrastructure-verified.json
```

### 8. Proceed to Phase 4.3

Once verified, announce:

```
Infrastructure prerequisites verified:
- Stripe: Connected ([test/live] mode)
- Supabase: Connected (project: [ref])

Ready to proceed with Phase 4.3 (Template Integration).

During Phase 4.3, I will:
1. Apply your brand identity to the template (4.3.1)
2. Generate content for UI slots (4.3.2)
3. Deploy products/prices to your Stripe account (4.3.3)
4. Run database migrations in your Supabase project (4.3.4)

These are REAL deployments to your connected services.

Shall I proceed?
```

## Completion Criteria

- [ ] `check-infrastructure-prerequisites.sh` returns READY
- [ ] User understands Stripe test vs live mode
- [ ] `docs/infrastructure-verified.json` created
- [ ] `docs/supabase-project.json` exists and references the active project
- [ ] User explicitly confirms to proceed

## Troubleshooting

### Stripe Issues

**Invalid API Key:**
```
Check that your key starts with sk_test_ or sk_live_
Get a fresh key from: https://dashboard.stripe.com/apikeys
```

**Connection Failed:**
```
- Verify internet connectivity
- Check if Stripe is experiencing issues: https://status.stripe.com
- Try regenerating the API key
```

### Supabase Issues

**Project Not Found:**
```
- Verify the URL matches your project exactly
- Check that the project has finished initializing
- Ensure the project hasn't been paused (free tier pauses after inactivity)
```

**Authentication Failed:**
```
- Verify you're using the correct key type
- anon key for public operations
- service_role key for admin operations (migrations)
```

**Connection Timeout:**
```
- Check if Supabase is experiencing issues: https://status.supabase.com
- Verify your project region and network connectivity
- For paused projects, wake them from the dashboard
```

## Important Notes

- **Never skip this phase** - deployment scripts will fail without proper credentials
- **Test mode is recommended** for development
- **Live mode requires** completed Stripe business verification
- **Supabase free tier** projects pause after 1 week of inactivity - wake before deployment

## Helper Script Reference

```bash
# Full check (Stripe + Supabase)
.shared/scripts/co-ceo/check-infrastructure-prerequisites.sh

# Check only Stripe
.shared/scripts/co-ceo/check-infrastructure-prerequisites.sh --stripe

# Check only Supabase
.shared/scripts/co-ceo/check-infrastructure-prerequisites.sh --supabase

# JSON output for programmatic use
.shared/scripts/co-ceo/check-infrastructure-prerequisites.sh --json

# Individual connection tests
python3 .shared/scripts/stripe/test_connection.py --all
python3 .shared/scripts/supabase/test_connection.py --all
```

## Verify Before Proceeding

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 4.2.5
```
