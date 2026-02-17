#!/usr/bin/env python3
"""
Stripe Webhook Handler Checker

Audits webhook handler files for completeness against required Stripe events.
No API key required - analyzes source code only.

Usage:
    python3 check_webhooks.py --file "path/to/webhook/route.ts"
    python3 check_webhooks.py --all
    python3 check_webhooks.py --file "path/to/route.ts" --model "usage-based"
"""

import argparse
import json
import os
import re
import sys
import glob

# Event definitions by priority
CORE_EVENTS = {
    "checkout.session.completed": {
        "priority": "required",
        "description": "User completed checkout"
    },
    "customer.subscription.created": {
        "priority": "required", 
        "description": "New subscription started"
    },
    "customer.subscription.updated": {
        "priority": "required",
        "description": "Subscription changed (upgrade/downgrade/renewal)"
    },
    "customer.subscription.deleted": {
        "priority": "required",
        "description": "Subscription canceled or expired"
    },
    "invoice.payment_succeeded": {
        "priority": "required",
        "description": "Payment successful"
    },
    "invoice.payment_failed": {
        "priority": "required",
        "description": "Payment failed - start dunning"
    }
}

TRIAL_EVENTS = {
    "customer.subscription.trial_will_end": {
        "priority": "recommended",
        "description": "3 days before trial ends"
    }
}

DUNNING_EVENTS = {
    "invoice.payment_action_required": {
        "priority": "recommended",
        "description": "SCA/3D Secure required"
    },
    "invoice.upcoming": {
        "priority": "optional",
        "description": "Preview of next invoice"
    }
}

USAGE_EVENTS = {
    "v1.billing.meter.error_report_triggered": {
        "priority": "recommended",
        "description": "Meter event validation errors"
    }
}

CUSTOMER_EVENTS = {
    "customer.created": {
        "priority": "optional",
        "description": "New customer created in Stripe"
    },
    "customer.updated": {
        "priority": "optional",
        "description": "Customer details changed"
    }
}


def get_all_events(billing_model=None):
    """Get all events, optionally filtered by billing model."""
    events = {}
    events.update(CORE_EVENTS)
    events.update(TRIAL_EVENTS)
    events.update(DUNNING_EVENTS)
    events.update(CUSTOMER_EVENTS)
    
    if billing_model == 'usage-based':
        events.update(USAGE_EVENTS)
    
    return events


def extract_handled_events(file_path):
    """Extract event types handled in a webhook file."""
    if not os.path.exists(file_path):
        return None, f"File not found: {file_path}"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return None, f"Error reading file: {str(e)}"
    
    # Find all event type strings in case statements or if conditions
    # Patterns:
    # - case 'event.type':
    # - case "event.type":
    # - event.type === 'event.type'
    # - event.type === "event.type"
    
    patterns = [
        r"case\s+['\"]([a-z_\.]+)['\"]",  # case 'event.type'
        r"event\.type\s*===?\s*['\"]([a-z_\.]+)['\"]",  # event.type === 'x'
        r"type\s*===?\s*['\"]([a-z_\.]+)['\"]",  # type === 'x'
    ]
    
    handled = set()
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        handled.update(matches)
    
    return list(handled), None


def check_webhook_file(file_path, billing_model=None):
    """Check a single webhook handler file for completeness."""
    result = {
        "success": True,
        "file": file_path,
        "billingModel": billing_model,
        "coverage": {
            "handled": [],
            "missing_required": [],
            "missing_recommended": [],
            "missing_optional": []
        },
        "score": "0%",
        "summary": ""
    }
    
    # Extract handled events
    handled, error = extract_handled_events(file_path)
    if error:
        result["success"] = False
        result["summary"] = error
        return result
    
    result["coverage"]["handled"] = sorted(handled)
    
    # Get expected events
    all_events = get_all_events(billing_model)
    
    # Categorize missing events
    required_count = 0
    required_handled = 0
    
    for event, info in all_events.items():
        if event in handled:
            if info["priority"] == "required":
                required_count += 1
                required_handled += 1
            continue
        
        missing_item = {
            "event": event,
            "description": info["description"]
        }
        
        if info["priority"] == "required":
            required_count += 1
            result["coverage"]["missing_required"].append(missing_item)
        elif info["priority"] == "recommended":
            result["coverage"]["missing_recommended"].append(missing_item)
        else:
            result["coverage"]["missing_optional"].append(missing_item)
    
    # Calculate score
    total_events = len(all_events)
    handled_count = len([e for e in handled if e in all_events])
    score = int((handled_count / total_events) * 100) if total_events > 0 else 0
    result["score"] = f"{score}%"
    
    # Check if all required events are handled
    if result["coverage"]["missing_required"]:
        result["success"] = False
        result["summary"] = (
            f"Missing {len(result['coverage']['missing_required'])} required events. "
            "Billing will not work correctly."
        )
    elif result["coverage"]["missing_recommended"]:
        result["summary"] = (
            f"Good coverage ({score}%). "
            f"Missing {len(result['coverage']['missing_recommended'])} recommended events."
        )
    else:
        result["summary"] = f"Excellent coverage ({score}%)."
    
    return result


def find_webhook_files():
    """Find all webhook handler files in templates."""
    patterns = [
        'templates/*/frontend/app/api/stripe/webhook/route.ts',
        'templates/*/frontend/app/api/stripe/webhook/route.js',
        'templates/**/api/stripe/webhook/route.ts',
        'templates/**/api/webhooks/stripe/route.ts'
    ]
    
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern, recursive=True))
    
    return list(set(files))


def detect_billing_model(file_path):
    """Try to detect billing model from template structure."""
    # Look for products.json in the same template
    parts = file_path.split('/')
    if 'templates' in parts:
        template_idx = parts.index('templates')
        if template_idx + 1 < len(parts):
            template_name = parts[template_idx + 1]
            products_path = f"templates/{template_name}/stripe/products.json"
            
            if os.path.exists(products_path):
                try:
                    with open(products_path, 'r') as f:
                        config = json.load(f)
                    return config.get('billingModel')
                except:
                    pass
    
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Check Stripe webhook handler completeness"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to webhook handler file"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check all templates"
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=['usage-based', 'seat-based', 'feature-limits', 'flat-rate'],
        help="Billing model for model-specific checks"
    )
    
    args = parser.parse_args()
    
    if args.all:
        files = find_webhook_files()
        if not files:
            print(json.dumps({
                "success": False,
                "error": "No webhook handler files found in templates/"
            }, indent=2))
            sys.exit(1)
        
        results = []
        all_success = True
        
        for file_path in files:
            billing_model = args.model or detect_billing_model(file_path)
            result = check_webhook_file(file_path, billing_model)
            results.append(result)
            if not result["success"]:
                all_success = False
        
        print(json.dumps({
            "success": all_success,
            "files_checked": len(results),
            "results": results
        }, indent=2))
        
        sys.exit(0 if all_success else 1)
    
    elif args.file:
        billing_model = args.model or detect_billing_model(args.file)
        result = check_webhook_file(args.file, billing_model)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["success"] else 1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
