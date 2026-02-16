---
name: stripe-deployer
description: Use when deploying Stripe products, prices, and webhooks from a template's configuration to the user's Stripe account. Creates the billing infrastructure needed for the MVP.
---

# Stripe Deployer

## Overview

Deploy Stripe billing infrastructure from the template's pre-configured `products.json` to the user's Stripe account. This creates products, prices, and configures webhooks so the MVP has working subscription billing.

**Core principle:** Templates define WHAT billing looks like. This skill makes it REAL in Stripe. The user should go from zero to functional billing with one skill execution.

## When to Use

- After template personalization is complete (Phase 4.3.3)
- When `STRIPE_SECRET_KEY` is configured in environment
- Before deploying the application (billing must exist first)

## Pre-Requisites

**Environment variable required:**
```bash
# Verify Stripe key exists
echo $STRIPE_SECRET_KEY | head -c 10
# Should show: sk_test_xx or sk_live_xx
```

**Template products.json must exist:**
```bash
ls templates/{selected-template}/stripe/products.json
```

**WARNING:** Only use `sk_test_*` keys unless explicitly deploying to production.

## Understanding Template Billing Models

Each template has a different billing model:

### Analytics Dashboard (Usage-Based)
```json
{
  "billingModel": "usage-based",
  "metric": "events",
  "products": [
    {
      "name": "Starter",
      "prices": [{ "type": "metered", "unitAmount": 0.001, "unit": "event" }]
    },
    {
      "name": "Pro", 
      "prices": [{ "type": "metered", "unitAmount": 0.0005, "unit": "event" }]
    }
  ]
}
```

### Productivity Tool (Seat-Based)
```json
{
  "billingModel": "seat-based",
  "products": [
    {
      "name": "Team",
      "prices": [{ "type": "per_seat", "unitAmount": 1000, "interval": "month" }]
    },
    {
      "name": "Business",
      "prices": [{ "type": "per_seat", "unitAmount": 2000, "interval": "month" }]
    }
  ]
}
```

### Content Creator (Feature Limits)
```json
{
  "billingModel": "feature-limits",
  "products": [
    {
      "name": "Creator",
      "limits": { "posts": 50, "channels": 2 },
      "prices": [{ "type": "recurring", "unitAmount": 900, "interval": "month" }]
    },
    {
      "name": "Pro Creator",
      "limits": { "posts": 500, "channels": 10 },
      "prices": [{ "type": "recurring", "unitAmount": 2900, "interval": "month" }]
    }
  ]
}
```

## Process Workflow

### Phase 1: Validate Environment

```bash
# Test Stripe connection
python3 .shared/scripts/stripe/test_connection.py --test connection
```

**Expected output:**
```
✓ Stripe API connection successful
✓ Account: acct_xxxxx (Test Mode)
✓ API version: 2023-10-16
```

**If connection fails:**
1. Verify `STRIPE_SECRET_KEY` is set correctly
2. Check key is valid at dashboard.stripe.com
3. Escalate to Co-CEO if cannot resolve

### Phase 2: Read Template Configuration

Parse `templates/{template}/stripe/products.json`:

1. Extract billing model type
2. List all products to create
3. List all prices per product
4. Note any trial periods or free tiers
5. Identify webhook events needed

### Phase 3: Create Products

For each product in the configuration:

```python
import stripe

stripe.api_key = os.environ['STRIPE_SECRET_KEY']

product = stripe.Product.create(
    name="Pro Plan",
    description="Full access to all features",
    metadata={
        "template": "analytics-dashboard",
        "tier": "pro",
        "created_by": "co-ceo-process"
    }
)
```

**Product metadata is important:** It links Stripe objects back to the template configuration for debugging.

### Phase 4: Create Prices

For each price in the configuration:

**Recurring (standard subscription):**
```python
price = stripe.Price.create(
    product=product.id,
    unit_amount=2900,  # $29.00
    currency="usd",
    recurring={"interval": "month"},
    metadata={"tier": "pro"}
)
```

