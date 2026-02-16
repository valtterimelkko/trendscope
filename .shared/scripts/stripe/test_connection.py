#!/usr/bin/env python3
"""
Stripe Integration Test

Tests live Stripe API connection and validates configuration.
Requires STRIPE_SECRET_KEY environment variable.

Usage:
    python3 test_connection.py --test connection
    python3 test_connection.py --test products
    python3 test_connection.py --all
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

STRIPE_API_BASE = "https://api.stripe.com/v1"


def load_api_key():
    """
    Load Stripe API key from environment or .env file.
    
    Checks in order:
    1. STRIPE_SECRET_KEY environment variable
    2. .env file in current directory
    3. .env file in project root
    """
    # Check environment variable
    api_key = os.environ.get('STRIPE_SECRET_KEY')
    if api_key:
        return api_key, None
    
    # Check .env files
    env_paths = [
        '.env',
        os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'),
    ]
    
    for env_path in env_paths:
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('STRIPE_SECRET_KEY='):
                            value = line.split('=', 1)[1].strip()
                            # Remove quotes if present
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            if value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            if value:
                                return value, None
            except Exception:
                pass
    
    return None, "STRIPE_SECRET_KEY not found in environment or .env file"


def make_stripe_request(endpoint, api_key, method="GET", data=None):
    """Make a request to Stripe API."""
    url = f"{STRIPE_API_BASE}/{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    request = urllib.request.Request(url, headers=headers, method=method)
    
    if data:
        request.data = urllib.parse.urlencode(data).encode()
    
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode()), None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            error_data = json.loads(error_body)
            return None, error_data.get('error', {}).get('message', str(e))
        except:
            return None, str(e)
    except urllib.error.URLError as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, str(e)


def test_connection(api_key, verbose=False):
    """Test API connection and get account info."""
    result, error = make_stripe_request("account", api_key)
    
    if error:
        if "Invalid API Key" in str(error):
            return {
                "success": False,
                "test": "connection",
                "error": "Invalid API key",
                "suggestion": "Check STRIPE_SECRET_KEY in .env file"
            }
        return {
            "success": False,
            "test": "connection",
            "error": str(error)
        }
    
    is_live = api_key.startswith('sk_live_')
    
    response = {
        "success": True,
        "test": "connection",
        "account": {
            "id": result.get("id"),
            "email": result.get("email"),
            "livemode": result.get("livemode", False)
        },
        "message": f"Connected to Stripe {'LIVE' if is_live else 'test'} mode"
    }
    
    if is_live:
        response["warning"] = (
            "Connected to LIVE mode. Use test mode for development."
        )
        response["suggestion"] = "Use sk_test_xxx key instead of sk_live_xxx"
    
    return response


def test_products(api_key, verbose=False):
    """List products in Stripe account."""
    result, error = make_stripe_request("products?limit=10&active=true", api_key)
    
    if error:
        return {
            "success": False,
            "test": "products",
            "error": str(error)
        }
    
    products = result.get("data", [])
    
    response = {
        "success": True,
        "test": "products",
        "count": len(products),
        "has_more": result.get("has_more", False)
    }
    
    if verbose:
        response["products"] = [
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "active": p.get("active"),
                "metadata": p.get("metadata", {})
            }
            for p in products
        ]
    else:
        response["products"] = [
            {"id": p.get("id"), "name": p.get("name")}
            for p in products
        ]
    
    if len(products) == 0:
        response["message"] = "No products found. Create products using Stripe Dashboard or fixtures."
    
    return response


def test_webhooks(api_key, verbose=False):
    """List webhook endpoints."""
    result, error = make_stripe_request("webhook_endpoints?limit=10", api_key)
    
    if error:
        return {
            "success": False,
            "test": "webhooks",
            "error": str(error)
        }
    
    endpoints = result.get("data", [])
    
    response = {
        "success": True,
        "test": "webhooks",
        "count": len(endpoints)
    }
    
    if verbose:
        response["endpoints"] = [
            {
                "id": e.get("id"),
                "url": e.get("url"),
                "status": e.get("status"),
                "enabled_events": e.get("enabled_events", [])
            }
            for e in endpoints
        ]
    else:
        response["endpoints"] = [
            {"url": e.get("url"), "status": e.get("status")}
            for e in endpoints
        ]
    
    if len(endpoints) == 0:
        response["message"] = (
            "No webhook endpoints configured. "
            "For local testing, use: stripe listen --forward-to localhost:3000/api/stripe/webhook"
        )
    
    return response


def test_customers(api_key, verbose=False):
    """List recent customers."""
    result, error = make_stripe_request("customers?limit=5", api_key)
    
    if error:
        return {
            "success": False,
            "test": "customers",
            "error": str(error)
        }
    
    customers = result.get("data", [])
    
    response = {
        "success": True,
        "test": "customers",
        "count": len(customers),
        "has_more": result.get("has_more", False)
    }
    
    if verbose:
        response["customers"] = [
            {
                "id": c.get("id"),
                "email": c.get("email"),
                "name": c.get("name"),
                "created": c.get("created")
            }
            for c in customers
        ]
    else:
        response["customers"] = [
            {"id": c.get("id"), "email": c.get("email")}
            for c in customers
        ]
    
    return response


def test_subscriptions(api_key, verbose=False):
    """List active subscriptions."""
    result, error = make_stripe_request(
        "subscriptions?limit=5&status=active", api_key
    )
    
    if error:
        return {
            "success": False,
            "test": "subscriptions",
            "error": str(error)
        }
    
    subscriptions = result.get("data", [])
    
    response = {
        "success": True,
        "test": "subscriptions",
        "count": len(subscriptions),
        "has_more": result.get("has_more", False)
    }
    
    if verbose:
        response["subscriptions"] = [
            {
                "id": s.get("id"),
                "status": s.get("status"),
                "customer": s.get("customer"),
                "current_period_end": s.get("current_period_end")
            }
            for s in subscriptions
        ]
    else:
        response["subscriptions"] = [
            {"id": s.get("id"), "status": s.get("status")}
            for s in subscriptions
        ]
    
    return response


def run_all_tests(api_key, verbose=False):
    """Run all tests."""
    tests = [
        ("connection", test_connection),
        ("products", test_products),
        ("webhooks", test_webhooks),
        ("customers", test_customers),
        ("subscriptions", test_subscriptions)
    ]
    
    results = []
    all_success = True
    
    for name, test_func in tests:
        result = test_func(api_key, verbose)
        results.append(result)
        if not result.get("success"):
            all_success = False
    
    return {
        "success": all_success,
        "tests_run": len(results),
        "results": results
    }


def main():
    parser = argparse.ArgumentParser(
        description="Test Stripe API connection and configuration"
    )
    parser.add_argument(
        "--test",
        type=str,
        choices=['connection', 'products', 'webhooks', 'customers', 'subscriptions'],
        help="Test to run"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    
    args = parser.parse_args()
    
    # Load API key
    api_key, error = load_api_key()
    if error:
        print(json.dumps({
            "success": False,
            "error": error,
            "suggestion": "Add STRIPE_SECRET_KEY to .env file"
        }, indent=2))
        sys.exit(1)
    
    # Run tests
    if args.all:
        result = run_all_tests(api_key, args.verbose)
    elif args.test == "connection":
        result = test_connection(api_key, args.verbose)
    elif args.test == "products":
        result = test_products(api_key, args.verbose)
    elif args.test == "webhooks":
        result = test_webhooks(api_key, args.verbose)
    elif args.test == "customers":
        result = test_customers(api_key, args.verbose)
    elif args.test == "subscriptions":
        result = test_subscriptions(api_key, args.verbose)
    else:
        parser.print_help()
        sys.exit(1)
    
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
