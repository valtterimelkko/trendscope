# GLM-5 Handoff Document - Trendscope

**Date:** 2026-02-16  
**Project:** Trendscope (trendscope.io) - TikTok Trend Intelligence Platform  
**Status:** Ready for Phase 4.3+ Implementation  
**Handoff From:** Kimi Code CLI (Phases 0-4.2)  
**Handoff To:** GLM-5 (Phases 4.3-7.1)

---

## Executive Summary

All planning phases complete. Trendscope is a real-time TikTok trend detection platform using self-hosted scraping (TikTok-Api + IPRoyal proxies) with a Next.js/Supabase web app and Python FastAPI scraper service.

**Key Decision:** Frontend is being built separately by another agent. GLM-5 should focus on:
- Backend API implementation (FastAPI)
- Database schema implementation (Supabase)
- Scraper integration and trend detection engine
- Alert delivery system
- Stripe webhook handlers

---

## Deliverables Inventory

### Core Documents (Phase 1-2)

| Document | Path | Purpose |
|----------|------|---------|
| Master Concept | `docs/concept/master-concept.md` | Product vision, MoSCoW scope, personas |
| Brand Kit | `docs/brand/brand-kit-guide.md` | Colors (#0F172A, #3B82F6), typography (Inter), voice |
| UX Design | `docs/mvp-ux-trendscope.md` | User flows, screen specs, 4 states |
| Technical PRD | `docs/Project-Technical-Architecture.md` | Architecture, API contracts, 6 stages |
| Git Structure | `docs/Git-Branch-Structure.md` | Branch naming, workflow for AI agents |

### Marketing Foundation (Phase 1.4)

| Document | Path | Purpose |
|----------|------|---------|
| Positioning Angles | `marketing/positioning-angles.md` | "Bloomberg Terminal" primary angle |
| Direct Response Copy | `marketing/direct-response-copy.md` | Landing page copy, email sequences |
| Lead Magnet | `marketing/lead-magnet.md` | Lead magnet strategies |
| SEO Content | `marketing/seo-content.md` | Content strategy |
| Keyword Research | `marketing/keyword-research.md` | Search terms |

### Background Technical Research

| Document | Path | Purpose |
|----------|------|---------|
| Tech Feasibility | `background_files/TECH_FEASIBILITY.md` | Detailed scraping analysis, algorithms |
| Self-Hosted Guide | `background_files/SELF_HOSTED.md` | TikTok-Api implementation guide |

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      TRENDSCOPE PLATFORM                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  WEB APP (Next.js + Supabase)                    PYTHON     │
│  ┌─────────────────────────────┐                 SCRAPER    │
│  │  Frontend                   │                 SERVICE    │
│  │  - Dashboard                │                 (FastAPI)  │
│  │  - Niche management         │                            │
│  │  - Alert preferences        │    ┌──────────────────┐   │
│  │  - Subscription mgmt        │    │ TikTok-Api       │   │
│  └──────────┬──────────────────┘    │ + IPRoyal Proxy  │   │
│             │                       └────────┬─────────┘   │
│             │                                │             │
│  ┌──────────▼──────────────────┐    ┌────────▼─────────┐   │
│  │  Supabase                   │    │ Redis Queue      │   │
│  │  - Auth                     │    │ (Hot Cache 72hr) │   │
│  │  - PostgreSQL (Trends)      │◄───┤                  │   │
│  │  - RLS Policies             │    └──────────────────┘   │
│  └─────────────────────────────┘                            │
│                                                              │
│  EXTERNAL SERVICES:                                          │
│  - Stripe (payments)                                         │
│  - Slack API (alerts)                                        │
│  - Email service (SendGrid/Resend)                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | Next.js 14+ (App Router), TypeScript, Tailwind | **Being built separately** |
| Auth | Supabase Auth | Email/password + OAuth |
| Database | Supabase PostgreSQL | 11 tables with RLS policies defined |
| Cache/Queue | Redis | 72-hour TTL for hot window |
| Scraper | Python 3.11+, FastAPI, TikTok-Api | Self-hosted with IPRoyal proxies |
| Payments | Stripe | 4-tier subscriptions |
| Hosting | Vercel (web), VPS (scraper) | Existing VPS available |

---

## Implementation Stages (From Technical PRD)

GLM-5 should implement these 6 stages:

### Stage 1: Backend API Foundation (6-8 hours)
- FastAPI project setup
- Database models (SQLAlchemy)
- Supabase client integration
- Basic CRUD endpoints

### Stage 2: Stripe Integration (4-6 hours)
- Stripe webhook handlers
- Subscription lifecycle
- Tier enforcement middleware

### Stage 3: Scraper Service (8-10 hours)
- TikTok-Api integration
- Redis producer-consumer
- IPRoyal proxy rotation
- Rate limiting, circuit breaker

### Stage 4: Trend Detection Engine (6-8 hours)
- Velocity calculation (R² > 0.85)
- Doubling time analysis
- Adaptive percentile thresholds
- Trend classification

### Stage 5: Alert Delivery System (6-8 hours)
- Slack webhook integration
- Email service integration
- Alert throttling/deduplication
- Delivery status tracking

### Stage 6: Monitoring & Observability (4-6 hours)
- Prometheus metrics
- Health checks
- Structured logging
- Error tracking

**Total Estimated:** 36-48 hours of autonomous work

---

## Database Schema (11 Tables)

See `docs/Project-Technical-Architecture.md` Section 3.1 for complete schema.

Key tables:
- `profiles` (users, tier, preferences)
- `niches` (available niches)
- `user_niches` (user selections)
- `trends` (detected trends with velocity)
- `alerts` (sent alerts with status)
- `alert_channels` (Slack webhooks, emails)
- `clients` (Agency tier - multi-tenant)
- `subscriptions` (Stripe subscription data)
- `trend_snapshots` (hourly velocity history)
- `scraper_jobs` (job queue tracking)
- `system_metrics` (performance data)

**RLS policies defined for all tables.**

---

## API Contracts

See `docs/Project-Technical-Architecture.md` Section 3.3 for complete API documentation.

Key endpoints:
- `GET /api/v1/trends` - List trends with filters
- `GET /api/v1/trends/{id}` - Trend detail
- `GET /api/v1/alerts` - User's alert history
- `POST /webhooks/stripe` - Stripe events
- `GET /health` - Service health check
- `GET /metrics` - Prometheus metrics

---

## Critical Implementation Notes

### 1. Self-Hosted Scraping (Not Template)
The TikTok scraper is a **separate Python service**, not part of the Next.js template:
- Runs on existing VPS
- Uses TikTok-Api library (Playwright-based)
- IPRoyal rotating residential proxies (credentials in `.env`)
- See `background_files/SELF_HOSTED.md` for detailed implementation

### 2. Data Flow
```
TikTok Scraper → Redis Queue → Trend Processor → PostgreSQL → API → Frontend
                    ↓
              (72hr hot window, velocity calc)
```

### 3. Cost Target
- **Web app:** Vercel hobby (free) → Pro ($20/mo) at scale
- **Scraper:** Existing VPS (sunk cost) + IPRoyal (~$7-45/mo)
- **Supabase:** Free tier → Pro ($25/mo) at scale
- **Total target:** $7-45/month initially

### 4. Alert Latency by Tier
- **Free:** Weekly digest only
- **Solo ($29):** 2-hour latency
- **Agency ($199):** 30-minute latency  
- **Enterprise ($499):** Real-time (immediate)

### 5. Frontend Being Built Separately
The user is building the frontend with another agent. GLM-5 should:
- Focus on backend/scraper implementation
- Provide clear API contracts for frontend integration
- Not implement frontend components

---

## Git Workflow

See `docs/Git-Branch-Structure.md` for complete workflow.

**Branch naming:**
```
ai/feat/coder/S<stage>-<ticket>/<description>

Examples:
ai/feat/coder/S01-001/setup-fastapi-project
ai/feat/coder/S03-004/implement-tiktok-scraper
```

**Strategy:** Linear with Stage Prefixes (sequential development)

---

## Environment Variables

Key variables (see `.env` for existing values):

```bash
# Database
SUPABASE_URL=
SUPABASE_SERVICE_KEY=

# Redis
REDIS_URL=redis://localhost:6379/0

# Stripe
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_SOLO=
STRIPE_PRICE_AGENCY=
STRIPE_PRICE_ENTERPRISE=

# Scraper
PROXY_URL=http://user:pass@geo.iproyal.com:12321
SCRAPE_RATE_LIMIT=10

# Alerts
SLACK_WEBHOOK_SECRET=
SENDGRID_API_KEY=

# App
APP_ENV=production
LOG_LEVEL=INFO
```

---

## Open Questions (From Technical PRD)

1. **Email service provider:** SendGrid vs Resend vs AWS SES?
2. **SMS provider:** Twilio vs AWS SNS? (Enterprise tier only)
3. **Niche seed list:** Initial 20 niches to populate database?
4. **Alert suppression rules:** Known campaigns to exclude?
5. **Visual similarity:** MVP excludes this (post-MVP feature)?

---

## Security Requirements

### Supabase RLS
All tables must have RLS policies. See Technical PRD Section 6 for:
- Function classification (internal/public/admin)
- RLS matrix per table
- SECURITY DEFINER usage policy
- Immutable `search_path = 'public'` requirement
- RPC exposure constraints

### Key Security Patterns
- Use `security definer` functions with `search_path = 'public'`
- Validate all user inputs
- Rate limit API endpoints
- Encrypt sensitive data at rest
- Never expose API keys in frontend

---

## Success Criteria

### Phase 4.3-4.4 (Template Integration & Planning)
- [ ] Template selected and integrated (or custom base created)
- [ ] Database schema implemented in Supabase
- [ ] RLS policies active
- [ ] Environment variables configured
- [ ] Stage plans detailed

### Phase 6 (Implementation)
- [ ] All 6 stages complete
- [ ] API endpoints functional
- [ ] Scraper ingesting data
- [ ] Trend detection working
- [ ] Alerts delivering
- [ ] Stripe billing active

### Phase 7 (Completion)
- [ ] End-to-end testing passes
- [ ] Documentation complete
- [ ] Monitoring active
- [ ] Production deployment ready

---

## Contact & Escalation

**Project Owner:** User (via Co-CEO Session)  
**Frontend:** Being built by separate agent  
**Kimi Phases Complete:** 0.0 - 4.2  
**GLM-5 Phases:** 4.3 - 7.1

---

## Quick Start for GLM-5

1. **Read these documents in order:**
   - `docs/GLM5_HANDOFF.md` (this file)
   - `docs/Project-Technical-Architecture.md`
   - `docs/mvp-ux-trendscope.md`
   - `background_files/SELF_HOSTED.md`

2. **Verify infrastructure:**
   - Check `.env` for required credentials
   - Confirm Supabase project access
   - Confirm Stripe account setup

3. **Start with Phase 4.3:**
   - Template integration (or custom base)
   - Database schema creation
   - RLS policy implementation

4. **Proceed to Phase 4.4:**
   - Detailed stage planning
   - Task breakdown

---

**Ready for implementation. Good luck! 🚀**

---

*Document created: 2026-02-16*  
*Last updated: 2026-02-16*  
*Version: 1.0*
