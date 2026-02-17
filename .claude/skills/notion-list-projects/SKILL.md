---
name: notion-list-projects
description: List all projects from the Notion Projects database. Use when the user wants to see available projects, find project IDs, or get an overview of their project portfolio in the Ultimate Brain system.
---

# List Projects in Notion

List all projects from the Ultimate Brain Notion Projects database with pagination support.


## Prerequisites

Set the `NOTION_TOKEN` environment variable:
```bash
export NOTION_TOKEN="your-notion-integration-token"
```
[Get your token →](https://www.notion.so/my-integrations)
## When to Use

Use this Skill when the user wants to:
- See all available projects
- Find a project ID for other operations
- Get an overview of their project portfolio
- Check project statuses

## How to Execute

### List All Projects

```bash
python3 .shared/scripts/notion/list_projects.py
```

### Include Archived Projects

```bash
python3 .shared/scripts/notion/list_projects.py --include-archived
```

### Limit Results

```bash
python3 .shared/scripts/notion/list_projects.py --limit 20
```

## Handling Results

- Parse the JSON output from the script
- If `success` is `true`: Present the projects list in a readable format
- Each project includes: id, name, status, archived flag, created/updated timestamps

## Example Output Format for User

Present results like this:

```
Found 5 projects:

1. ProductMotion.app
   Status: Ongoing
   ID: 2bf45010-ad5d-8016-a523-d572399c0ebe

2. Server Infrastructure
   Status: Doing
   ID: 2bf45010-ad5d-8016-b124-c462625bacf9

3. API Documentation
   Status: Planned
   ID: 2bf45010-ad5d-801c-bd8f-ebfa1ddd9bb7

[...]
```

## Important Notes

- By default, archived projects are excluded
- Project IDs can be used with `notion-list-project-notes`, `notion-add-note-to-project`, and other skills
- Status values include: Planned, On Hold, Doing, Ongoing, Done
