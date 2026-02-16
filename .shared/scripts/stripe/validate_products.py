#!/usr/bin/env python3
"""
Stripe Products Configuration Validator

Validates products.json files against Stripe billing patterns and schema.
No API key required - validates structure only.

Usage:
    python3 validate_products.py --file "templates/analytics-dashboard/stripe/products.json"
    python3 validate_products.py --all
    python3 validate_products.py --file "path/to/products.json" --verbose
"""

import argparse
import json
import os
import sys
import glob

# Valid billing models
VALID_BILLING_MODELS = ['usage-based', 'seat-based', 'feature-limits', 'flat-rate', 'hybrid']

# Valid currencies
VALID_CURRENCIES = ['usd', 'eur', 'gbp', 'cad', 'aud', 'jpy']

# Valid subscription statuses
VALID_STATUSES = ['trialing', 'active', 'canceled', 'incomplete', 
                  'incomplete_expired', 'past_due', 'unpaid', 'paused']


def validate_products_file(file_path, verbose=False):
    """Validate a single products.json file."""
    result = {
        "success": True,
        "file": file_path,
        "billingModel": None,
        "validation": {
            "errors": [],
            "warnings": [],
            "passed": []
        },
        "products": 0,
        "summary": ""
    }
    
    # Check file exists
    if not os.path.exists(file_path):
        result["success"] = False
        result["validation"]["errors"].append(f"File not found: {file_path}")
        result["summary"] = "Validation failed: File not found"
        return result
    
    # Load JSON
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        result["success"] = False
        result["validation"]["errors"].append(f"Invalid JSON: {str(e)}")
        result["summary"] = "Validation failed: Invalid JSON"
        return result
    
    # Check for products array
    if 'products' not in config:
        result["validation"]["errors"].append("Missing 'products' array")
    elif not isinstance(config['products'], list):
        result["validation"]["errors"].append("'products' must be an array")
    else:
        result["products"] = len(config['products'])
        result["validation"]["passed"].append(f"Found {result['products']} products")
    
    # Determine billing model
    billing_model = config.get('billingModel')
    if not billing_model and 'products' in config and len(config['products']) > 0:
        billing_model = config['products'][0].get('type')
    
    if billing_model:
        result["billingModel"] = billing_model
        if billing_model in VALID_BILLING_MODELS:
            result["validation"]["passed"].append(f"Valid billing model: {billing_model}")
        else:
            result["validation"]["warnings"].append(
                f"Unknown billing model: {billing_model}. "
                f"Expected one of: {', '.join(VALID_BILLING_MODELS)}"
            )
    else:
        result["validation"]["warnings"].append(
            "No billing model specified (add 'billingModel' field)"
        )
    
    # Validate each product
    if 'products' in config and isinstance(config['products'], list):
        validate_products(config['products'], billing_model, result)
    
    # Check billing-model-specific requirements
    if billing_model == 'usage-based':
        validate_usage_based(config, result)
    elif billing_model == 'seat-based':
        validate_seat_based(config, result)
    elif billing_model == 'feature-limits':
        validate_feature_limits(config, result)
    
    # Check for best practices
    validate_best_practices(config, result)
    
    # Generate summary
    errors = len(result["validation"]["errors"])
    warnings = len(result["validation"]["warnings"])
    
    if errors > 0:
        result["success"] = False
        result["summary"] = f"Validation failed with {errors} error(s)"
    elif warnings > 0:
        result["summary"] = f"Validation passed with {warnings} warning(s)"
    else:
        result["summary"] = "Validation passed"
    
    return result


