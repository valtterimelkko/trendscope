#!/usr/bin/env python3
"""
Validate brand tokens CSS file for required variables.
Usage: python3 check-brand-tokens.py <tokens-css-path>
"""

import re
import sys
import json


REQUIRED_COLOR_TOKENS = [
    "--color-primary",
    "--color-secondary",
    "--color-accent",
    "--color-background",
    "--color-foreground",
    "--color-muted",
]

REQUIRED_SEMANTIC_TOKENS = [
    "--color-success",
    "--color-warning",
    "--color-error",
    "--color-info",
]

REQUIRED_TYPOGRAPHY_TOKENS = [
    "--font-display",
    "--font-body",
]

REQUIRED_SPACING_TOKENS = [
    "--spacing-xs",
    "--spacing-sm",
    "--spacing-md",
    "--spacing-lg",
    "--spacing-xl",
]

REQUIRED_RADIUS_TOKENS = [
    "--radius-sm",
    "--radius-md",
    "--radius-lg",
]


def extract_css_variables(css_content: str) -> set:
    """Extract all CSS variable definitions from content."""
    pattern = r'(--[a-zA-Z0-9-]+)\s*:'
    matches = re.findall(pattern, css_content)
    return set(matches)


def check_dark_mode(css_content: str) -> bool:
    """Check if dark mode variables are defined."""
    return '.dark' in css_content or '[data-theme="dark"]' in css_content


def validate_tokens(file_path: str) -> tuple:
    """Validate the tokens.css file."""
    blockers = []
    warnings = []

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        blockers.append(f"File not found: {file_path}")
        return blockers, warnings

    defined_vars = extract_css_variables(content)

    # Check required color tokens
    all_required = (
        REQUIRED_COLOR_TOKENS +
        REQUIRED_SEMANTIC_TOKENS +
        REQUIRED_TYPOGRAPHY_TOKENS +
        REQUIRED_SPACING_TOKENS +
        REQUIRED_RADIUS_TOKENS
    )

    missing = []
    for token in all_required:
        if token not in defined_vars:
            missing.append(token)

    if missing:
        blockers.append(f"Missing required tokens: {', '.join(missing)}")

    # Check dark mode
    if not check_dark_mode(content):
        warnings.append("No dark mode (.dark) styles defined")

    # Check for common issues
    if 'rgb(' in content.lower() and 'var(--' not in content:
        warnings.append("Consider using CSS variables instead of raw RGB")

    return blockers, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check-brand-tokens.py <tokens-css-path>")
        sys.exit(1)

    file_path = sys.argv[1]
    blockers, warnings = validate_tokens(file_path)

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
            print("✅ Brand tokens valid")

    # Exit codes
    if blockers:
        sys.exit(1)
    elif warnings:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
