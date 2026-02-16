#!/usr/bin/env python3
"""
Create a new Supabase project.

Usage:
    python3 create_project.py --name "My Project" --region "us-east-1"
    python3 create_project.py --name "My Project" --org-id "org_xxx" --db-pass "securepass123"
    python3 create_project.py --name "My Project" --wait --save-credentials
"""

import argparse
import secrets
import string
import time
import sys
sys.path.insert(0, '/root/.shared/scripts/supabase')

from supabase_api import (
    management_api_request,
    get_default_org_id,
    save_project,
    output_success,
    output_error,
    output_info
)


# Available regions
REGIONS = [
    "us-east-1",      # North Virginia
    "us-west-1",      # North California
    "ap-northeast-1", # Tokyo
    "ap-northeast-2", # Seoul
    "ap-south-1",     # Mumbai
    "ap-southeast-1", # Singapore
    "ap-southeast-2", # Sydney
    "eu-central-1",   # Frankfurt
    "eu-west-1",      # Ireland
    "eu-west-2",      # London
    "eu-west-3",      # Paris
    "sa-east-1",      # Sao Paulo
]


def generate_password(length=24):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    # Ensure at least one of each type
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]
    # Fill the rest
    password += [secrets.choice(alphabet) for _ in range(length - 4)]
    # Shuffle
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


def wait_for_project(ref, max_wait=180, interval=10):
    """Wait for project to become ACTIVE_HEALTHY."""
    elapsed = 0
    while elapsed < max_wait:
        success, project = management_api_request("GET", f"/projects/{ref}")
        if success and project.get("status") == "ACTIVE_HEALTHY":
            return True, project
        output_info(f"Waiting for project... status: {project.get('status', 'unknown')}")
        time.sleep(interval)
        elapsed += interval
    return False, None


def main():
    parser = argparse.ArgumentParser(
        description="Create a new Supabase project"
    )
    parser.add_argument("--name", required=True, help="Project name")
    parser.add_argument("--org-id", help="Organization ID (uses default)")
    parser.add_argument("--region", default="eu-central-1",
                        choices=REGIONS, help="AWS region")
    parser.add_argument("--db-pass", help="Database password (auto-generated)")
    parser.add_argument("--plan", default="free", choices=["free", "pro"],
                        help="Pricing plan")
    parser.add_argument("--wait", action="store_true",
                        help="Wait for project to be ready")
    parser.add_argument("--save-credentials", action="store_true",
                        help="Auto-save credentials after creation")

    args = parser.parse_args()

    # Get org ID
    org_id = args.org_id or get_default_org_id()
    if not org_id:
        output_error(
            "Organization ID required. Use --org-id or set SUPABASE_ORG_ID."
        )

    # Generate password if not provided
    db_password = args.db_pass or generate_password()

    # Build request
    data = {
        "name": args.name,
        "organization_id": org_id,
        "region": args.region,
        "plan": args.plan,
        "db_pass": db_password
    }

    success, response = management_api_request("POST", "/projects", data=data)

    if not success:
        error_msg = response.get("message", response.get("error", "Unknown"))
        output_error(f"Failed to create project: {error_msg}")

    project_ref = response.get("ref")
    
    result = {
        "id": response.get("id"),
        "ref": project_ref,
        "name": response.get("name"),
        "region": response.get("region"),
        "status": response.get("status"),
        "endpoint": f"https://{project_ref}.supabase.co",
        "database_password": db_password,
        "database_url": f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
    }

    # Wait for project if requested
    if args.wait:
        output_info("Waiting for project to be ready...")
        ready, project = wait_for_project(project_ref)
        if ready:
            result["status"] = "ACTIVE_HEALTHY"
        else:
            result["status"] = "TIMEOUT_WAITING"
            result["warning"] = "Project not ready yet, check status later"

    # Save credentials if requested
    if args.save_credentials and result.get("status") == "ACTIVE_HEALTHY":
        # Fetch API keys
        keys_success, keys = management_api_request(
            "GET", f"/projects/{project_ref}/api-keys"
        )
        
        if keys_success and isinstance(keys, list):
            anon_key = ""
            service_key = ""
            for key in keys:
                if key.get("name") == "anon":
                    anon_key = key.get("api_key", "")
                elif key.get("name") == "service_role":
                    service_key = key.get("api_key", "")
            
            # Save to projects file
            save_project(project_ref, {
                "name": args.name,
                "anon_key": anon_key,
                "service_role_key": service_key,
                "database_url": result["database_url"]
            })
            result["credentials_saved"] = True
            result["anon_key"] = anon_key
            result["service_role_key"] = service_key

    if not args.save_credentials:
        result["next_steps"] = [
            "Wait for status: ACTIVE_HEALTHY (use --wait flag)",
            "Run with --save-credentials to auto-save all credentials",
            "Or manually save with save_project_credentials.py"
        ]

    output_success(result, f"Project '{args.name}' creation initiated")


if __name__ == "__main__":
    main()
