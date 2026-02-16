#!/usr/bin/env python3
"""
Insert, update, or delete data in a Supabase table.

Usage:
    # Insert single row
    python3 mutate_table.py --ref "xxx" --table "users" --insert '{"email":"a@b.com"}'
    
    # Insert multiple rows (batch)
    python3 mutate_table.py --ref "xxx" --table "users" \
        --insert '[{"email":"a@b.com"}, {"email":"c@d.com"}]'
    
    # Update
    python3 mutate_table.py --ref "xxx" --table "users" --update '{"status":"active"}' \
        --filter "id=eq.123"
    
    # Delete
    python3 mutate_table.py --ref "xxx" --table "users" --delete --filter "id=eq.123"
"""

import argparse
import json
import sys
sys.path.insert(0, '/root/.shared/scripts/supabase')

from supabase_api import (
    postgrest_request,
    output_success,
    output_error
)


def main():
    parser = argparse.ArgumentParser(description="Mutate Supabase table data")
    parser.add_argument("--ref", required=True, help="Project reference ID")
    parser.add_argument("--table", required=True, help="Table name")

    # Mutation type
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--insert",
                       help="JSON object or array to insert")
    group.add_argument("--update", help="JSON data to update")
    group.add_argument("--upsert",
                       help="JSON object or array to upsert")
    group.add_argument("--delete", action="store_true",
                       help="Delete matching rows")

    parser.add_argument("--filter", action="append",
                        help="PostgREST filter for update/delete")

    args = parser.parse_args()

    # Determine operation
    if args.insert:
        method = "POST"
        try:
            data = json.loads(args.insert)
        except json.JSONDecodeError:
            output_error("Invalid JSON for --insert")
        is_batch = isinstance(data, list)
    elif args.update:
        method = "PATCH"
        if not args.filter:
            output_error("--filter required for update")
        try:
            data = json.loads(args.update)
        except json.JSONDecodeError:
            output_error("Invalid JSON for --update")
        is_batch = False
    elif args.upsert:
        method = "POST"
        try:
            data = json.loads(args.upsert)
        except json.JSONDecodeError:
            output_error("Invalid JSON for --upsert")
        is_batch = isinstance(data, list)
    elif args.delete:
        method = "DELETE"
        if not args.filter:
            output_error("--filter required for delete")
        data = None
        is_batch = False

    success, response = postgrest_request(
        project_ref=args.ref,
        method=method,
        table=args.table,
        data=data,
        filters=args.filter
    )

    if not success:
        error_msg = response.get("message", response.get("error", "Unknown"))
        output_error(f"Operation failed: {error_msg}")

    affected = len(response) if isinstance(response, list) else 1
    result = {
        "operation": method,
        "table": args.table,
        "batch": is_batch,
        "affected": affected,
        "data": response
    }

    output_success(result, f"{method} completed: {affected} row(s)")


if __name__ == "__main__":
    main()
    main()
