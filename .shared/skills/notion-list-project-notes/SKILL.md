---
name: notion-list-project-notes
description: List all notes belonging to a Notion project. Use when the user wants to see all notes in a project, get an overview of project documentation, or find note IDs in the Ultimate Brain system.
---

# List Project Notes in Notion

List all notes in the Ultimate Brain Notion workspace that belong to a specific project.


## Prerequisites

Set the `NOTION_TOKEN` environment variable:
```bash
export NOTION_TOKEN="your-notion-integration-token"
```
[Get your token →](https://www.notion.so/my-integrations)
## When to Use

Use this Skill when the user wants to:
- See all notes in a project
- Get an overview of project documentation
- Find note IDs for further operations
- Review what's been documented for a project

## How to Execute

### List by Project Name

Run the list script with project name:

```bash
python3 .shared/scripts/notion/list_project_notes.py --project-name "PROJECT_NAME"
```

### List by Project ID

Run with project ID directly:

```bash
python3 .shared/scripts/notion/list_project_notes.py --project-id "PROJECT_ID"
```

### Include Archived Notes

If user wants archived notes too:

```bash
python3 .shared/scripts/notion/list_project_notes.py --project-name "PROJECT_NAME" --include-archived
```

## Handling Results

- Parse the JSON output from the script
- If `success` is `true`: Present the notes list to the user in a readable format
- If `success` is `false` and error is "Project not found":
  1. Try using `search_projects.py` to find the project with partial name matching:
     ```bash
     python3 .shared/scripts/notion/search_projects.py --name "PARTIAL_NAME"
     ```
  2. Once you find the correct project ID, retry with `--project-id`
- For other errors: Report the error and suggest alternatives

## Fallback: Search for Project First

If the project name doesn't match exactly, search for it first:

```bash
python3 .shared/scripts/notion/search_projects.py --name "PROJECT_NAME"
```

This returns matching projects with their IDs. Then use the ID with:

```bash
python3 .shared/scripts/notion/list_project_notes.py --project-id "PROJECT_ID"
```

## Example Output Format for User

Present results like this:

```
Found 5 notes in project "Serveri":

1. Commands to SCP html files
   ID: 2bf45010-ad5d-814f-9fed-cf53648c962c
   Updated: March 20, 2024

2. Server Configuration Guide
   ID: 2bf45010-ad5d-8150-abcd-1234567890ab
   Updated: March 18, 2024

3. Database Backup Procedures
   ID: 2bf45010-ad5d-8151-efgh-0987654321cd
   Updated: March 15, 2024

[...]
```

## Important Notes

- By default, archived notes are excluded
- If the project name is ambiguous, the script will return an error listing matching projects
- Note IDs can be used with the `notion-read-note` and `notion-edit-note` skills
