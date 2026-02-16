#!/usr/bin/env python3
"""
List Supabase organizations the user has access to.

Usage:
    python3 list_organizations.py
"""

import sys
sys.path.insert(0, '/root/.shared/scripts/supabase')

from supabase_api import (
    management_api_request,
    output_success,
    output_error
)


def main():
    success, response = management_api_request("GET", "/organizations")
    
    if not success:
        error_msg = response.get("message", response.get("error", "Unknown error"))
        output_error(f"Failed to list organizations: {error_msg}")
    
    orgs = []
    for org in response:
        orgs.append({
            "id": org.get("id"),
            "name": org.get("name"),
            "billing_email": org.get("billing_email")
        })
    
    output_success(orgs, f"Found {len(orgs)} organization(s)")


if __name__ == "__main__":
    main()
