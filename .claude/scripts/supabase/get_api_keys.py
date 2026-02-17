#!/usr/bin/env python3
"""
Get API keys for a Supabase project.

Usage:
    python3 get_api_keys.py --ref "abcdefghijklmnopqrst"
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
    parser = argparse.ArgumentParser(description="Get Supabase project API keys")
    parser.add_argument("--ref", required=True, help="Project reference ID")
    
    args = parser.parse_args()
    
    success, response = management_api_request(
        "GET", f"/projects/{args.ref}/api-keys"
    )
    
    if not success:
        error_msg = response.get("message", response.get("error", "Unknown"))
        output_error(f"Failed to get API keys: {error_msg}")
    
    keys = {}
    for key in response:
        key_name = key.get("name", "unknown")
        keys[key_name] = {
            "api_key": key.get("api_key"),
            "name": key_name
        }
    
    result = {
        "project_ref": args.ref,
        "keys": keys,
        "usage": {
            "anon_key": "Use for client-side requests (respects RLS)",
            "service_role": "Use for server-side/admin (bypasses RLS)"
        }
    }
    
    output_success(result)


if __name__ == "__main__":
    main()
