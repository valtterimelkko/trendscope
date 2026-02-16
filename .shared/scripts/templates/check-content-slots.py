#!/usr/bin/env python3
"""
Validate content/slots.json structure and completeness.
Usage: python3 check-content-slots.py <slots-json-path>
"""

import json
import sys


REQUIRED_CATEGORIES = ["landing", "dashboard", "errors", "auth"]

REQUIRED_SLOT_FIELDS = ["type", "maxLength"]

VALID_SLOT_TYPES = [
    "headline",
    "body",
    "button",
    "section_title",
    "feature_title",
    "empty_state",
    "error",
    "array",
]


def validate_slot(slot_key: str, slot_value: dict) -> list:
    """Validate a single slot definition."""
    issues = []

    if not isinstance(slot_value, dict):
        issues.append(f"Slot '{slot_key}' must be an object")
        return issues

    # Check required fields
    if "type" not in slot_value:
        issues.append(f"Slot '{slot_key}' missing required field: type")

    if slot_value.get("type") != "array" and "maxLength" not in slot_value:
        issues.append(f"Slot '{slot_key}' missing required field: maxLength")

    # Validate type
    slot_type = slot_value.get("type")
    if slot_type and slot_type not in VALID_SLOT_TYPES:
        issues.append(
            f"Slot '{slot_key}' has invalid type: {slot_type}. "
            f"Valid: {VALID_SLOT_TYPES}"
        )

    # Validate array slots
    if slot_type == "array":
        if "itemType" not in slot_value:
            issues.append(f"Array slot '{slot_key}' missing itemType")

    # Validate maxLength is positive
    max_len = slot_value.get("maxLength")
    if max_len is not None and (not isinstance(max_len, int) or max_len <= 0):
        issues.append(f"Slot '{slot_key}' maxLength must be a positive integer")

    return issues


def validate_slots_json(file_path: str) -> tuple:
    """Validate the entire slots.json file."""
    blockers = []
    warnings = []

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        blockers.append(f"Invalid JSON: {e}")
        return blockers, warnings, 0
    except FileNotFoundError:
        blockers.append(f"File not found: {file_path}")
        return blockers, warnings, 0

    # Check version field
    if "version" not in data:
        warnings.append("Missing 'version' field")

    # Check slots object
    if "slots" not in data:
        blockers.append("Missing 'slots' object")
        return blockers, warnings, 0

    slots = data["slots"]

    # Check required categories
    for category in REQUIRED_CATEGORIES:
        if category not in slots:
            blockers.append(f"Missing required category: {category}")

    # Count and validate all slots
    total_slots = 0
    for category, category_slots in slots.items():
        if not isinstance(category_slots, dict):
            blockers.append(f"Category '{category}' must be an object")
            continue

        for slot_key, slot_value in category_slots.items():
            total_slots += 1
            issues = validate_slot(f"{category}.{slot_key}", slot_value)
            blockers.extend(issues)

    return blockers, warnings, total_slots


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check-content-slots.py <slots-json-path>")
        sys.exit(1)

    file_path = sys.argv[1]
    blockers, warnings, total_slots = validate_slots_json(file_path)

    # JSON output mode
    if "--json" in sys.argv:
        result = {
            "status": "pass" if not blockers else "fail",
            "blockers": blockers,
            "warnings": warnings,
            "total_slots": total_slots,
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
            print(f"✅ Content slots valid ({total_slots} slots defined)")
        else:
            print(f"\nTotal slots: {total_slots}")

    # Exit codes: 0=pass, 1=blockers, 2=warnings only
    if blockers:
        sys.exit(1)
    elif warnings:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
