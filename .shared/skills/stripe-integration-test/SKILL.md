---
name: stripe-integration-test
description: Test live Stripe API connection and validate configuration. Requires STRIPE_SECRET_KEY in environment.
---

# Stripe Integration Test

Tests live Stripe API connection and validates that your Stripe account is properly configured.

## When to Use

Use this skill when:
- Setting up Stripe integration for the first time
- Verifying API keys are valid
- Checking webhook endpoint configuration
- Testing before production deployment

## Prerequisites

1. **Stripe account** - Free to create at https://stripe.com
2. **API key** - Get from Dashboard → Developers → API Keys
3. **Environment variable** - Set `STRIPE_SECRET_KEY` in `.env` file

### Setting Up

Add to your `.env` file:
```
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## How to Execute

### Test API Connection

```bash
python3 .shared/scripts/stripe/test_connection.py --test connection
```

### List Products (Verify Setup)

```bash
python3 .shared/scripts/stripe/test_connection.py --test products
```

### List Webhook Endpoints

```bash
python3 .shared/scripts/stripe/test_connection.py --test webhooks
```

### Run All Tests

```bash
python3 .shared/scripts/stripe/test_connection.py --all
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--test` | Yes* | Test to run: `connection`, `products`, `webhooks`, `customers` |
| `--all` | No | Run all tests |
| `--verbose` | No | Show detailed output |

*Required unless using `--all`

## Tests Available

| Test | Description |
|------|-------------|
| `connection` | Verify API key is valid and has correct permissions |
| `products` | List products in Stripe account |
| `webhooks` | List configured webhook endpoints |
| `customers` | List recent customers (limit 5) |
| `subscriptions` | List active subscriptions (limit 5) |

## Examples

### Basic Connection Test

```bash
python3 .shared/scripts/stripe/test_connection.py --test connection
```

**Output:**
```json
{
  "success": true,
  "test": "connection",
  "account": {
    "id": "acct_xxxxx",
    "email": "you@example.com",
    "livemode": false
  },
  "message": "Connected to Stripe test mode"
}
```

### Check Products

```bash
python3 .shared/scripts/stripe/test_connection.py --test products --verbose
```

**Output:**
```json
{
  "success": true,
  "test": "products",
  "count": 3,
  "products": [
    {"id": "prod_xxx", "name": "Starter", "active": true},
    {"id": "prod_xxx", "name": "Pro", "active": true}
  ]
}
```

## Error Handling

### Invalid API Key
```json
{
  "success": false,
  "error": "Invalid API key",
  "suggestion": "Check STRIPE_SECRET_KEY in .env file"
}
```

### Missing API Key
```json
{
  "success": false,
  "error": "STRIPE_SECRET_KEY not found",
  "suggestion": "Add STRIPE_SECRET_KEY to .env file"
}
```

### Live Mode Warning
```json
{
  "success": true,
  "warning": "Connected to LIVE mode. Use test mode for development.",
  "suggestion": "Use sk_test_xxx key instead of sk_live_xxx"
}
```

## Integration with Testing Phase

1. Verify connection:
   ```bash
   python3 .shared/scripts/stripe/test_connection.py --test connection
   ```

2. Check if products exist:
   ```bash
   python3 .shared/scripts/stripe/test_connection.py --test products
   ```

3. If no products, create from fixtures:
   ```bash
   stripe fixtures templates/analytics-dashboard/stripe/fixtures/test-fixtures.json
   ```

4. Verify products created:
   ```bash
   python3 .shared/scripts/stripe/test_connection.py --test products
   ```

## Security Notes

- Never commit `.env` file to git
- Use test mode keys (`sk_test_`) for development
- Live mode keys (`sk_live_`) only for production
- Rotate keys if accidentally exposed

## Related Skills

- `stripe-fixture-generator` - Generate test data
- `stripe-products-validator` - Validate local configuration
- `stripe-webhook-checker` - Check webhook handlers
