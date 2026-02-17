#!/usr/bin/env python3
"""
Stripe Billing Documentation Pattern Lookup

Provides code patterns and implementation guidance for Stripe billing features.
No API key required - uses bundled pattern definitions.

Usage:
    python3 lookup_pattern.py --pattern "webhook-handler"
    python3 lookup_pattern.py --list
    python3 lookup_pattern.py --search "trial"
"""

import argparse
import json
import os
import sys

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PATTERNS_FILE = os.path.join(SCRIPT_DIR, 'patterns.json')


def load_patterns():
    """Load patterns from JSON file."""
    if not os.path.exists(PATTERNS_FILE):
        print(json.dumps({
            "success": False,
            "error": f"Patterns file not found: {PATTERNS_FILE}"
        }, indent=2))
        sys.exit(1)
    
    with open(PATTERNS_FILE, 'r') as f:
        return json.load(f)


def list_patterns(patterns):
    """List all available patterns."""
    result = {
        "success": True,
        "patterns": []
    }
    
    for name, pattern in patterns.items():
        result["patterns"].append({
            "name": name,
            "description": pattern.get("description", ""),
            "category": pattern.get("category", "general")
        })
    
    print(json.dumps(result, indent=2))


def search_patterns(patterns, keyword):
    """Search patterns by keyword."""
    keyword_lower = keyword.lower()
    matches = []
    
    for name, pattern in patterns.items():
        # Search in name, description, and tags
        searchable = f"{name} {pattern.get('description', '')} {' '.join(pattern.get('tags', []))}"
        if keyword_lower in searchable.lower():
            matches.append({
                "name": name,
                "description": pattern.get("description", ""),
                "category": pattern.get("category", "general")
            })
    
    print(json.dumps({
        "success": True,
        "query": keyword,
        "matches": matches,
        "count": len(matches)
    }, indent=2))


def lookup_pattern(patterns, pattern_name):
    """Lookup a specific pattern by name."""
    # Normalize pattern name
    pattern_key = pattern_name.lower().replace(" ", "-").replace("_", "-")
    
    if pattern_key not in patterns:
        # Try fuzzy match
        for key in patterns.keys():
            if pattern_key in key or key in pattern_key:
                pattern_key = key
                break
        else:
            print(json.dumps({
                "success": False,
                "error": f"Pattern '{pattern_name}' not found",
                "available_patterns": list(patterns.keys())
            }, indent=2))
            sys.exit(1)
    
    pattern = patterns[pattern_key]
    
    print(json.dumps({
        "success": True,
        "pattern": pattern_key,
        "description": pattern.get("description", ""),
        "category": pattern.get("category", "general"),
        "code": pattern.get("code", ""),
        "language": pattern.get("language", "typescript"),
        "notes": pattern.get("notes", []),
        "related_patterns": pattern.get("related", []),
        "stripe_docs_url": pattern.get("docs_url", "")
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Lookup Stripe billing documentation patterns"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help="Pattern name to lookup"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available patterns"
    )
    parser.add_argument(
        "--search",
        type=str,
        help="Search patterns by keyword"
    )
    
    args = parser.parse_args()
    
    # Load patterns
    patterns = load_patterns()
    
    if args.list:
        list_patterns(patterns)
    elif args.search:
        search_patterns(patterns, args.search)
    elif args.pattern:
        lookup_pattern(patterns, args.pattern)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