def validate_products(products, billing_model, result):
    """Validate individual products in the array."""
    product_ids = []
    has_highlighted = False
    has_enterprise = False
    
    for i, product in enumerate(products):
        prefix = f"products[{i}]"
        
        # Required fields
        if 'id' not in product:
            result["validation"]["errors"].append(f"{prefix}: Missing 'id' field")
        else:
            if product['id'] in product_ids:
                result["validation"]["errors"].append(
                    f"{prefix}: Duplicate product id '{product['id']}'"
                )
            product_ids.append(product['id'])
        
        if 'name' not in product:
            result["validation"]["errors"].append(f"{prefix}: Missing 'name' field")
        
        if 'features' not in product:
            result["validation"]["warnings"].append(f"{prefix}: Missing 'features' array")
        elif not isinstance(product['features'], list):
            result["validation"]["errors"].append(f"{prefix}: 'features' must be an array")
        
        # Check for highlighted product
        if product.get('highlighted') or product.get('metadata', {}).get('recommended'):
            has_highlighted = True
        
        # Check for enterprise tier
        if 'enterprise' in product.get('id', '').lower():
            has_enterprise = True
            if not product.get('prices', {}).get('custom') and \
               not product.get('prices', {}).get('contact_sales'):
                result["validation"]["warnings"].append(
                    f"{prefix}: Enterprise tier should have 'contact_sales: true'"
                )
        
        # Validate prices
        validate_prices(product, prefix, result)
    
    if len(products) >= 2:
        result["validation"]["passed"].append("Has 2+ pricing tiers")
    else:
        result["validation"]["warnings"].append(
            "Recommend at least 2-3 pricing tiers"
        )
    
    if has_highlighted:
        result["validation"]["passed"].append("Has highlighted/recommended tier")
    else:
        result["validation"]["warnings"].append(
            "Consider marking one tier as highlighted/recommended"
        )


def validate_prices(product, prefix, result):
    """Validate price configuration for a product."""
    prices = product.get('prices', {})
    default_price = product.get('default_price', {})
    
    # Check for price definition
    if not prices and not default_price:
        # Allow free tier
        if product.get('id') == 'starter' or product.get('id') == 'free':
            return
        result["validation"]["warnings"].append(
            f"{prefix}: No prices defined"
        )
        return
    
    # Validate monthly/yearly prices
    monthly = prices.get('monthly', {})
    yearly = prices.get('yearly', {})
    
    if monthly:
        amount = monthly.get('amount')
        if amount is not None:
            if not isinstance(amount, int):
                result["validation"]["errors"].append(
                    f"{prefix}.prices.monthly.amount: Must be integer (cents)"
                )
            if isinstance(amount, int) and amount > 0 and amount < 100:
                result["validation"]["warnings"].append(
                    f"{prefix}.prices.monthly.amount: {amount} seems low. "
                    "Prices should be in cents (e.g., 900 for $9)"
                )
    
    # Check annual discount
    if monthly and yearly:
        monthly_amount = monthly.get('amount', 0)
        yearly_amount = yearly.get('amount', 0)
        
        if monthly_amount > 0 and yearly_amount > 0:
            expected_yearly = monthly_amount * 12
            actual_discount = (expected_yearly - yearly_amount) / expected_yearly * 100
            
            if actual_discount < 15:
                result["validation"]["warnings"].append(
                    f"{prefix}: Annual discount of {actual_discount:.0f}% is low. "
                    "Consider 20-30% discount"
                )
            elif actual_discount > 35:
                result["validation"]["warnings"].append(
                    f"{prefix}: Annual discount of {actual_discount:.0f}% is very high"
                )
            else:
                result["validation"]["passed"].append(
                    f"{prefix}: Annual discount of {actual_discount:.0f}% is reasonable"
                )
    
    # Validate currency
    currency = monthly.get('currency') or yearly.get('currency') or \
               default_price.get('currency')
    if currency and currency.lower() not in VALID_CURRENCIES:
        result["validation"]["warnings"].append(
            f"{prefix}: Unknown currency '{currency}'"
        )


