#!/usr/bin/env python3
"""
List all projects from the Notion Projects database.

This script queries the Projects database and returns all projects with pagination.
"""

import argparse
import requests
import time
from common import (
    PROJECTS_DB_ID, NOTION_BASE_URL, get_headers,
    build_archived_filter,
    output_success, output_error, extract_title
)


def extract_status(page):
    """Extract status from a project page."""
    status_prop = page.get('properties', {}).get('Status', {})
    if status_prop.get('type') == 'status':
        status_obj = status_prop.get('status', {})
        return status_obj.get('name', 'Unknown')
    return None


def list_projects(include_archived=False, limit=100):
    """
    List all projects from the Projects database.

    Args:
        include_archived: If True, include archived projects
        limit: Maximum results to return

    Returns:
        dict: Results with project list
    """
    headers = get_headers()

    # Build filters
    archived_filter = build_archived_filter(include_archived)

    # Build request body
    body = {
        "page_size": min(limit, 100)
    }
    if archived_filter:
        body["filter"] = archived_filter

    # Execute query with pagination
    url = f"{NOTION_BASE_URL}/databases/{PROJECTS_DB_ID}/query"
    all_results = []

    try:
        while True:
            response = requests.post(url, headers=headers, json=body, timeout=10)
            response.raise_for_status()

            data = response.json()
            all_results.extend(data.get('results', []))

            # Check if we have enough results or no more pages
            if len(all_results) >= limit or not data.get('has_more', False):
                break

            # Set up pagination
            body['start_cursor'] = data.get('next_cursor')
            time.sleep(0.3)  # Rate limiting
    except requests.exceptions.RequestException as e:
        output_error(f"API request failed: {str(e)}")

    # Limit results
    all_results = all_results[:limit]

    # Format results
    projects = []
    for project in all_results:
        projects.append({
            "id": project['id'],
            "name": extract_title(project),
            "status": extract_status(project),
            "archived": project.get('archived', False),
            "created": project.get('created_time'),
            "updated": project.get('last_edited_time')
        })

    output_success({
        "include_archived": include_archived,
        "count": len(projects),
        "projects": projects
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="List all projects from the Notion Projects database"
    )
    parser.add_argument("--include-archived", action="store_true", help="Include archived projects")
    parser.add_argument("--limit", type=int, default=100, help="Maximum results")

    args = parser.parse_args()

    list_projects(
        include_archived=args.include_archived,
        limit=args.limit
    )
