---
name: notion-create-project
description: Create a new project in the Notion Projects database. Use when the user wants to start a new project, add a project for organizing notes, or set up a new work initiative in the Ultimate Brain system.
---

# Create Project in Notion

Create a new project in the Ultimate Brain Notion Projects database.


## Prerequisites

Set the `NOTION_TOKEN` environment variable:
```bash
export NOTION_TOKEN="your-notion-integration-token"
```
[Get your token →](https://www.notion.so/my-integrations)
## When to Use

Use this Skill when the user wants to:
- Create a new project
- Start organizing notes under a new project
- Set up a new work initiative or area

## How to Execute

### Create Project with Default Status

Creates a project with status "Doing":

```bash
python3 .shared/scripts/notion/create_project.py --name "My New Project"
```

### Create Project with Custom Status

Available statuses: Planned, On Hold, Doing, Ongoing, Done

```bash
python3 .shared/scripts/notion/create_project.py --name "My New Project" --status "Planned"
```

## Default Behavior

- **Status**: New projects are created with status "Doing" by default
- **Archived**: Projects are created as not archived

## Handling Results

- Parse the JSON output from the script
- If `success` is `true`: Return the project ID and URL so user can navigate to it
- If there's an error: Report the error message

## Example Interaction

User: "Create a project called 'Website Redesign'"

1. Execute create_project.py with the name
2. Return the project ID and Notion URL
3. Offer to add notes to the project or list existing notes

## Important Notes

- Project names should be descriptive and unique
- The project ID can be used with `notion-add-note-to-project` to link notes
- Use `notion-list-projects` to see all existing projects
