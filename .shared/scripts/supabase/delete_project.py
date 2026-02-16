#!/usr/bin/env python3
"""
Delete a Supabase project.

Usage:
    python3 delete_project.py --ref "abcdefghij"
    python3 delete_project.py --ref "abcdefghij" --confirm
"""

import argparse
import sys
sys.path.insert(0, '/root/.shared/scripts/supabase')

from supabase_api import (
    management_api_request,
    load_projects,
    output_success,
    output_error
)


PROJECTS_FILE = "/etc/supabase/projects.json"


def remove_saved_credentials(ref):
    """Remove project from saved credentials file."""
    import json
    projects = load_projects()
    if ref in projects:
        del projects[ref]
        try:
            with open(PROJECTS_FILE, 'w') as f:
                json.dump(projects, f, indent=2)
            return True
        except Exception:
            return False
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Delete a Supabase project"
    )
    parser.add_argument("--ref", required=True,
                        help="Project reference ID to delete")
    parser.add_argument("--confirm", action="store_true",
                        help="Confirm deletion (required for safety)")

    args = parser.parse_args()

    # Safety check
    if not args.confirm:
        # Get project name for confirmation message
        success, project = management_api_request(
            "GET", f"/projects/{args.ref}"
        )
        project_name = project.get("name", args.ref) if success else args.ref
        
        output_error(
            f"Deletion requires --confirm flag. "
            f"This will permanently delete project '{project_name}' "
            f"and all its data. Run with --confirm to proceed.",
            "CONFIRMATION_REQUIRED"
        )

    # Delete the project
    success, response = management_api_request(
        "DELETE", f"/projects/{args.ref}"
    )

    if not success:
        error_msg = response.get("message", response.get("error", "Unknown"))
        output_error(f"Failed to delete project: {error_msg}")

    # Remove from saved credentials
    creds_removed = remove_saved_credentials(args.ref)

    output_success({
        "ref": args.ref,
        "deleted": True,
        "credentials_removed": creds_removed
    }, f"Project '{args.ref}' deleted successfully")


if __name__ == "__main__":
    main()
