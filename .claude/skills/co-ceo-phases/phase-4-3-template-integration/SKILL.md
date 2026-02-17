---
name: phase-4-3-template-integration
description: Co-CEO Phase 4.3 - Orchestrate 4 agents (2 sequential, 2 parallel) to personalize template with brand, generate content, and DEPLOY Stripe/Supabase infrastructure to live services.
---

# Phase 4.3: Template Integration

**Mode:** Sequential agents → Parallel agents
**Depends on:** Phase 4.2.5 complete (infrastructure prerequisites verified)

## CRITICAL PREREQUISITE CHECK

**Before starting Phase 4.3, verify Phase 4.2.5 completed:**

```bash
# Check infrastructure verification exists
cat docs/infrastructure-verified.json

# If file doesn't exist or shows not ready, STOP and run Phase 4.2.5
.shared/scripts/co-ceo/check-infrastructure-prerequisites.sh
```

If `docs/supabase-project.json` exists, reuse it:
```bash
export SUPABASE_PROJECT_REF=$(python3 - <<'PY'
import json;print(json.load(open("docs/supabase-project.json")).get("project_ref",""))
PY
)
export SUPABASE_URL=$(python3 - <<'PY'
import json;print(json.load(open("docs/supabase-project.json")).get("supabase_url",""))
PY
)
```
This ensures deployment agents target the same Supabase project.

**DO NOT PROCEED** if infrastructure prerequisites are not verified. The deployment agents will fail without valid credentials.

## Determine Selected Template

Before starting, read the template selection:

```bash
cat docs/selected-template.txt
```

Expected values: `analytics-dashboard`, `productivity-tool`, `content-creator`, `utility-processor`, or `digital-download`

## Status Communication

Announce:
> "Starting template integration. I'll personalize the [selected-template] with your brand identity, then **deploy real infrastructure** to your Stripe and Supabase accounts. Takes 15-25 minutes."

## Agent Sequence

### 4.3.1: Brand Personalization (Sequential)
**Skill:** `template-personalizer` | **Model:** Haiku

```
You are a Brand Personalizer agent. Use template-personalizer skill.

INPUTS:
- docs/brand/brand-kit-guide.md
- templates/[SELECTED_TEMPLATE]/frontend/styles/tokens.css
- templates/[SELECTED_TEMPLATE]/frontend/tailwind.config.js

TASK: Apply brand colors, typography to template tokens.

OUTPUTS:
- Updated tokens.css and tailwind.config.js
- Validate WCAG AA contrast ratios

CONSTRAINTS: No additional agents. 3-attempt escalation.
```

After completion: `git-commit-phase.sh "4.3.1" "Brand personalization applied"`

### 4.3.2: Content Generation (Sequential, after 4.3.1)
**Skill:** `copywriter` | **Model:** Haiku

```
You are a Content Copywriter agent. Use copywriter skill.

INPUTS: master-concept.md, brand-kit-guide.md, all marketing/*.md, templates/.../slots.json

TASK: Generate content for all UI slots respecting maxLength constraints, brand voice, and marketing messaging.

OUTPUTS: Updated template component files with personalized content.
```

After completion: `git-commit-phase.sh "4.3.2" "Content generation complete"`

### 4.3.3 & 4.3.4: Infrastructure Deployment (Parallel after 4.3.2)

**THESE ARE REAL DEPLOYMENTS** - Not configuration, not validation. Actual execution.

#### 4.3.3: Stripe Deployment
**Agent:** `stripe-deployer` | **Model:** Haiku

Agent MUST execute:
```bash
# Deploy products and prices to Stripe
python3 .shared/scripts/stripe/deploy-products.py \
  --config templates/[SELECTED_TEMPLATE]/stripe/products.json \
  --deploy

# Verify deployment succeeded
python3 .shared/scripts/stripe/test_connection.py --test products --verbose
```

Expected outcomes:
- Products created in Stripe dashboard
- Price IDs generated and recorded
- `.env` updated with real STRIPE_PRICE_* IDs

