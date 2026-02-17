#!/usr/bin/env python3
"""
Execute raw SQL on a Supabase project's Postgres database.

Requires psql (postgresql-client) to be installed.

Usage:
    python3 execute_sql.py --ref "abcdefghij" --sql "SELECT * FROM users"
    python3 execute_sql.py --ref "abcdefghij" --file "/path/to/migration.sql"
    python3 execute_sql.py --ref "abcdefghij" --sql "DROP TABLE x" --dry-run
"""

import argparse
import sys
sys.path.insert(0, '/root/.shared/scripts/supabase')

from supabase_api import (
    execute_sql,
    execute_sql_file,
    output_success,
    output_error
)


def main():
    parser = argparse.ArgumentParser(description="Execute SQL on Supabase")
    parser.add_argument("--ref", required=True, help="Project reference ID")
    parser.add_argument("--sql", help="SQL statement to execute")
    parser.add_argument("--file", help="SQL file to execute")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print SQL without executing")

    args = parser.parse_args()

    if not args.sql and not args.file:
        output_error("Either --sql or --file is required")

    if args.sql and args.file:
        output_error("Use either --sql or --file, not both")

    # Get SQL content
    if args.file:
        try:
            with open(args.file, 'r') as f:
                sql_content = f.read()
        except FileNotFoundError:
            output_error(f"File not found: {args.file}")
        except Exception as e:
            output_error(f"Error reading file: {e}")
    else:
        sql_content = args.sql

    # Dry run - just show the SQL
    if args.dry_run:
        output_success({
            "mode": "dry-run",
            "sql": sql_content,
            "would_execute_on": args.ref
        }, "SQL preview (not executed)")
        return

    # Execute
    if args.file:
        success, result = execute_sql_file(args.ref, args.file)
    else:
        success, result = execute_sql(args.ref, args.sql)

    if not success:
        err = result.get('error', 'Unknown error')
        output_error(f"SQL execution failed: {err}")

    output_success(result, "SQL executed successfully")


if __name__ == "__main__":
    main()
