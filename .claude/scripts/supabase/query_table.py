#!/usr/bin/env python3
"""
Query data from a Supabase table using PostgREST API.

Usage:
    python3 query_table.py --ref "xxx" --table "users"
    python3 query_table.py --ref "xxx" --table "users" --select "id,email"
    python3 query_table.py --ref "xxx" --table "users" --filter "status=eq.active"
    python3 query_table.py --ref "xxx" --table "users" --limit 10 --order "created_at.desc"
"""

import argparse
import sys
sys.path.insert(0, '/root/.shared/scripts/supabase')

from supabase_api import (
    postgrest_request,
    output_success,
    output_error
)


def main():
    parser = argparse.ArgumentParser(description="Query Supabase table")
    parser.add_argument("--ref", required=True, help="Project reference ID")
    parser.add_argument("--table", required=True, help="Table name")
    parser.add_argument("--select", help="Columns to select (comma-separated)")
    parser.add_argument("--filter", action="append", 
                        help="PostgREST filter (can be repeated)")
    parser.add_argument("--limit", type=int, help="Limit results")
    parser.add_argument("--order", help="Order by (e.g., 'created_at.desc')")
    
    args = parser.parse_args()
    
    # Build params
    params = {}
    if args.limit:
        params["limit"] = str(args.limit)
    if args.order:
        params["order"] = args.order
    
    success, response = postgrest_request(
        project_ref=args.ref,
        method="GET",
        table=args.table,
        select=args.select,
        filters=args.filter,
        params=params
    )
    
    if not success:
        error_msg = response.get("message", response.get("error", "Unknown"))
        output_error(f"Query failed: {error_msg}")
    
    result = {
        "table": args.table,
        "count": len(response) if isinstance(response, list) else 0,
        "data": response
    }
    
    output_success(result)


if __name__ == "__main__":
    main()
