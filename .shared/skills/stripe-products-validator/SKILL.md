---
name: stripe-products-validator
description: Validate products.json structure against Stripe billing patterns. Use to check template billing configuration before implementation.
---

# Stripe Products Configuration Validator

Validates `products.json` files in templates against Stripe billing best practices and required schema.

## When to Use

Use this skill when:
- Creating or modifying template billing configuration
- Reviewing products.json after changes
- Running template validation checks
- Ensuring billing config follows Stripe patterns

## How to Execute

### Validate a Single Template

```bash
python3 .shared/scripts/stripe/validate_products.py --file "templates/TEMPLATE_NAME/stripe/products.json"
```

### Validate All Templates

```bash
python3 .shared/scripts/stripe/validate_products.py --all
```

### Validate with Verbose Output

```bash
python3 .shared/scripts/stripe/validate_products.py --file "path/to/products.json" --verbose
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--file` | Yes* | Path to products.json file to validate |
| `--all` | No | Validate all templates in templates/ folder |
| `--verbose` | No | Show detailed validation output |

*Required unless using `--all`

## Validation Checks

### Required Fields

| Field | Description |
|-------|-------------|
| `billingModel` or `products[].type` | Must specify billing model type |
| `products` | Array of product definitions |
| `products[].id` | Unique product identifier |
| `products[].name` | Display name |
| `products[].features` | Feature list array |

### Billing Model Validation

| Model | Required Fields |
|-------|----------------|
| `usage-based` | `metering.metric`, `metering.unit` |
| `seat-based` | `seatManagement.prorationBehavior` |
| `feature-limits` | `products[].limits` object |

### Price Validation

- Monthly/yearly prices should be in cents (integer)
- Annual discount should be 15-35% (warning if outside)
- Currency must be valid ISO code

### Best Practice Checks

- [ ] At least 2-3 tiers defined
- [ ] One tier marked as highlighted/recommended
- [ ] Enterprise tier has `contact_sales: true`
- [ ] Trial configuration if `trialDays` specified
- [ ] Feature flags defined for gating

## Examples

### Validate Analytics Template

```bash
python3 .shared/scripts/stripe/validate_products.py \
  --file "templates/analytics-dashboard/stripe/products.json"
```

### Validate All with Details

```bash
python3 .shared/scripts/stripe/validate_products.py --all --verbose
```

## Response Format

```json
{
  "success": true,
  "file": "templates/analytics-dashboard/stripe/products.json",
  "billingModel": "usage-based",
  "validation": {
    "errors": [],
    "warnings": ["Annual discount of 40% is higher than typical 28%"],
    "passed": ["Required fields present", "Price format valid", "Metering config valid"]
  },
  "products": 3,
  "summary": "Validation passed with 1 warning"
}
```

## Integration with Template Enhancement

Run after any products.json modification:

```bash
# After editing
python3 .shared/scripts/stripe/validate_products.py \
  --file "templates/analytics-dashboard/stripe/products.json"

# Before committing changes
python3 .shared/scripts/stripe/validate_products.py --all
```

## Related Skills

- `stripe-billing-docs` - Lookup billing patterns
- `stripe-webhook-checker` - Validate webhook handlers
- `template-validator` - Full template validation
