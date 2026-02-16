#!/usr/bin/env python3
"""
Get database connection string for a Supabase project.

Usage:
    python3 get_connection_string.py --ref "abcdefghij"
"""

import argparse
import sys
sys.path.insert(0, '/root/.shared/scripts/supabase')

from supabase_api import (
    management_api_request,
    output_success,
    output_error
)


def main():
    parser = argparse.ArgumentParser(
        description="Get Supabase database connection info"
    )
    parser.add_argument("--ref", required=True, help="Project reference ID")
    
    args = parser.parse_args()
    
    # Get project settings which includes DB info
    success, response = management_api_request(
        "GET", f"/projects/{args.ref}/settings/database"
    )
    
    if not success:
        # Fallback: construct from standard pattern
        result = {
            "note": "Could not fetch from API, using standard pattern",
            "host": f"db.{args.ref}.supabase.co",
            "port": 5432,
            "database": "postgres",
            "connection_string_template": (
                f"postgresql://postgres:[PASSWORD]@db.{args.ref}.supabase.co:5432/postgres"
            ),
            "pooler_connection_template": (
                f"postgresql://postgres.[args.ref]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres"
            ),
            "instructions": [
                "Replace [PASSWORD] with your database password",
                "Use pooler for connection pooling (recommended for serverless)",
                "Find password in Supabase Dashboard > Settings > Database"
            ]
        }
        output_success(result, "Constructed connection info from standard pattern")
        return
    
    result = {
        "host": response.get("host"),
        "port": response.get("port", 5432),
        "database": response.get("database", "postgres"),
        "pool_mode": response.get("pool_mode"),
        "connection_string": response.get("connection_string"),
        "pooler_connection_string": response.get("pooler_connection_string")
    }
    
    output_success(result)


if __name__ == "__main__":
    main()