**Metered (usage-based):**
```python
price = stripe.Price.create(
    product=product.id,
    currency="usd",
    recurring={
        "interval": "month",
        "usage_type": "metered",
        "aggregate_usage": "sum"
    },
    unit_amount_decimal="0.1",  # $0.001 per unit
    metadata={"tier": "pro", "metric": "events"}
)
```

**Per-seat:**
```python
price = stripe.Price.create(
    product=product.id,
    unit_amount=1000,  # $10.00 per seat
    currency="usd",
    recurring={"interval": "month"},
    metadata={"tier": "team", "billing": "per_seat"}
)
```

### Phase 5: Create Free Tier (if applicable)

If template includes a free tier:

```python
# Create a $0 price for free tier
free_price = stripe.Price.create(
    product=free_product.id,
    unit_amount=0,
    currency="usd",
    recurring={"interval": "month"},
    metadata={"tier": "free"}
)
```

### Phase 6: Configure Trial Period

If template specifies trial:

```python
# Trial is set at subscription creation time, not price creation
# Document the trial configuration for the app to use:
trial_config = {
    "trial_period_days": 14,
    "require_payment_method": False  # Reverse trial pattern
}
```

### Phase 7: Configure Webhook Endpoint

**For local development:**
```python
# Webhook endpoints are typically created manually or via Stripe CLI
# Document the required webhook events for the README
```

**Required webhook events by template:**

| Event | Purpose |
|-------|---------|
| `checkout.session.completed` | New subscription created |
| `customer.subscription.updated` | Plan change, renewal |
| `customer.subscription.deleted` | Cancellation |
| `invoice.paid` | Successful payment |
| `invoice.payment_failed` | Failed payment (dunning) |
| `customer.subscription.trial_will_end` | Trial ending soon |

**For production deployment:**
```python
webhook = stripe.WebhookEndpoint.create(
    url="https://yourdomain.com/api/stripe/webhook",
    enabled_events=[
        "checkout.session.completed",
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "invoice.paid",
        "invoice.payment_failed",
    ]
)
```

---

## IMPORTANT: Webhook Handler Implementation Timing

**The webhook endpoint URL configuration and the webhook handler implementation are SEPARATE steps:**

### What Happens in Phase 4.3.3 (This Skill)
- ✅ Stripe products and prices are created
- ✅ Stripe is configured to send webhook events to your app's webhook URL
- ✅ Webhook events are "registered" in Stripe (which events to send)
- ✅ The integration is set up at the Stripe level
- ❌ Webhook HANDLER logic is NOT implemented (only skeleton/placeholder)

### What Happens in Phase 6.1 (Backend Implementation)
- ✅ The actual backend code that *listens* for and *processes* webhook events is implemented
- ✅ When a webhook event arrives, the backend handler updates the database, activates features, etc.
- ✅ Use `stripe-webhook-checker` skill to validate handler completeness:
  ```bash
  python3 .shared/scripts/stripe/check_webhooks.py --file "path/to/webhook/route.ts"
  ```

### Required Events to Implement in Phase 6.1
The following events must be handled by the webhook handler:
- `checkout.session.completed` - Create subscription record in database
- `customer.subscription.created` - Record new subscription
- `customer.subscription.updated` - Update subscription status (plan changes, etc.)
- `customer.subscription.deleted` - Handle cancellation
- `invoice.payment_succeeded` - Record successful payment
- `invoice.payment_failed` - Handle failed payment (dunning)

### During Phase 5-6 (Before Backend Implementation Completes)
If Stripe tries to send a webhook event:
- The request will reach your app URL
- But the handler endpoint won't exist or will return 404/500
- Events will fail silently or with error responses
- **This is expected and normal**

### After Phase 6.1 Completes
- Webhook handlers are implemented and live
- Events are processed: subscriptions created, features activated, billing recorded
- End-to-end testing with Stripe test cards will work fully
- Run `stripe-webhook-checker` to validate all required handlers exist

---

### Phase 8: Update Environment Template

Update `templates/{template}/frontend/.env.example`:

