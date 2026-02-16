#!/usr/bin/env python3
"""
List tables in a Supabase project database.

Usage:
    python3 list_tables.py --ref "abcdefghij"
    python3 list_tables.py --ref "abcdefghij" --schema "public"
"""

import argparse
import sys
sys.path.insert(0, '/root/.shared/scripts/supabase')

from supabase_api import (
    execute_sql,
    output_success,
    output_error
)


SQL_LIST_TABLES = """
SELECT 
    table_schema,
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = '{schema}'
ORDER BY table_name;
"""

SQL_TABLE_DETAILS = """
SELECT 
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default
FROM information_schema.columns c
WHERE c.table_schema = '{schema}' AND c.table_name = '{table}'
ORDER BY c.ordinal_position;
"""


def main():
    parser = argparse.ArgumentParser(description="List Supabase tables")
    parser.add_argument("--ref", required=True, help="Project reference ID")
    parser.add_argument("--schema", default="public", help="Schema name")
    parser.add_argument("--table", help="Get columns for specific table")
    
    args = parser.parse_args()
    
    if args.table:
        sql = SQL_TABLE_DETAILS.format(schema=args.schema, table=args.table)
    else:
        sql = SQL_LIST_TABLES.format(schema=args.schema)
    
    success, result = execute_sql(args.ref, sql)
    
    if not success:
        output_error(f"Failed to list tables: {result.get('error')}")
    
    output_success({
        "schema": args.schema,
        "table": args.table,
        "output": result.get("output", "")
    })


if __name__ == "__main__":
    main()
