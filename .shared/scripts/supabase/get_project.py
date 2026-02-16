#!/usr/bin/env python3
"""
Get Supabase project details and API keys.

Usage:
    python3 get_project.py --ref "abcdefghijklmnopqrst"
    python3 get_project.py --ref "abcdefghijklmnopqrst" --include-keys
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
    parser = argparse.ArgumentParser(description="Get Supabase project details")
    parser.add_argument("--ref", required=True, help="Project reference ID")
    parser.add_argument("--include-keys", action="store_true",
                        help="Include API keys in response")
    
    args = parser.parse_args()
    
    # Get project details
    success, project = management_api_request("GET", f"/projects/{args.ref}")
    
    if not success:
        error_msg = project.get("message", project.get("error", "Unknown"))
        output_error(f"Failed to get project: {error_msg}")
    
    result = {
        "id": project.get("id"),
        "ref": project.get("ref"),
        "name": project.get("name"),
        "organization_id": project.get("organization_id"),
        "region": project.get("region"),
        "status": project.get("status"),
        "created_at": project.get("created_at"),
        "database": project.get("database", {}),
        "endpoint": f"https://{args.ref}.supabase.co",
        "rest_url": f"https://{args.ref}.supabase.co/rest/v1",
        "auth_url": f"https://{args.ref}.supabase.co/auth/v1"
    }
    
    # Optionally get API keys
    if args.include_keys:
        keys_success, keys = management_api_request(
            "GET", f"/projects/{args.ref}/api-keys"
        )
        
        if keys_success and isinstance(keys, list):
            result["api_keys"] = {}
            for key in keys:
                key_name = key.get("name", "unknown")
                result["api_keys"][key_name] = key.get("api_key")
    
    output_success(result)


if __name__ == "__main__":
    main()
