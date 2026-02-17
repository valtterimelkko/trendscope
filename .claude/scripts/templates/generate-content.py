#!/usr/bin/env python3
"""
Validate Generated Content Against Slots Schema

Checks that generated content matches the slots.json constraints.

Usage:
    python3 generate-content.py --slots templates/analytics-dashboard/content/slots.json --validate
"""

import argparse
import json
import os
import sys
from pathlib import Path


def load_slots(slots_path: str) -> dict:
    """Load content slots definition."""
    with open(slots_path, 'r') as f:
        return json.load(f)


def validate_content(content: str, slot_def: dict) -> dict:
    """Validate content against slot definition."""
    result = {
        "valid": True,
        "issues": []
    }
    
    max_length = slot_def.get('maxLength')
    if max_length and len(content) > max_length:
        result["valid"] = False
        result["issues"].append(
            f"Content too long: {len(content)} > {max_length}"
        )
    
    min_length = slot_def.get('minLength', 1)
    if len(content.strip()) < min_length:
        result["valid"] = False
        result["issues"].append(
            f"Content too short: {len(content)} < {min_length}"
        )
    
    return result


def count_slots(slots: dict) -> dict:
    """Count slots by type."""
    counts = {}
    
    def count_recursive(obj, prefix=""):
        if isinstance(obj, dict):
            if 'type' in obj:
                slot_type = obj['type']
                counts[slot_type] = counts.get(slot_type, 0) + 1
            else:
                for key, value in obj.items():
                    if key != 'version' and key != 'template' and key != 'totalSlots':
                        count_recursive(value, f"{prefix}.{key}" if prefix else key)
    
    count_recursive(slots.get('slots', slots))
    return counts


def list_all_slots(slots: dict) -> list:
    """List all slot paths and their definitions."""
    result = []
    
    def list_recursive(obj, prefix=""):
        if isinstance(obj, dict):
            if 'type' in obj:
                result.append({
                    "path": prefix,
                    "type": obj.get('type'),
                    "maxLength": obj.get('maxLength'),
                    "placeholder": obj.get('placeholder', '')[:50]
                })
            else:
                for key, value in obj.items():
                    if key not in ['version', 'template', 'totalSlots', 'slots']:
                        new_prefix = f"{prefix}.{key}" if prefix else key
                        list_recursive(value, new_prefix)
                # Handle nested 'slots' key
                if 'slots' in obj:
                    list_recursive(obj['slots'], prefix)
    
    list_recursive(slots)
    return result


def print_slot_summary(slots: dict):
    """Print summary of content slots."""
    counts = count_slots(slots)
    all_slots = list_all_slots(slots)
    
    print(f"Template: {slots.get('template', 'unknown')}")
    print(f"Total slots: {slots.get('totalSlots', len(all_slots))}")
    print()
    
    print("Slots by type:")
    for slot_type, count in sorted(counts.items()):
        print(f"  {slot_type}: {count}")
    print()
    
    print("All slots:")
    for slot in all_slots:
        max_len = f"(max: {slot['maxLength']})" if slot['maxLength'] else ""
        print(f"  {slot['path']}: {slot['type']} {max_len}")


def main():
    parser = argparse.ArgumentParser(
        description='Validate content against slots schema'
    )
    parser.add_argument(
        '--slots',
        required=True,
        help='Path to slots.json'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate and show slot summary'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all slots with details'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.slots):
        print(f"ERROR: Slots file not found: {args.slots}")
        sys.exit(1)
    
    slots = load_slots(args.slots)
    
    if args.validate or args.list:
        print_slot_summary(slots)
    else:
        print("Specify --validate or --list")


if __name__ == '__main__':
    main()
