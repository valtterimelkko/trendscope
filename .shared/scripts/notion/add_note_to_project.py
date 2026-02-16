#!/usr/bin/env python3
"""
Add a note to a project by updating the note's Project relation.

This script updates the Project relation property of a note to include a project,
appending to any existing project relations.
"""

import argparse
import requests
import subprocess
import json
import os
from common import (
    NOTES_DB_ID, NOTION_BASE_URL, get_headers,
    build_title_filter, build_archived_filter, combine_filters,
    output_success, output_error, extract_title
)


def find_note_by_name(note_name):
    """
    Find a note by name.

    Args:
        note_name: Name of the note to find

    Returns:
        tuple: (note_id, note_title)
    """
    headers = get_headers()
    title_filter = build_title_filter(note_name)
    archived_filter = build_archived_filter(include_archived=False)
    combined_filter = combine_filters(title_filter, archived_filter)

    body = {"page_size": 20}
    if combined_filter:
        body["filter"] = combined_filter

    url = f"{NOTION_BASE_URL}/databases/{NOTES_DB_ID}/query"

    try:
        response = requests.post(url, headers=headers, json=body, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        output_error(f"API request failed: {str(e)}")

    results = response.json().get('results', [])

    if not results:
        output_error(f"No notes found matching '{note_name}'")

    # Check for exact match
    exact_matches = [r for r in results if extract_title(r).lower() == note_name.lower()]
    if exact_matches:
        return exact_matches[0]['id'], extract_title(exact_matches[0])

    # If multiple matches, ask for clarification
    if len(results) > 1:
        matches = [extract_title(r) for r in results[:5]]
        output_error(
            f"Multiple notes match '{note_name}'. Please be more specific:",
            {"matches": matches}
        )

    return results[0]['id'], extract_title(results[0])


def get_project_id_from_name(project_name):
    """
    Find project ID by searching for project name.

    Args:
        project_name: Name of the project to find

    Returns:
        tuple: (project_id, project_name)
    """
    script_path = os.path.join(os.path.dirname(__file__), "search_projects.py")
    if not os.path.exists(script_path):
        fallback_paths = [
            os.path.expanduser("~/.shared/scripts/notion/search_projects.py")
        ]
        for path in fallback_paths:
            if os.path.exists(path):
                script_path = path
                break

    try:
        # First try: exact match (case-insensitive)
        result = subprocess.run(
            ["python3", script_path,
             "--name", project_name, "--exact", "--limit", "10"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # If exact match fails, try partial match
        if result.returncode != 0:
            result = subprocess.run(
                ["python3", script_path,
                 "--name", project_name, "--limit", "10"],
                capture_output=True,
                text=True,
                timeout=10
            )

        if result.returncode != 0:
            output_error(f"Project '{project_name}' not found. Try using list_projects.py to see available projects.")

        data = json.loads(result.stdout)
        if not data['success']:
            output_error(f"Project '{project_name}' not found. Try using list_projects.py to see available projects.")

        projects = data['data']['projects']
        if len(projects) == 0:
            output_error(f"No projects found matching '{project_name}'. Try using list_projects.py to see available projects.")
        elif len(projects) > 1:
            output_error(
                f"Multiple projects match '{project_name}'. Please be more specific:",
                {"matches": [p['name'] for p in projects]}
            )

        return projects[0]['id'], projects[0]['name']
    except Exception as e:
        output_error(f"Failed to search for project: {str(e)}")


def get_current_project_relations(note_id):
    """
    Get current project relations for a note.

    Args:
        note_id: Note ID

    Returns:
        list: List of current project relation IDs
    """
    headers = get_headers()
    url = f"{NOTION_BASE_URL}/pages/{note_id}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        output_error(f"Failed to fetch note: {str(e)}")

    page = response.json()
    project_prop = page.get('properties', {}).get('Project', {})

    if project_prop.get('type') == 'relation':
        relations = project_prop.get('relation', [])
        return [r.get('id') for r in relations if r.get('id')]

    return []


def add_note_to_project(note_id=None, note_name=None, project_id=None, project_name=None):
    """
    Add a note to a project by updating the Project relation.

    Args:
        note_id: Note ID (if not provided, note_name is required)
        note_name: Note name to search for
        project_id: Project ID (if not provided, project_name is required)
        project_name: Project name to search for
    """
    # Resolve note name to ID if needed
    resolved_note_name = None
    if note_name and not note_id:
        note_id, resolved_note_name = find_note_by_name(note_name)
    elif note_id:
        # Get note title for response
        headers = get_headers()
        url = f"{NOTION_BASE_URL}/pages/{note_id}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            resolved_note_name = extract_title(response.json())
        except:
            resolved_note_name = "Unknown"

    if not note_id:
        output_error("Either --note-id or --note-name must be provided")

    # Resolve project name to ID if needed
    resolved_project_name = None
    if project_name and not project_id:
        project_id, resolved_project_name = get_project_id_from_name(project_name)
    elif project_id:
        resolved_project_name = project_name or "Unknown"

    if not project_id:
        output_error("Either --project-id or --project-name must be provided")

    # Get current project relations to append to
    current_relations = get_current_project_relations(note_id)

    # Check if already related
    if project_id in current_relations:
        output_success({
            "action": "add_to_project",
            "note": {
                "id": note_id,
                "name": resolved_note_name
            },
            "project": {
                "id": project_id,
                "name": resolved_project_name
            },
            "message": "Note is already in this project",
            "already_related": True
        })
        return

    # Append new project to existing relations
    new_relations = [{"id": pid} for pid in current_relations]
    new_relations.append({"id": project_id})

    # Update the note's Project relation
    headers = get_headers()
    url = f"{NOTION_BASE_URL}/pages/{note_id}"

    update_data = {
        "properties": {
            "Project": {
                "relation": new_relations
            }
        }
    }

    try:
        response = requests.patch(url, headers=headers, json=update_data, timeout=10)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = response.json().get('message', str(e))
        except:
            error_detail = str(e)
        output_error(f"Failed to update note: {error_detail}")
    except requests.exceptions.RequestException as e:
        output_error(f"Failed to update note: {str(e)}")

    output_success({
        "action": "add_to_project",
        "note": {
            "id": note_id,
            "name": resolved_note_name
        },
        "project": {
            "id": project_id,
            "name": resolved_project_name
        },
        "previous_project_count": len(current_relations),
        "new_project_count": len(new_relations)
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add a note to a project by updating the Project relation"
    )
    parser.add_argument("--note-id", help="Note ID to update")
    parser.add_argument("--note-name", help="Note name to search for")
    parser.add_argument("--project-id", help="Project ID to add")
    parser.add_argument("--project-name", help="Project name to search for")

    args = parser.parse_args()

    if not args.note_id and not args.note_name:
        output_error("Either --note-id or --note-name must be provided")

    if not args.project_id and not args.project_name:
        output_error("Either --project-id or --project-name must be provided")

    add_note_to_project(
        note_id=args.note_id,
        note_name=args.note_name,
        project_id=args.project_id,
        project_name=args.project_name
    )
