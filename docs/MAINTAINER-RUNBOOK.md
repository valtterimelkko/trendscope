# Maintainer Runbook

This document preserves maintainer-facing context now that the root `README.md` has been rewritten for public readers.

## Scope

Use this document for operational orientation and repo archaeology, not as the first entry point for outside adopters.

## Main reference areas

- Public overview and adoption caveats: [`../README.md`](../README.md)
- Frontend-specific notes: [`../frontend/README.md`](../frontend/README.md)
- Agent/orchestration entrypoints: [`../AGENTS.md`](../AGENTS.md), [`../CLAUDE.md`](../CLAUDE.md)
- Build/process history: [`../PROGRESS.md`](../PROGRESS.md)
- Architecture docs: [`../docs/`](../docs/)

## Repo shape

This repository mixes product code and project-process artefacts.

Main code/service areas include:
- `frontend/` - Next.js frontend
- `scraper/` - scraping service work
- `detection/` - trend detection logic
- `alerts/` - alerting pipeline work
- `monitoring/` - metrics and health aggregation
- `supabase/` - schema and migration work

There are also internal planning and agent-execution traces such as:
- `.claude/`
- `.glm5/`
- `.kimi/`
- `.shared/`

These are part of the repo's history as an AI-assisted build experiment and have not been fully normalised into a clean public starter kit.

## Important operational note

This repo should be understood as an unfinished experiment with meaningful backend work, not a polished monolithic application. Some internal docs describe states of the project that were true at the time they were written but should not be assumed to represent a final deployable setup.

## Notes for future maintainers

- Keep the public `README.md` focused on story, status, and adoption caveats.
- Treat security-sensitive generated artefacts as local-only and untracked.
- If you continue the project, one of the first cleanups should be separating product code from orchestration/process clutter.
