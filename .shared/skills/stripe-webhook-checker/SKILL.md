---
name: stripe-webhook-checker
description: Audit webhook handlers for completeness against required Stripe billing events. Use to identify missing event handlers.
---

# Stripe Webhook Handler Checker

Audits webhook handler files to identify missing event handlers for complete billing coverage.

## When to Use

Use this skill when:
- Reviewing webhook handler completeness
- Adding new billing features that require webhooks
- Debugging why certain Stripe events aren't being handled
- Preparing for production deployment

## How to Execute

### Check a Single Webhook Handler

```bash
python3 .shared/scripts/stripe/check_webhooks.py --file "templates/TEMPLATE_NAME/frontend/app/api/stripe/webhook/route.ts"
```

### Check All Templates

```bash
python3 .shared/scripts/stripe/check_webhooks.py --all
```

### Check with Specific Billing Model

```bash
python3 .shared/scripts/stripe/check_webhooks.py --file "path/to/route.ts" --model "usage-based"
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--file` | Yes* | Path to webhook handler file |
| `--all` | No | Check all templates |
| `--model` | No | Billing model for model-specific checks |

*Required unless using `--all`

## Event Categories

### Core Events (All Templates)

| Event | Priority | Description |
|-------|----------|-------------|
| `checkout.session.completed` | Required | User completed checkout |
| `customer.subscription.created` | Required | New subscription started |
| `customer.subscription.updated` | Required | Subscription changed |
| `customer.subscription.deleted` | Required | Subscription canceled |
| `invoice.payment_succeeded` | Required | Payment successful |
| `invoice.payment_failed` | Required | Payment failed (dunning) |

### Trial Events

| Event | Priority | Description |
|-------|----------|-------------|
| `customer.subscription.trial_will_end` | Recommended | 3 days before trial ends |

### Dunning Events

| Event | Priority | Description |
|-------|----------|-------------|
| `invoice.payment_action_required` | Recommended | SCA required |
| `invoice.upcoming` | Optional | Preview of next invoice |

### Usage-Based Events

| Event | Priority | Description |
|-------|----------|-------------|
| `v1.billing.meter.error_report_triggered` | Recommended | Meter event errors |

### Customer Events

| Event | Priority | Description |
|-------|----------|-------------|
| `customer.created` | Optional | New customer created |
| `customer.updated` | Optional | Customer details changed |

## Examples

### Check Analytics Template Webhook

```bash
python3 .shared/scripts/stripe/check_webhooks.py \
  --file "templates/analytics-dashboard/frontend/app/api/stripe/webhook/route.ts" \
  --model "usage-based"
```

### Check All Templates

```bash
python3 .shared/scripts/stripe/check_webhooks.py --all
```

## Response Format

```json
{
  "success": true,
  "file": "templates/analytics-dashboard/frontend/app/api/stripe/webhook/route.ts",
  "coverage": {
    "handled": ["checkout.session.completed", "customer.subscription.created", ...],
    "missing_required": [],
    "missing_recommended": ["customer.subscription.trial_will_end"],
    "missing_optional": ["customer.created"]
  },
  "score": "85%",
  "summary": "Good coverage. Missing 1 recommended, 1 optional events."
}
```

## Integration with Template Enhancement

1. Run before adding new billing features:
   ```bash
   python3 .shared/scripts/stripe/check_webhooks.py \
     --file "templates/analytics-dashboard/frontend/app/api/stripe/webhook/route.ts"
   ```

2. Get patterns for missing handlers:
   ```bash
   python3 .shared/scripts/stripe/lookup_pattern.py --pattern "dunning-handler"
   ```

3. Re-run to verify coverage after adding handlers

## Best Practices

1. **Always handle all required events** - Core billing won't work without them
2. **Add trial events** - Essential for trial-to-paid conversion
3. **Add dunning events** - Improves payment recovery
4. **Log unhandled events** - Helps debugging
5. **Return 200 for unknown events** - Stripe expects acknowledgment

## Related Skills

- `stripe-billing-docs` - Get code patterns for missing handlers
- `stripe-products-validator` - Validate products configuration
- `template-validator` - Full template validation
