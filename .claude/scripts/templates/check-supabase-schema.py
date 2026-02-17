#!/usr/bin/env python3
"""
Validate Supabase migration files.
Usage: python3 check-supabase-schema.py <migrations-dir>
"""

import os
import re
import sys
import json


REQUIRED_TABLES = [
    "profiles",
    "teams",
    "team_members",
    "customers",
    "subscriptions",
]

RLS_PATTERN = re.compile(
    r'ALTER\s+TABLE\s+[\w.]+\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY',
    re.IGNORECASE
)

POLICY_PATTERN = re.compile(
    r'CREATE\s+POLICY\s+',
    re.IGNORECASE
)


def extract_tables(sql_content: str) -> list:
    """Extract table names from CREATE TABLE statements."""
    pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?(\w+)'
    matches = re.findall(pattern, sql_content, re.IGNORECASE)
    return matches


def check_rls_enabled(sql_content: str, table_name: str) -> bool:
    """Check if RLS is enabled for a table."""
    pattern = rf'ALTER\s+TABLE\s+(?:public\.)?{table_name}\s+ENABLE\s+ROW\s+LEVEL'
    return bool(re.search(pattern, sql_content, re.IGNORECASE))


def count_policies(sql_content: str, table_name: str) -> int:
    """Count policies for a specific table."""
    # Match policy names with or without quotes, including spaces in quoted names
    pattern = rf'CREATE\s+POLICY\s+(?:"[^"]+"|\'[^\']+\'|\w+)\s+ON\s+(?:public\.)?{table_name}'
    matches = re.findall(pattern, sql_content, re.IGNORECASE)
    return len(matches)


def validate_migrations(migrations_dir: str) -> tuple:
    """Validate all migration files in directory."""
    blockers = []
    warnings = []

    if not os.path.isdir(migrations_dir):
        blockers.append(f"Directory not found: {migrations_dir}")
        return blockers, warnings

    # Get all SQL files
    sql_files = sorted([
        f for f in os.listdir(migrations_dir)
        if f.endswith('.sql')
    ])

    if not sql_files:
        blockers.append("No .sql migration files found")
        return blockers, warnings

    # Check sequential numbering
    expected_num = 1
    for f in sql_files:
        match = re.match(r'^(\d+)', f)
        if match:
            num = int(match.group(1))
            if num != expected_num:
                warnings.append(
                    f"Non-sequential migration: expected {expected_num:05d}, "
                    f"got {num:05d}"
                )
            expected_num = num + 1

    # Combine all SQL content
    all_sql = ""
    for f in sql_files:
        file_path = os.path.join(migrations_dir, f)
        try:
            with open(file_path, 'r') as fp:
                content = fp.read()
                all_sql += f"\n-- File: {f}\n" + content

                # Check for syntax issues
                if content.count('(') != content.count(')'):
                    warnings.append(f"{f}: Unbalanced parentheses")

        except Exception as e:
            blockers.append(f"Error reading {f}: {e}")

    # Check required tables
    defined_tables = extract_tables(all_sql)
    for table in REQUIRED_TABLES:
        if table not in defined_tables:
            blockers.append(f"Missing required table: {table}")

    # Check RLS for user-data tables
    user_tables = ["profiles", "teams", "team_members", "subscriptions"]
    for table in user_tables:
        if table in defined_tables:
            if not check_rls_enabled(all_sql, table):
                blockers.append(f"RLS not enabled on table: {table}")
            elif count_policies(all_sql, table) == 0:
                blockers.append(f"No RLS policies defined for table: {table}")

    # Check for dangerous patterns
    danger_patterns = [
        (r'DROP\s+TABLE', "DROP TABLE without IF EXISTS"),
        (r'TRUNCATE', "TRUNCATE statement found"),
        (r'DELETE\s+FROM\s+\w+\s*;', "DELETE without WHERE clause"),
    ]

    for pattern, message in danger_patterns:
        if re.search(pattern, all_sql, re.IGNORECASE):
            warnings.append(f"Potentially dangerous: {message}")

    return blockers, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check-supabase-schema.py <migrations-dir>")
        sys.exit(1)

    migrations_dir = sys.argv[1]
    blockers, warnings = validate_migrations(migrations_dir)

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
            print("✅ Supabase schema valid")

    # Exit codes
    if blockers:
        sys.exit(1)
    elif warnings:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