def validate_usage_based(config, result):
    """Validate usage-based billing specific requirements."""
    metering = config.get('metering', {})
    
    if not metering:
        result["validation"]["errors"].append(
            "Usage-based billing requires 'metering' configuration"
        )
        return
    
    if 'metric' not in metering:
        result["validation"]["errors"].append(
            "metering.metric is required (e.g., 'events', 'api_calls')"
        )
    else:
        result["validation"]["passed"].append(
            f"Metering metric defined: {metering['metric']}"
        )
    
    if 'unit' not in metering:
        result["validation"]["warnings"].append(
            "metering.unit recommended (e.g., 'event', 'call')"
        )
    
    # Check for overage configuration
    overage = metering.get('overage', {})
    if overage.get('enabled'):
        if 'rate_per_unit' not in overage:
            result["validation"]["warnings"].append(
                "metering.overage.rate_per_unit recommended when overage enabled"
            )
        else:
            result["validation"]["passed"].append("Overage pricing configured")


def validate_seat_based(config, result):
    """Validate seat-based billing specific requirements."""
    seat_mgmt = config.get('seatManagement', {})
    
    if not seat_mgmt:
        result["validation"]["warnings"].append(
            "Seat-based billing should include 'seatManagement' configuration"
        )
        return
    
    if 'prorationBehavior' not in seat_mgmt:
        result["validation"]["warnings"].append(
            "seatManagement.prorationBehavior recommended "
            "('create_prorations', 'always_invoice', or 'none')"
        )
    else:
        result["validation"]["passed"].append(
            f"Proration behavior: {seat_mgmt['prorationBehavior']}"
        )
    
    # Check products have per_seat pricing
    products = config.get('products', [])
    for product in products:
        prices = product.get('prices', {})
        monthly = prices.get('monthly', {})
        if monthly and not monthly.get('per_seat'):
            result["validation"]["warnings"].append(
                f"products[{product.get('id')}]: Consider adding 'per_seat: true' "
                "for seat-based billing"
            )


def validate_feature_limits(config, result):
    """Validate feature-limits billing specific requirements."""
    products = config.get('products', [])
    
    has_free_tier = False
    all_have_limits = True
    
    for product in products:
        limits = product.get('limits', {})
        
        if not limits:
            all_have_limits = False
            result["validation"]["warnings"].append(
                f"products[{product.get('id')}]: Missing 'limits' for feature-limits model"
            )
        
        # Check for free tier
        default_price = product.get('default_price', {})
        if default_price.get('amount') == 0:
            has_free_tier = True
    
    if all_have_limits:
        result["validation"]["passed"].append("All products have limits defined")
    
    if has_free_tier:
        result["validation"]["passed"].append("Free tier available")


def validate_best_practices(config, result):
    """Check general best practices."""
    # Check for billing config (trial, dunning, etc.)
    billing_config = config.get('billingConfig', {})
    
    if billing_config:
        if 'trialDays' in billing_config:
            result["validation"]["passed"].append(
                f"Trial period: {billing_config['trialDays']} days"
            )
        
        if billing_config.get('dunningEnabled'):
            result["validation"]["passed"].append("Dunning enabled")
        
        if billing_config.get('gracePeriodDays'):
            result["validation"]["passed"].append(
                f"Grace period: {billing_config['gracePeriodDays']} days"
            )


def find_all_products_files():
    """Find all products.json files in templates folder."""
    patterns = [
        'templates/*/stripe/products.json',
        'templates/**/stripe/products.json'
    ]
    
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern, recursive=True))
    
    return list(set(files))  # Remove duplicates


def main():
    parser = argparse.ArgumentParser(
        description="Validate Stripe products.json configuration"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to products.json file to validate"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all templates"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    
    args = parser.parse_args()
    
    if args.all:
        files = find_all_products_files()
        if not files:
            print(json.dumps({
                "success": False,
                "error": "No products.json files found in templates/"
            }, indent=2))
            sys.exit(1)
        
        results = []
        all_success = True
        
        for file_path in files:
            result = validate_products_file(file_path, args.verbose)
            results.append(result)
            if not result["success"]:
                all_success = False
        
        print(json.dumps({
            "success": all_success,
            "files_validated": len(results),
            "results": results
        }, indent=2))
        
        sys.exit(0 if all_success else 1)
    
    elif args.file:
        result = validate_products_file(args.file, args.verbose)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["success"] else 1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