```bash
# Stripe Configuration (auto-populated by stripe-deployer)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Product IDs (created by stripe-deployer)
STRIPE_PRODUCT_FREE=prod_xxxxx
STRIPE_PRODUCT_PRO=prod_xxxxx
STRIPE_PRICE_FREE_MONTHLY=price_xxxxx
STRIPE_PRICE_PRO_MONTHLY=price_xxxxx
```

### Phase 9: Verify Deployment

Run verification:
```bash
python3 .shared/scripts/stripe/test_connection.py --test products
```

**Expected output:**
```
Products in Stripe account:
  - prod_xxxxx: Pro Plan ($29/mo)
  - prod_xxxxx: Starter Plan ($9/mo)
  - prod_xxxxx: Free Plan ($0/mo)

✓ All template products found in Stripe
```

## Helper Script

Location: `.shared/scripts/stripe/deploy-products.py`

**Usage:**
```bash
# Dry run (show what would be created)
python3 .shared/scripts/stripe/deploy-products.py \
  --config templates/analytics-dashboard/stripe/products.json \
  --dry-run

# Actual deployment
python3 .shared/scripts/stripe/deploy-products.py \
  --config templates/analytics-dashboard/stripe/products.json \
  --deploy

# With webhook setup
python3 .shared/scripts/stripe/deploy-products.py \
  --config templates/analytics-dashboard/stripe/products.json \
  --deploy \
  --webhook-url https://yourdomain.com/api/stripe/webhook
```

## Idempotency

**Important:** This skill should be idempotent. Running it twice should not create duplicate products.

**Strategy:**
1. Before creating, search for existing products by metadata
2. If product exists with matching metadata, skip creation
3. Update existing products if configuration changed
4. Log all actions (created, skipped, updated)

```python
# Check if product already exists
existing = stripe.Product.search(
    query=f"metadata['template']:'{template_name}' AND metadata['tier']:'{tier}'"
)

if existing.data:
    print(f"Product {tier} already exists, skipping...")
    product = existing.data[0]
else:
    product = stripe.Product.create(...)
```

## Error Handling

### API Rate Limits
- Stripe has rate limits (100 requests/second in test mode)
- Add small delays between creations if creating many products
- Batch operations where possible

### Invalid Configuration
- Validate products.json structure before creating anything
- Check required fields: name, at least one price
- Validate price amounts are positive integers (cents)

### Partial Failure
- If creation fails midway, log what was created
- On retry, idempotency check prevents duplicates
- Report partial state to Co-CEO

## Output Report

Provide summary to Co-CEO:

```markdown
## Stripe Deployment Complete

**Template:** analytics-dashboard
**Mode:** Test (sk_test_*)

### Created Resources

| Resource | Stripe ID | Details |
|----------|-----------|---------|
| Product: Free | prod_xxxxx | $0/mo |
| Product: Starter | prod_xxxxx | $9/mo |
| Product: Pro | prod_xxxxx | $29/mo |
| Price: Free Monthly | price_xxxxx | $0.00 |
| Price: Starter Monthly | price_xxxxx | $9.00 |
| Price: Pro Monthly | price_xxxxx | $29.00 |

### Webhook Configuration

Required events documented in template README.
For local testing, use Stripe CLI:
```
stripe listen --forward-to localhost:3000/api/stripe/webhook
```

### Environment Variables

Add these to your `.env`:
```
STRIPE_PRICE_FREE=price_xxxxx
STRIPE_PRICE_STARTER=price_xxxxx
STRIPE_PRICE_PRO=price_xxxxx
```

### Next Steps

1. Copy price IDs to `.env.local`
2. Configure webhook endpoint in Stripe Dashboard (for production)
3. Test checkout flow with test cards
```

## Common Mistakes to Avoid

1. **Using live keys in development:** Always verify `sk_test_*` prefix
2. **Creating duplicate products:** Use idempotency checks
3. **Missing webhook events:** Ensure all required events are configured
4. **Hardcoding prices:** Use environment variables for price IDs
5. **Forgetting trial config:** Trial is set at subscription creation, not product creation

## Related Skills

- `stripe-integration-test`: Verify Stripe connection before deployment
- `stripe-products-validator`: Validate products.json structure
- `stripe-webhook-checker`: Verify webhook configuration