**Agent must verify:** At least 1 product exists in Stripe after deployment.

#### 4.3.4: Supabase Deployment
**Agent:** `supabase-deployer` | **Model:** Haiku

Agent MUST execute:
```bash
# Run migrations against live Supabase project
python3 .shared/scripts/supabase/run-migrations.py \
  --migrations templates/[SELECTED_TEMPLATE]/supabase/migrations/ \
  --execute

# Verify deployment succeeded
python3 .shared/scripts/supabase/test_connection.py --test tables --verbose
```

Expected outcomes:
- Tables created in Supabase database
- RLS policies active on all public tables
- Auth configuration ready

**Agent must verify:** Tables exist and RLS is enabled after migrations.

These touch different services with no file overlap—safe to run parallel.

### Post-Deployment Verification

After BOTH agents complete, run infrastructure verification:

```bash
# Full verification
.shared/scripts/co-ceo/check-infrastructure-prerequisites.sh --json
```

Expected output should show:
- `stripe.products_count` > 0
- `supabase.tables_count` > 0

**If verification fails:**
1. Check agent error logs
2. Retry the failed deployment
3. If 3 attempts fail, escalate to user with specific error

After verification passes: `git-commit-phase.sh "4.3.3 & 4.3.4" "Infrastructure deployed: Stripe and Supabase"`

## Deployment Record

Create a deployment record for tracking:

```bash
cat > docs/deployment-record.json << 'EOF'
{
  "phase": "4.3",
  "deployed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "template": "[SELECTED_TEMPLATE]",
  "stripe": {
    "products_deployed": true,
    "mode": "[test|live]",
    "product_ids": ["prod_xxx", "prod_yyy"]
  },
  "supabase": {
    "migrations_run": true,
    "tables_created": ["profiles", "customers", "subscriptions", ...],
    "rls_enabled": true
  }
}
EOF
git add docs/deployment-record.json
```

## Completion Criteria

- [ ] Brand personalization applied (4.3.1)
- [ ] Content generated for all UI slots (4.3.2)
- [ ] **Stripe products exist** in dashboard (4.3.3)
- [ ] **Supabase tables exist** in database (4.3.4)
- [ ] Post-deployment verification passes
- [ ] `docs/deployment-record.json` created
- [ ] All committed to git
- [ ] **Handoff to Phase 4.3.5 Supabase Security Audit (blocking gate)**

## Troubleshooting

### Stripe Deployment Fails

```bash
# Check API key validity
python3 .shared/scripts/stripe/test_connection.py --test connection

# Validate products.json structure
python3 .shared/scripts/stripe/validate_products.py \
  --config templates/[TEMPLATE]/stripe/products.json

# Try deployment with verbose logging
python3 .shared/scripts/stripe/deploy-products.py \
  --config templates/[TEMPLATE]/stripe/products.json \
  --deploy --verbose
```

### Supabase Deployment Fails

```bash
# Check connection
python3 .shared/scripts/supabase/test_connection.py --test connection

# Try dry run first
python3 .shared/scripts/supabase/run-migrations.py \
  --migrations templates/[TEMPLATE]/supabase/migrations/ \
  --dry-run

# Check for existing objects (idempotency)
python3 .shared/scripts/supabase/test_connection.py --test tables
```

### Partial Deployment

If one service deploys but not the other:
1. Don't rollback the successful deployment
2. Fix the failing service
3. Re-run only the failing agent
4. Verify both services in final check

## Important Notes

- **These are REAL deployments** - Products will appear in Stripe, tables will be created in Supabase
- **Test mode is safe** - Using sk_test_ key means no real charges
- **Migrations are idempotent** - Safe to re-run if interrupted
- **Webhook handlers are NOT implemented yet** - That's Phase 6.1

## Verify Before Proceeding

```bash
.shared/scripts/co-ceo/verify-phase-completion.sh 4.3
```
