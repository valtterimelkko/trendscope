#!/usr/bin/env python3
"""
Create a new project in the Notion Projects database.

This script creates a new project page in the Projects database with a given name
and sets the status to "Doing" by default.
"""

import argparse
import requests
from common import (
    PROJECTS_DB_ID, NOTION_BASE_URL, get_headers,
    output_success, output_error
)

# Default status for new projects
DEFAULT_STATUS = "Doing"


def create_project(name, status=None):
    """
    Create a new project in the Projects database.

    Args:
        name: Name/title of the project (required)
        status: Status to set (defaults to "Doing")
    """
    if not name or not name.strip():
        output_error("Project name is required")

    if status is None:
        status = DEFAULT_STATUS

    headers = get_headers()

    # Build page creation payload
    page_data = {
        "parent": {
            "database_id": PROJECTS_DB_ID
        },
        "properties": {
            "Name": {
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": name.strip()
                        }
                    }
                ]
            },
            "Status": {
                "status": {
                    "name": status
                }
            }
        }
    }

    # Create the page
    url = f"{NOTION_BASE_URL}/pages"

    try:
        response = requests.post(url, headers=headers, json=page_data, timeout=10)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = response.json().get('message', str(e))
        except:
            error_detail = str(e)
        output_error(f"API request failed: {error_detail}")
    except requests.exceptions.RequestException as e:
        output_error(f"API request failed: {str(e)}")

    page = response.json()
    project_id = page.get('id')

    output_success({
        "action": "create",
        "project": {
            "id": project_id,
            "name": name.strip(),
            "status": status,
            "url": page.get('url', '')
        }
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a new project in the Notion Projects database"
    )
    parser.add_argument("--name", required=True, help="Name of the new project")
    parser.add_argument("--status", default=DEFAULT_STATUS,
                        help=f"Project status (default: {DEFAULT_STATUS})")

    args = parser.parse_args()

    create_project(
        name=args.name,
        status=args.status
    )
