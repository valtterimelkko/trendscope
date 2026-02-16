#!/usr/bin/env python3
"""
Autosuggest Scraper - Google/Bing Autocomplete Mining

Expands seed keywords using search engine autocomplete suggestions.
No API key required.

Usage:
    python autosuggest.py --seed "project management"
    python autosuggest.py --seed "saas" --depth 2 --engine google
    python autosuggest.py --seed "billing software" --alphabetic
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
import ssl

# Disable SSL verification for autocomplete requests (they're read-only)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def get_google_suggestions(query: str) -> list:
    """Fetch Google autocomplete suggestions for a query."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://suggestqueries.google.com/complete/search?client=firefox&q={encoded}"

        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
            if len(data) > 1 and isinstance(data[1], list):
                return data[1]
    except Exception as e:
        pass

    return []


def get_bing_suggestions(query: str) -> list:
    """Fetch Bing autocomplete suggestions for a query."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.bing.com/osjson.aspx?query={encoded}"

        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
            if len(data) > 1 and isinstance(data[1], list):
                return data[1]
    except Exception as e:
        pass

    return []


def expand_with_alphabet(seed: str, engine: str = "google") -> dict:
    """Expand seed with alphabetic variations (seed a, seed b, ...)."""
    results = {}
    alphabet = "abcdefghijklmnopqrstuvwxyz"

    fetch_func = get_google_suggestions if engine == "google" else get_bing_suggestions

    for letter in alphabet:
        query = f"{seed} {letter}"
        suggestions = fetch_func(query)
        if suggestions:
            results[letter] = suggestions
        time.sleep(0.5)  # Rate limiting

    return results


def expand_with_modifiers(seed: str, engine: str = "google") -> dict:
    """Expand seed with common modifier patterns."""
    modifiers = [
        "how to",
        "best",
        "free",
        "vs",
        "alternative",
        "for small business",
        "for startups",
        "software",
        "tool",
        "app",
        "pricing",
        "review",
        "tutorial",
        "examples"
    ]

    results = {}
    fetch_func = get_google_suggestions if engine == "google" else get_bing_suggestions

    for modifier in modifiers:
        # Try both prefix and suffix patterns
        patterns = [
            f"{modifier} {seed}",
            f"{seed} {modifier}"
        ]

        for pattern in patterns:
            suggestions = fetch_func(pattern)
            if suggestions:
                key = pattern.replace(seed, "[seed]")
                results[key] = suggestions
            time.sleep(0.3)  # Rate limiting

    return results


def recursive_expand(seed: str, depth: int, engine: str = "google", seen: set = None) -> list:
    """Recursively expand suggestions to find long-tail keywords."""
    if seen is None:
        seen = set()

    if depth <= 0 or seed in seen:
        return []

    seen.add(seed)
    fetch_func = get_google_suggestions if engine == "google" else get_bing_suggestions

    suggestions = fetch_func(seed)
    all_suggestions = list(suggestions)

    if depth > 1:
        for suggestion in suggestions[:3]:  # Limit to top 3 to avoid explosion
            if suggestion not in seen:
                time.sleep(0.3)
                child_suggestions = recursive_expand(suggestion, depth - 1, engine, seen)
                all_suggestions.extend(child_suggestions)

    return list(set(all_suggestions))


def main():
    parser = argparse.ArgumentParser(description="Mine autocomplete suggestions for keyword research")
    parser.add_argument("--seed", required=True, help="Seed keyword to expand")
    parser.add_argument("--engine", default="google", choices=["google", "bing"], help="Search engine")
    parser.add_argument("--depth", type=int, default=1, help="Recursion depth (1-3)")
    parser.add_argument("--alphabetic", action="store_true", help="Expand with alphabetic variations")
    parser.add_argument("--modifiers", action="store_true", help="Expand with modifier patterns")
    parser.add_argument("--output", default="json", choices=["json", "list"], help="Output format")

    args = parser.parse_args()

    results = {
        "seed": args.seed,
        "engine": args.engine,
        "suggestions": [],
        "alphabetic": {},
        "modifiers": {},
        "errors": []
    }

    try:
        # Basic expansion
        print(f"Fetching suggestions for: {args.seed}", file=sys.stderr)
        base_suggestions = recursive_expand(args.seed, min(args.depth, 3), args.engine)
        results["suggestions"] = sorted(set(base_suggestions))

        # Alphabetic expansion
        if args.alphabetic:
            print("Expanding with alphabetic variations...", file=sys.stderr)
            results["alphabetic"] = expand_with_alphabet(args.seed, args.engine)

        # Modifier expansion
        if args.modifiers:
            print("Expanding with modifiers...", file=sys.stderr)
            results["modifiers"] = expand_with_modifiers(args.seed, args.engine)

    except Exception as e:
        results["errors"].append(str(e))

    if args.output == "json":
        print(json.dumps(results, indent=2))
    else:
        # Simple list output
        all_keywords = set(results["suggestions"])

        for letter_suggestions in results["alphabetic"].values():
            all_keywords.update(letter_suggestions)

        for modifier_suggestions in results["modifiers"].values():
            all_keywords.update(modifier_suggestions)

        for kw in sorted(all_keywords):
            print(kw)


if __name__ == "__main__":
    main()
