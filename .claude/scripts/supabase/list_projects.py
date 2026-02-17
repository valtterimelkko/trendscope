#!/usr/bin/env python3
"""
List all Supabase projects.

Usage:
    python3 list_projects.py
"""

import sys
sys.path.insert(0, '/root/.shared/scripts/supabase')

from supabase_api import (
    management_api_request,
    output_success,
    output_error
)


def main():
    success, response = management_api_request("GET", "/projects")
    
    if not success:
        error_msg = response.get("message", response.get("error", "Unknown"))
        output_error(f"Failed to list projects: {error_msg}")
    
    projects = []
    for proj in response:
        projects.append({
            "id": proj.get("id"),
            "ref": proj.get("ref"),
            "name": proj.get("name"),
            "organization_id": proj.get("organization_id"),
            "region": proj.get("region"),
            "status": proj.get("status"),
            "created_at": proj.get("created_at")
        })
    
    output_success(projects, f"Found {len(projects)} project(s)")


if __name__ == "__main__":
    main()
