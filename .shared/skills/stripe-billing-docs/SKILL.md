---
name: stripe-billing-docs
description: Lookup Stripe billing documentation patterns and code examples. Use when implementing Stripe subscriptions, webhooks, meters API, or customer portal.
---

# Stripe Billing Documentation Lookup

Provides Stripe billing patterns, code examples, and implementation guidance without requiring API access.

## When to Use

Use this skill when:
- Implementing Stripe subscription flows
- Writing webhook handlers for billing events
- Setting up usage-based billing with Meters API
- Configuring Stripe Customer Portal
- Understanding proration, trials, or dunning patterns

## How to Execute

### Lookup a Billing Pattern

```bash
python3 .shared/scripts/stripe/lookup_pattern.py --pattern "PATTERN_NAME"
```

### List All Available Patterns

```bash
python3 .shared/scripts/stripe/lookup_pattern.py --list
```

### Search Patterns by Keyword

```bash
python3 .shared/scripts/stripe/lookup_pattern.py --search "KEYWORD"
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--pattern` | Yes* | Pattern name to lookup (e.g., `webhook-handler`, `meters-api`) |
| `--list` | No | List all available patterns |
| `--search` | No | Search patterns by keyword |

*Required unless using `--list` or `--search`

## Available Patterns

| Pattern Name | Description |
|--------------|-------------|
| `webhook-handler` | Complete webhook handler with signature verification |
| `checkout-session` | Create Stripe Checkout session for subscriptions |
| `customer-portal` | Customer Portal session creation |
| `meters-api` | Usage-based billing with Meters API v2 |
| `subscription-create` | Create subscription programmatically |
| `subscription-update` | Update subscription (upgrade/downgrade) |
| `proration` | Handle prorated charges on plan changes |
| `trial-subscription` | Create subscription with trial period |
| `dunning-handler` | Handle failed payments and dunning |
| `seat-based-billing` | Per-seat subscription management |
| `usage-records` | Record usage for metered billing |
| `invoice-preview` | Preview upcoming invoice |

## Examples

### Get Webhook Handler Pattern

```bash
python3 .shared/scripts/stripe/lookup_pattern.py --pattern "webhook-handler"
```

**Output:** Complete TypeScript webhook handler with:
- Signature verification
- Event type handling
- Supabase integration
- Error handling

### Get Meters API Pattern

```bash
python3 .shared/scripts/stripe/lookup_pattern.py --pattern "meters-api"
```

**Output:** Usage-based billing implementation with:
- Meter event creation
- Idempotency handling
- Batch ingestion pattern
- Error monitoring

### Search for Trial-Related Patterns

```bash
python3 .shared/scripts/stripe/lookup_pattern.py --search "trial"
```

## Response Format

```json
{
  "success": true,
  "pattern": "webhook-handler",
  "description": "Complete webhook handler with signature verification",
  "code": "// TypeScript code...",
  "notes": ["Important implementation notes"],
  "related_patterns": ["checkout-session", "subscription-create"]
}
```

## Integration with Template Enhancement

When enhancing billing templates, use this skill to:

1. **Extend webhook handlers:**
   ```bash
   python3 .shared/scripts/stripe/lookup_pattern.py --pattern "dunning-handler"
   ```

2. **Add Customer Portal:**
   ```bash
   python3 .shared/scripts/stripe/lookup_pattern.py --pattern "customer-portal"
   ```

3. **Implement usage tracking:**
   ```bash
   python3 .shared/scripts/stripe/lookup_pattern.py --pattern "meters-api"
   ```

## Best Practices

1. **Always verify webhook signatures** - Never trust unverified events
2. **Use idempotency keys** - Prevent duplicate processing
3. **Handle all subscription statuses** - Including `past_due`, `unpaid`, `paused`
4. **Store Stripe IDs locally** - Map `stripe_customer_id` to your users table
5. **Use Customer Portal** - Don't build custom billing UI from scratch

## Related Skills

- `stripe-products-validator` - Validate products.json structure
- `stripe-webhook-checker` - Audit webhook handler completeness
- `stripe-fixture-generator` - Generate Stripe CLI test fixtures
