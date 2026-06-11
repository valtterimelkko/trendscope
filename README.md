# Trendscope

> An unfinished vibe-coding experiment in trend intelligence for short-form video markets.

## Important status note

**This repository is not a turnkey product and is not immediately adoptable as-is.**

Trendscope was built as an experiment in AI-assisted / "vibe coded" SaaS development. Some of the backend work became surprisingly solid, but the overall product never reached a finished public release state. The landing page remained incomplete, the dashboard was never fully carried through, and the exact trend-selection logic still needed much more refinement.

I am **not actively continuing development** on this project. My main focus is on building professional tools that support my day job more directly and make that work more efficient and meaningful. Still, this was a very dear experiment to me: I loved the idea, I still think it could become a good product, and I think someone else could meaningfully continue it.

If you want to take it forward, the intended path is to **fork it, finish the user-facing product, refine the ranking logic, and package it into a cleaner deployable system**.

## Project story

Trendscope began as a response to a startup idea prompt rather than a pure greenfield brainstorm.

I was inspired by **Greg Isenberg** ([@gregisenberg](https://x.com/gregisenberg)) and his broader startup-idea ecosystem around **IdeaBrowser**. Greg's public work often encourages people to take emerging behaviour, validated demand, and creator-market signals seriously — then actually ship something from that insight.

Useful context links:
- Greg Isenberg on X: [@gregisenberg](https://x.com/gregisenberg)
- IdeaBrowser: [ideabrowser.com](https://www.ideabrowser.com/)
- The specific IdeaBrowser prompt that pushed this repo forward: [TikTok trend tool that catches viral waves before they peak](https://www.ideabrowser.com/idea/ai-powered-trend-finder-for-scriptwriters-that-auto-generates-viral-topics-2659)

That idea was close enough to something I genuinely wanted to test that I decided to build it.

The bet behind Trendscope was that creators, agencies, and short-form operators need something closer to a Bloomberg Terminal for fast-moving social video trends: a system that can help identify emerging TikTok patterns before they become obvious, overused, or already saturated.

So this repo became one of my experiments in translating a strong startup prompt into an actual product build. I tested different approaches to scraping TikTok data, evaluated multiple API paths, and ended up with a backend direction that was much more real than the unfinished public surface might suggest.

What exists here is not just a fake shell. There is real implementation work around scraping, detection, monitoring, alerts, and supporting architecture. What remains unfinished is the part that outsiders would most need first: a fully convincing landing page, a properly finished dashboard, and a mature algorithm for deciding which trends are genuinely worth surfacing.

That is why the repo is interesting but not turnkey.

I still think the idea itself is strong.

If someone wanted to continue it today, they would probably:
- finish the public landing and positioning layer
- complete or redesign the dashboard UX
- refine the trend-ranking and opportunity-scoring logic
- tighten deployment and service packaging
- decide whether to keep the current backend approach or swap in newer data sources

## What is in the repo

At a high level, this repository contains:
- a Next.js frontend workspace in `frontend/`
- backend/service experimentation for scraping, detection, alerts, and monitoring
- Supabase-oriented product architecture work
- research, planning, and implementation-history artefacts from the build process

## Current maturity

What is relatively strong:
- backend experimentation
- service decomposition and architecture notes
- scraping and detection direction
- evidence that the concept can be implemented

What is still incomplete:
- finished landing page
- finished dashboard
- fully proven trend-selection logic
- packaging for outside adopters

## For potential adopters

If the idea resonates with you, treat this repo as:
- a documented experiment
- a backend-heavy prototype
- a fork-and-finish candidate

Do **not** treat it as a production-ready trend intelligence SaaS you can deploy unchanged.

## Documentation

- Public overview: this `README.md`
- Maintainer-oriented operational notes: [`docs/MAINTAINER-RUNBOOK.md`](docs/MAINTAINER-RUNBOOK.md)
- Frontend notes: [`frontend/README.md`](frontend/README.md)
- Agent/orchestration context: [`AGENTS.md`](AGENTS.md), [`CLAUDE.md`](CLAUDE.md), [`PROGRESS.md`](PROGRESS.md)

## Licence

[MIT](LICENSE)
