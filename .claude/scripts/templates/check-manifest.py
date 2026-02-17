#!/usr/bin/env python3
"""
Validate manifest.json structure and content.
Usage: python3 check-manifest.py <manifest-path> <expected-name>
"""

import json
import re
import sys


REQUIRED_FIELDS = [
    "name",
    "displayName",
    "description",
    "version",
    "category",
    "techStack",
    "features",
    "brandTokens",
    "contentSlots",
]

VALID_CATEGORIES = ["analytics", "productivity", "content"]

REQUIRED_TECH_STACK = ["frontend", "database", "auth", "payments"]

MINIMUM_BRAND_TOKENS = ["--color-primary", "--font-display"]


def validate_semver(version: str) -> bool:
    """Check if version follows semver format."""
    return bool(re.match(r'^\d+\.\d+\.\d+$', version))


def validate_manifest(file_path: str, expected_name: str = None) -> tuple:
    """Validate the manifest.json file."""
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

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            blockers.append(f"Missing required field: {field}")

    # Validate name
    name = data.get("name", "")
    if name:
        if not re.match(r'^[a-z0-9-]+$', name):
            blockers.append(
                f"Name '{name}' must be lowercase with hyphens only"
            )
        if expected_name and name != expected_name:
            blockers.append(
                f"Name '{name}' doesn't match directory name '{expected_name}'"
            )

    # Validate version
    version = data.get("version", "")
    if version and not validate_semver(version):
        blockers.append(f"Version '{version}' must follow semver (X.Y.Z)")

    # Validate category
    category = data.get("category", "")
    if category and category not in VALID_CATEGORIES:
        blockers.append(
            f"Category '{category}' must be one of: {VALID_CATEGORIES}"
        )

    # Validate techStack
    tech_stack = data.get("techStack", {})
    if isinstance(tech_stack, dict):
        for field in REQUIRED_TECH_STACK:
            if field not in tech_stack:
                blockers.append(f"techStack missing field: {field}")
    else:
        blockers.append("techStack must be an object")

    # Validate features
    features = data.get("features", [])
    if isinstance(features, list):
        if len(features) < 3:
            warnings.append("features should have at least 3 items")
    else:
        blockers.append("features must be an array")

    # Validate brandTokens
    tokens = data.get("brandTokens", [])
    if isinstance(tokens, list):
        for req_token in MINIMUM_BRAND_TOKENS:
            if req_token not in tokens:
                blockers.append(f"brandTokens missing: {req_token}")
    else:
        blockers.append("brandTokens must be an array")

    # Validate contentSlots
    slots = data.get("contentSlots")
    if slots is not None:
        if not isinstance(slots, int) or slots < 1:
            blockers.append("contentSlots must be a positive integer")

    # Description length
    desc = data.get("description", "")
    if len(desc) < 50:
        warnings.append("description should be at least 50 characters")
    elif len(desc) > 200:
        warnings.append("description should be under 200 characters")

    return blockers, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check-manifest.py <manifest-path> [expected-name]")
        sys.exit(1)

    file_path = sys.argv[1]
    expected_name = sys.argv[2] if len(sys.argv) > 2 else None

    blockers, warnings = validate_manifest(file_path, expected_name)

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
        print("✅ Manifest valid")

    # Exit codes
    if blockers:
        sys.exit(1)
    elif warnings:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
