#!/usr/bin/env python3
"""
Save Supabase project credentials for local use.

This saves credentials to /etc/supabase/projects.json so other scripts
can access the project without requiring manual credential entry.

Usage:
    python3 save_project_credentials.py --ref "abcdefghij" \
        --anon-key "eyJ..." \
        --service-key "eyJ..." \
        --db-url "postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres"
"""

import argparse
import json
import os
import sys
sys.path.insert(0, '/root/.shared/scripts/supabase')

from supabase_api import (
    save_project,
    load_projects,
    output_success,
    output_error
)


PROJECTS_FILE = "/etc/supabase/projects.json"


def main():
    parser = argparse.ArgumentParser(
        description="Save Supabase project credentials"
    )
    parser.add_argument("--ref",
                        help="Project reference ID (20 chars)")
    parser.add_argument("--anon-key",
                        help="Anonymous/public API key")
    parser.add_argument("--service-key", 
                        help="Service role API key (admin access)")
    parser.add_argument("--db-url", 
                        help="Direct database connection URL")
    parser.add_argument("--name", 
                        help="Human-readable project name")
    parser.add_argument("--list", action="store_true",
                        help="List saved projects instead of saving")
    
    args = parser.parse_args()
    
    # List mode
    if args.list:
        projects = load_projects()
        if not projects:
            output_success([], "No saved projects")
            return
        
        result = []
        for ref, data in projects.items():
            result.append({
                "ref": ref,
                "name": data.get("name", "Unnamed"),
                "has_anon_key": bool(data.get("anon_key")),
                "has_service_key": bool(data.get("service_role_key")),
                "has_db_url": bool(data.get("database_url"))
            })
        output_success(result, f"Found {len(result)} saved project(s)")
        return
    
    # Save mode - ref required
    if not args.ref:
        output_error("--ref is required when saving credentials")
    
    # Save mode - at least one credential required
    if not any([args.anon_key, args.service_key, args.db_url]):
        output_error(
            "At least one credential required: --anon-key, --service-key, or --db-url"
        )
    
    # Load existing or create new
    projects = load_projects()
    existing = projects.get(args.ref, {})
    
    # Update with new values
    project_data = {
        "name": args.name or existing.get("name", args.ref),
        "anon_key": args.anon_key or existing.get("anon_key", ""),
        "service_role_key": args.service_key or existing.get("service_role_key", ""),
        "database_url": args.db_url or existing.get("database_url", "")
    }
    
    try:
        save_project(args.ref, project_data)
    except Exception as e:
        output_error(f"Failed to save credentials: {e}")
    
    output_success({
        "ref": args.ref,
        "name": project_data["name"],
        "saved_to": PROJECTS_FILE,
        "credentials": {
            "anon_key": bool(project_data["anon_key"]),
            "service_role_key": bool(project_data["service_role_key"]),
            "database_url": bool(project_data["database_url"])
        }
    }, f"Credentials saved for project '{args.ref}'")


if __name__ == "__main__":
    main()
