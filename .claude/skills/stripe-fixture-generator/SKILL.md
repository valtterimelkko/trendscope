---
name: stripe-fixture-generator
description: Generate Stripe CLI fixtures from products.json for local testing. Creates test data for webhook simulation.
---

# Stripe CLI Fixture Generator

Generates Stripe CLI fixture files from products.json for testing billing flows locally.

## When to Use

Use this skill when:
- Setting up local testing with Stripe CLI
- Creating test data for webhook simulation
- Preparing for Phase C validation testing
- Need to test specific billing scenarios

## How to Execute

### Generate Fixtures for a Template

```bash
python3 .shared/scripts/stripe/generate_fixtures.py --template "analytics-dashboard"
```

### Generate with Custom Output Path

```bash
python3 .shared/scripts/stripe/generate_fixtures.py --template "productivity-tool" --output "tests/stripe-fixtures.json"
```

### Generate All Template Fixtures

```bash
python3 .shared/scripts/stripe/generate_fixtures.py --all
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--template` | Yes* | Template name to generate fixtures for |
| `--output` | No | Custom output path for fixture file |
| `--all` | No | Generate fixtures for all templates |

*Required unless using `--all`

## Generated Fixtures

The generated fixture file includes:

### Products & Prices
- Products matching products.json configuration
- Monthly and yearly prices
- Metered prices for usage-based models

### Customers
- Test customer for each tier
- Customer with trial subscription
- Customer with past_due subscription

### Subscriptions
- Active subscriptions for each tier
- Trial subscription (14 days remaining)
- Past-due subscription (dunning scenario)

### Invoices
- Paid invoice examples
- Failed invoice for dunning test

## Example Output

```json
{
  "_meta": {
    "template": "analytics-dashboard",
    "generated": "2025-01-01T00:00:00Z"
  },
  "fixtures": [
    {
      "name": "product_starter",
      "path": "/v1/products",
      "method": "post",
      "params": {
        "name": "Starter",
        "description": "For personal projects"
      }
    },
    {
      "name": "price_starter_monthly",
      "path": "/v1/prices",
      "method": "post",
      "params": {
        "product": "${product_starter:id}",
        "unit_amount": 900,
        "currency": "usd",
        "recurring": {"interval": "month"}
      }
    }
  ]
}
```

## Using with Stripe CLI

After generating fixtures:

```bash
# Create test data in Stripe
stripe fixtures tests/stripe-fixtures.json

# Forward webhooks to local server
stripe listen --forward-to localhost:3000/api/stripe/webhook

# Trigger test events
stripe trigger checkout.session.completed
stripe trigger invoice.payment_failed
```

## Integration with Testing Phase

1. Generate fixtures:
   ```bash
   python3 .shared/scripts/stripe/generate_fixtures.py --template "analytics-dashboard"
   ```

2. Load fixtures into Stripe:
   ```bash
   stripe fixtures templates/analytics-dashboard/stripe/fixtures/test-fixtures.json
   ```

3. Run test scenarios from `stripe-billing-enhancement-plan.md`

## Related Skills

- `stripe-products-validator` - Validate products.json first
- `stripe-webhook-checker` - Verify webhook handlers
- `stripe-integration-test` - Test live Stripe connection
