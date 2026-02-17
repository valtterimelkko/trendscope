#!/usr/bin/env python3
"""
Deploy Stripe Products from Template Configuration

Creates products and prices in Stripe based on template's products.json.
Implements idempotency to prevent duplicates on re-runs.

Usage:
    python3 deploy-products.py --config templates/analytics-dashboard/stripe/products.json --dry-run
    python3 deploy-products.py --config templates/analytics-dashboard/stripe/products.json --deploy
"""

import argparse
import json
import os
import sys

try:
    import stripe
except ImportError:
    print("ERROR: stripe package not installed. Run: pip install stripe")
    sys.exit(1)


def load_config(config_path: str) -> dict:
    """Load products configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def check_existing_product(template_name: str, tier: str) -> dict | None:
    """Check if a product already exists with matching metadata."""
    try:
        products = stripe.Product.search(
            query=f"metadata['template']:'{template_name}' AND metadata['tier']:'{tier}'"
        )
        if products.data:
            return products.data[0]
    except stripe.error.StripeError:
        # Search might not be available, fall back to listing
        products = stripe.Product.list(limit=100)
        for product in products.data:
            meta = product.get('metadata', {})
            if meta.get('template') == template_name and meta.get('tier') == tier:
                return product
    return None


def create_product(name: str, description: str, template_name: str, tier: str, dry_run: bool) -> str:
    """Create a product in Stripe."""
    if dry_run:
        print(f"  [DRY RUN] Would create product: {name}")
        return f"prod_dry_run_{tier}"
    
    # Check for existing
    existing = check_existing_product(template_name, tier)
    if existing:
        print(f"  [SKIP] Product '{name}' already exists: {existing.id}")
        return existing.id
    
    product = stripe.Product.create(
        name=name,
        description=description or f"{name} plan",
        metadata={
            "template": template_name,
            "tier": tier,
            "created_by": "co-ceo-process"
        }
    )
    print(f"  [CREATED] Product: {product.id} - {name}")
    return product.id


def create_price(product_id: str, price_config: dict, tier: str, dry_run: bool) -> str:
    """Create a price in Stripe."""
    price_type = price_config.get('type', 'recurring')
    unit_amount = price_config.get('unitAmount', 0)
    interval = price_config.get('interval', 'month')
    currency = price_config.get('currency', 'usd')
    
    if dry_run:
        print(f"    [DRY RUN] Would create price: ${unit_amount/100:.2f}/{interval}")
        return f"price_dry_run_{tier}"
    
    if price_type == 'metered':
        # Usage-based pricing
        price = stripe.Price.create(
            product=product_id,
            currency=currency,
            recurring={
                "interval": interval,
                "usage_type": "metered",
                "aggregate_usage": "sum"
            },
            unit_amount_decimal=str(price_config.get('unitAmountDecimal', '0.001')),
            metadata={"tier": tier, "type": "metered"}
        )
    elif price_type == 'per_seat':
        # Per-seat pricing
        price = stripe.Price.create(
            product=product_id,
            unit_amount=unit_amount,
            currency=currency,
            recurring={"interval": interval},
            metadata={"tier": tier, "type": "per_seat"}
        )
    else:
        # Standard recurring
        price = stripe.Price.create(
            product=product_id,
            unit_amount=unit_amount,
            currency=currency,
            recurring={"interval": interval},
            metadata={"tier": tier, "type": "recurring"}
        )
    
    print(f"    [CREATED] Price: {price.id} - ${unit_amount/100:.2f}/{interval}")
    return price.id


def deploy_products(config: dict, dry_run: bool) -> dict:
    """Deploy all products and prices from configuration."""
    results = {
        "products": [],
        "prices": [],
        "errors": []
    }
    
    template_name = config.get('template', 'unknown')
    products = config.get('products', [])
    
    print(f"\nDeploying {len(products)} products from template: {template_name}")
    print("=" * 50)
    
    for product_config in products:
        name = product_config.get('name', 'Unnamed')
        tier = product_config.get('tier', name.lower().replace(' ', '_'))
        description = product_config.get('description', '')
        
        try:
            # Create product
            product_id = create_product(
                name=name,
                description=description,
                template_name=template_name,
                tier=tier,
                dry_run=dry_run
            )
            
            results["products"].append({
                "name": name,
                "tier": tier,
                "id": product_id
            })
            
            # Create prices for this product
            # Handle both array format and object format (monthly/yearly)
            prices_data = product_config.get('prices', {})
            
            # Convert object format to array format
            if isinstance(prices_data, dict):
                prices = []
                for interval_key, price_obj in prices_data.items():
                    if isinstance(price_obj, dict):
                        prices.append({
                            'type': 'recurring',
                            'unitAmount': price_obj.get('amount', 0),
                            'currency': price_obj.get('currency', 'usd'),
                            'interval': 'year' if interval_key == 'yearly' else 'month'
                        })
            else:
                prices = prices_data
            
            for price_config in prices:
                try:
                    price_id = create_price(
                        product_id=product_id,
                        price_config=price_config,
                        tier=tier,
                        dry_run=dry_run
                    )
                    results["prices"].append({
                        "tier": tier,
                        "id": price_id,
                        "amount": price_config.get('unitAmount', 0)
                    })
                except stripe.error.StripeError as e:
                    error_msg = f"Failed to create price for {name}: {str(e)}"
                    print(f"    [ERROR] {error_msg}")
                    results["errors"].append(error_msg)
                    
        except stripe.error.StripeError as e:
            error_msg = f"Failed to create product {name}: {str(e)}"
            print(f"  [ERROR] {error_msg}")
            results["errors"].append(error_msg)
    
    return results


def print_summary(results: dict, dry_run: bool):
    """Print deployment summary."""
    print("\n" + "=" * 50)
    print("DEPLOYMENT SUMMARY")
    print("=" * 50)
    
    if dry_run:
        print("[DRY RUN MODE - No changes made]")
    
    print(f"\nProducts: {len(results['products'])}")
    for p in results['products']:
        print(f"  - {p['name']}: {p['id']}")
    
    print(f"\nPrices: {len(results['prices'])}")
    for p in results['prices']:
        print(f"  - {p['tier']}: {p['id']} (${p['amount']/100:.2f})")
    
    if results['errors']:
        print(f"\nErrors: {len(results['errors'])}")
        for e in results['errors']:
            print(f"  - {e}")
    
    print("\n" + "=" * 50)
    
    if not dry_run and results['products']:
        print("\nAdd these to your .env file:")
        for p in results['products']:
            env_name = f"STRIPE_PRODUCT_{p['tier'].upper()}"
            print(f"{env_name}={p['id']}")
        for p in results['prices']:
            env_name = f"STRIPE_PRICE_{p['tier'].upper()}"
            print(f"{env_name}={p['id']}")


def main():
    parser = argparse.ArgumentParser(
        description='Deploy Stripe products from template config'
    )
    parser.add_argument(
        '--config',
        required=True,
        help='Path to products.json'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without creating'
    )
    parser.add_argument(
        '--deploy',
        action='store_true',
        help='Actually deploy to Stripe'
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.deploy:
        print("ERROR: Specify --dry-run or --deploy")
        sys.exit(1)
    
    # Check for Stripe key (only required for actual deployment)
    api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not api_key and not args.dry_run:
        print("ERROR: STRIPE_SECRET_KEY not set")
        sys.exit(1)
    
    # Skip Stripe setup for dry-run without key
    if args.dry_run and not api_key:
        print("[DRY RUN MODE - No Stripe key required]")
        # Load config and show what would be created
        if not os.path.exists(args.config):
            print(f"ERROR: Config not found: {args.config}")
            sys.exit(1)
        config = load_config(args.config)
        results = deploy_products(config, dry_run=True)
        print_summary(results, dry_run=True)
        sys.exit(0)
    
    # Warn if using live key
    if api_key and api_key.startswith('sk_live'):
        print("WARNING: Using LIVE Stripe key!")
        if not args.deploy:
            print("Use --deploy flag to confirm")
            sys.exit(1)
        response = input("Are you sure? Type 'yes' to continue: ")
        if response != 'yes':
            print("Aborted")
            sys.exit(0)
    
    stripe.api_key = api_key
    
    # Test connection
    print("Testing Stripe connection...")
    try:
        stripe.Account.retrieve()
        mode = "LIVE" if api_key.startswith('sk_live') else "TEST"
        print(f"✓ Connected to Stripe ({mode} mode)")
    except stripe.error.AuthenticationError:
        print("ERROR: Invalid Stripe API key")
        sys.exit(1)
    
    # Load config
    if not os.path.exists(args.config):
        print(f"ERROR: Config not found: {args.config}")
        sys.exit(1)
    
    config = load_config(args.config)
    
    # Deploy
    results = deploy_products(config, dry_run=args.dry_run)
    
    # Print summary
    print_summary(results, dry_run=args.dry_run)
    
    if results['errors']:
        sys.exit(1)


if __name__ == '__main__':
    main()
