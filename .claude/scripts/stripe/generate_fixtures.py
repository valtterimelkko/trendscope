#!/usr/bin/env python3
"""
Stripe CLI Fixture Generator

Generates Stripe CLI fixture files from products.json for local testing.
No API key required - generates static fixture files.

Usage:
    python3 generate_fixtures.py --template "analytics-dashboard"
    python3 generate_fixtures.py --template "productivity-tool" --output "tests/fixtures.json"
    python3 generate_fixtures.py --all
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

TEMPLATES_DIR = "templates"


def load_products_config(template_name):
    """Load products.json for a template."""
    products_path = os.path.join(
        TEMPLATES_DIR, template_name, "stripe", "products.json"
    )
    
    if not os.path.exists(products_path):
        return None, f"products.json not found: {products_path}"
    
    try:
        with open(products_path, 'r') as f:
            return json.load(f), None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {str(e)}"


def generate_product_fixtures(config):
    """Generate product and price fixtures."""
    fixtures = []
    products = config.get('products', [])
    billing_model = config.get('billingModel', 'flat-rate')
    
    for product in products:
        product_id = product.get('id', 'unknown')
        product_name = product.get('name', product_id.title())
        description = product.get('description', '')
        
        # Skip enterprise/contact-sales products
        prices = product.get('prices', {})
        default_price = product.get('default_price', {})
        
        if prices.get('custom') or prices.get('contact_sales'):
            continue
        
        # Create product fixture
        product_fixture = {
            "name": f"product_{product_id}",
            "path": "/v1/products",
            "method": "post",
            "params": {
                "name": product_name,
                "description": description,
                "metadata": {
                    "template_id": product_id,
                    "billing_model": billing_model
                }
            }
        }
        fixtures.append(product_fixture)
        
        # Create price fixtures
        price_fixtures = generate_price_fixtures(
            product_id, prices, default_price, billing_model
        )
        fixtures.extend(price_fixtures)
    
    return fixtures


def generate_price_fixtures(product_id, prices, default_price, billing_model):
    """Generate price fixtures for a product."""
    fixtures = []
    
    # Monthly price
    monthly = prices.get('monthly', {})
    if monthly and monthly.get('amount') is not None:
        monthly_fixture = {
            "name": f"price_{product_id}_monthly",
            "path": "/v1/prices",
            "method": "post",
            "params": {
                "product": f"${{product_{product_id}:id}}",
                "unit_amount": monthly.get('amount', 0),
                "currency": monthly.get('currency', 'usd'),
                "recurring": {"interval": "month"}
            }
        }
        
        # Add per-seat for seat-based billing
        if monthly.get('per_seat') or billing_model == 'seat-based':
            monthly_fixture["params"]["recurring"]["usage_type"] = "licensed"
        
        fixtures.append(monthly_fixture)
    
    # Yearly price
    yearly = prices.get('yearly', {})
    if yearly and yearly.get('amount') is not None:
        yearly_fixture = {
            "name": f"price_{product_id}_yearly",
            "path": "/v1/prices",
            "method": "post",
            "params": {
                "product": f"${{product_{product_id}:id}}",
                "unit_amount": yearly.get('amount', 0),
                "currency": yearly.get('currency', 'usd'),
                "recurring": {"interval": "year"}
            }
        }
        fixtures.append(yearly_fixture)
    
    # Default price (for feature-limits model)
    if default_price and default_price.get('amount') is not None:
        interval = default_price.get('interval')
        default_fixture = {
            "name": f"price_{product_id}_default",
            "path": "/v1/prices",
            "method": "post",
            "params": {
                "product": f"${{product_{product_id}:id}}",
                "unit_amount": default_price.get('amount', 0),
                "currency": default_price.get('currency', 'usd')
            }
        }
        if interval:
            default_fixture["params"]["recurring"] = {"interval": interval}
        fixtures.append(default_fixture)
    
    return fixtures


def generate_customer_fixtures():
    """Generate test customer fixtures."""
    fixtures = [
        {
            "name": "customer_active",
            "path": "/v1/customers",
            "method": "post",
            "params": {
                "email": "active-user@test.example.com",
                "name": "Active Test User",
                "metadata": {"test": "true", "scenario": "active_subscription"}
            }
        },
        {
            "name": "customer_trial",
            "path": "/v1/customers",
            "method": "post",
            "params": {
                "email": "trial-user@test.example.com",
                "name": "Trial Test User",
                "metadata": {"test": "true", "scenario": "trial_subscription"}
            }
        },
        {
            "name": "customer_dunning",
            "path": "/v1/customers",
            "method": "post",
            "params": {
                "email": "dunning-user@test.example.com",
                "name": "Dunning Test User",
                "metadata": {"test": "true", "scenario": "payment_failed"}
            }
        }
    ]
    return fixtures


def generate_subscription_fixtures(config):
    """Generate test subscription fixtures."""
    fixtures = []
    products = config.get('products', [])
    
    # Find a non-free, non-enterprise product for subscriptions
    test_product = None
    for product in products:
        prices = product.get('prices', {})
        default_price = product.get('default_price', {})
        
        if prices.get('custom') or prices.get('contact_sales'):
            continue
        
        monthly_amount = prices.get('monthly', {}).get('amount', 0)
        default_amount = default_price.get('amount', 0)
        
        if monthly_amount > 0 or default_amount > 0:
            test_product = product
            break
    
    if not test_product:
        return fixtures
    
    product_id = test_product.get('id')
    
    # Active subscription
    fixtures.append({
        "name": "subscription_active",
        "path": "/v1/subscriptions",
        "method": "post",
        "params": {
            "customer": "${customer_active:id}",
            "items": [{"price": f"${{price_{product_id}_monthly:id}}"}],
            "metadata": {"test": "true", "scenario": "active"}
        }
    })
    
    # Trial subscription (can't set trial via fixtures, just note)
    fixtures.append({
        "name": "subscription_trial",
        "path": "/v1/subscriptions",
        "method": "post",
        "params": {
            "customer": "${customer_trial:id}",
            "items": [{"price": f"${{price_{product_id}_monthly:id}}"}],
            "trial_period_days": 14,
            "metadata": {"test": "true", "scenario": "trial"}
        }
    })
    
    return fixtures


def generate_fixtures(template_name, output_path=None):
    """Generate complete fixture file for a template."""
    config, error = load_products_config(template_name)
    if error:
        return {"success": False, "error": error}
    
    fixtures = []
    
    # Products and prices
    fixtures.extend(generate_product_fixtures(config))
    
    # Customers
    fixtures.extend(generate_customer_fixtures())
    
    # Subscriptions
    fixtures.extend(generate_subscription_fixtures(config))
    
    result = {
        "_meta": {
            "template": template_name,
            "billing_model": config.get('billingModel', 'unknown'),
            "generated": datetime.now(timezone.utc).isoformat(),
            "stripe_cli_version": ">=1.17.0"
        },
        "fixtures": fixtures
    }
    
    # Determine output path
    if not output_path:
        output_dir = os.path.join(
            TEMPLATES_DIR, template_name, "stripe", "fixtures"
        )
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "test-fixtures.json")
    
    # Write fixture file
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        return {
            "success": True,
            "template": template_name,
            "output": output_path,
            "fixtures_count": len(fixtures),
            "categories": {
                "products": len([f for f in fixtures if '/products' in f['path']]),
                "prices": len([f for f in fixtures if '/prices' in f['path']]),
                "customers": len([f for f in fixtures if '/customers' in f['path']]),
                "subscriptions": len([f for f in fixtures if '/subscriptions' in f['path']])
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def find_all_templates():
    """Find all templates with products.json."""
    templates = []
    
    if not os.path.exists(TEMPLATES_DIR):
        return templates
    
    for name in os.listdir(TEMPLATES_DIR):
        products_path = os.path.join(
            TEMPLATES_DIR, name, "stripe", "products.json"
        )
        if os.path.exists(products_path):
            templates.append(name)
    
    return templates


def main():
    parser = argparse.ArgumentParser(
        description="Generate Stripe CLI fixtures from products.json"
    )
    parser.add_argument(
        "--template",
        type=str,
        help="Template name to generate fixtures for"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Custom output path for fixture file"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate fixtures for all templates"
    )
    
    args = parser.parse_args()
    
    if args.all:
        templates = find_all_templates()
        if not templates:
            print(json.dumps({
                "success": False,
                "error": "No templates found with products.json"
            }, indent=2))
            sys.exit(1)
        
        results = []
        all_success = True
        
        for template in templates:
            result = generate_fixtures(template)
            results.append(result)
            if not result.get("success"):
                all_success = False
        
        print(json.dumps({
            "success": all_success,
            "templates_processed": len(results),
            "results": results
        }, indent=2))
        
        sys.exit(0 if all_success else 1)
    
    elif args.template:
        result = generate_fixtures(args.template, args.output)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("success") else 1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
