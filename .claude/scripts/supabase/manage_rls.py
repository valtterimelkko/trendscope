#!/usr/bin/env python3
"""
Manage Row Level Security (RLS) policies on Supabase tables.

Usage:
    python3 manage_rls.py --ref "xxx" --table "posts" --enable
    python3 manage_rls.py --ref "xxx" --table "posts" --list
    python3 manage_rls.py --ref "xxx" --table "posts" --add-policy \
        --policy-name "Users can view own" \
        --operation "SELECT" \
        --using "auth.uid() = user_id"
"""

import argparse
import sys
sys.path.insert(0, '/root/.shared/scripts/supabase')

from supabase_api import (
    execute_sql,
    output_success,
    output_error
)


def main():
    parser = argparse.ArgumentParser(description="Manage Supabase RLS")
    parser.add_argument("--ref", required=True, help="Project reference ID")
    parser.add_argument("--table", required=True, help="Table name")
    parser.add_argument("--schema", default="public", help="Schema name")
    
    # Actions
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--enable", action="store_true", help="Enable RLS")
    group.add_argument("--disable", action="store_true", help="Disable RLS")
    group.add_argument("--list", action="store_true", help="List policies")
    group.add_argument("--add-policy", action="store_true", help="Add policy")
    group.add_argument("--drop-policy", help="Drop policy by name")
    
    # Policy options
    parser.add_argument("--policy-name", help="Policy name")
    parser.add_argument("--operation", 
                        choices=["SELECT", "INSERT", "UPDATE", "DELETE", "ALL"],
                        help="Operation for policy")
    parser.add_argument("--using", help="USING clause (for SELECT/UPDATE/DELETE)")
    parser.add_argument("--with-check", help="WITH CHECK clause (for INSERT/UPDATE)")
    
    args = parser.parse_args()
    full_table = f"{args.schema}.{args.table}"
    
    if args.enable:
        sql = f"ALTER TABLE {full_table} ENABLE ROW LEVEL SECURITY;"
        success, result = execute_sql(args.ref, sql)
        if not success:
            output_error(f"Failed to enable RLS: {result.get('error')}")
        output_success({"table": full_table, "rls_enabled": True})
        
    elif args.disable:
        sql = f"ALTER TABLE {full_table} DISABLE ROW LEVEL SECURITY;"
        success, result = execute_sql(args.ref, sql)
        if not success:
            output_error(f"Failed to disable RLS: {result.get('error')}")
        output_success({"table": full_table, "rls_enabled": False})
        
    elif args.list:
        sql = f"""
        SELECT 
            policyname,
            permissive,
            roles,
            cmd,
            qual,
            with_check
        FROM pg_policies
        WHERE schemaname = '{args.schema}' AND tablename = '{args.table}';
        """
        success, result = execute_sql(args.ref, sql)
        if not success:
            output_error(f"Failed to list policies: {result.get('error')}")
        output_success({
            "table": full_table,
            "policies": result.get("output", "No policies found")
        })
        
    elif args.add_policy:
        if not args.policy_name or not args.operation:
            output_error("--policy-name and --operation required")
        if not args.using and not args.with_check:
            output_error("At least one of --using or --with-check required")
        
        sql_parts = [
            f'CREATE POLICY "{args.policy_name}"',
            f"ON {full_table}",
            f"FOR {args.operation}"
        ]
        
        if args.using:
            sql_parts.append(f"USING ({args.using})")
        if args.with_check:
            sql_parts.append(f"WITH CHECK ({args.with_check})")
        
        sql = " ".join(sql_parts) + ";"
        
        success, result = execute_sql(args.ref, sql)
        if not success:
            output_error(f"Failed to create policy: {result.get('error')}")
        output_success({
            "table": full_table,
            "policy": args.policy_name,
            "created": True
        })
        
    elif args.drop_policy:
        sql = f'DROP POLICY IF EXISTS "{args.drop_policy}" ON {full_table};'
        success, result = execute_sql(args.ref, sql)
        if not success:
            output_error(f"Failed to drop policy: {result.get('error')}")
        output_success({
            "table": full_table,
            "policy": args.drop_policy,
            "dropped": True
        })


if __name__ == "__main__":
    main()
