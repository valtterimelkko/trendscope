#!/usr/bin/env python3
"""
Validate Stripe products.json configuration.
Usage: python3 check-stripe-config.py <products-json-path>
"""

import json
import re
import sys


VALID_CURRENCIES = ["usd", "eur", "gbp", "cad", "aud"]


def validate_product_id(product_id: str) -> bool:
    """Check if product ID is URL-safe."""
    return bool(re.match(r'^[a-z0-9-]+$', product_id))


def validate_products(file_path: str) -> tuple:
    """Validate the products.json file."""
    blockers = []
    warnings = []

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        blockers.append(f"Invalid JSON: {e}")
        return blockers, warnings
    except FileNotFoundError:
        blockers.append(f"File not found: {file_path}")
        return blockers, warnings

    # Check products array
    if "products" not in data:
        blockers.append("Missing 'products' array")
        return blockers, warnings

    products = data["products"]

    if not isinstance(products, list):
        blockers.append("'products' must be an array")
        return blockers, warnings

    if len(products) < 2:
        warnings.append("At least 2 products recommended for pricing page")

    highlighted_count = 0

    for i, product in enumerate(products):
        prefix = f"Product {i+1}"

        # Required fields
        required = ["id", "name", "description", "features"]
        for field in required:
            if field not in product:
                blockers.append(f"{prefix}: Missing required field '{field}'")

        # Validate ID format
        pid = product.get("id", "")
        if pid and not validate_product_id(pid):
            blockers.append(
                f"{prefix}: ID '{pid}' must be lowercase, "
                "alphanumeric with hyphens only"
            )

        # Check features
        features = product.get("features", [])
        if isinstance(features, list) and len(features) < 1:
            warnings.append(f"{prefix}: Should have at least 1 feature")

        # Check prices
        prices = product.get("prices", {})
        if not prices and not product.get("custom"):
            warnings.append(f"{prefix}: No prices defined")

        # Validate price amounts (should be in cents)
        for period, price_data in prices.items():
            if isinstance(price_data, dict):
                amount = price_data.get("amount", 0)
                if amount < 100 and amount > 0:
                    warnings.append(
                        f"{prefix}: Price {amount} seems low. "
                        "Prices should be in cents (e.g., 900 = $9.00)"
                    )

                currency = price_data.get("currency", "").lower()
                if currency and currency not in VALID_CURRENCIES:
                    warnings.append(
                        f"{prefix}: Currency '{currency}' "
                        f"not in common list: {VALID_CURRENCIES}"
                    )

        # Check yearly discount
        if "monthly" in prices and "yearly" in prices:
            monthly = prices["monthly"]
            yearly = prices["yearly"]
            if isinstance(monthly, dict) and isinstance(yearly, dict):
                m_amount = monthly.get("amount", 0)
                y_amount = yearly.get("amount", 0)
                if m_amount > 0 and y_amount > 0:
                    expected_yearly = m_amount * 12
                    discount = (expected_yearly - y_amount) / expected_yearly
                    if discount < 0.1:
                        warnings.append(
                            f"{prefix}: Yearly discount is only "
                            f"{discount*100:.0f}% (recommend 10-30%)"
                        )

        # Check highlighted
        if product.get("highlighted"):
            highlighted_count += 1

    if highlighted_count == 0:
        warnings.append(
            "No product marked as 'highlighted: true' "
            "(recommended for pricing page)"
        )
    elif highlighted_count > 1:
        warnings.append(
            f"{highlighted_count} products marked as highlighted "
            "(only 1 recommended)"
        )

    return blockers, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check-stripe-config.py <products-json-path>")
        sys.exit(1)

    file_path = sys.argv[1]
    blockers, warnings = validate_products(file_path)

    # JSON output mode
    if "--json" in sys.argv:
        result = {
            "status": "pass" if not blockers else "fail",
            "blockers": blockers,
            "warnings": warnings,
        }
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        if blockers:
            print("❌ BLOCKERS:")
            for b in blockers:
                print(f"   {b}")

        if warnings:
            print("⚠️  WARNINGS:")
            for w in warnings:
                print(f"   {w}")

        if not blockers and not warnings:
            print("✅ Stripe configuration valid")

    # Exit codes
    if blockers:
        sys.exit(1)
    elif warnings:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
