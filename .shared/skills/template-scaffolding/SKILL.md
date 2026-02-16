---
name: template-scaffolding
description: Generates complete MVP template directories (Analytics, Productivity, Content, Utility Processor, Digital Download) with Next.js frontend, Supabase backend, Google OAuth authentication, and Stripe billing. Use this skill to create the 5 core templates from research and benchmark materials.
---

# Template Scaffolding

## Overview

Generate production-ready MVP template directories from research documentation and benchmark captures. Each template includes a complete stack: Next.js 14+ frontend, Supabase database with RLS policies, authentication (including Google OAuth), and Stripe billing integration.

**Core principle:** Templates should be 80% complete MVPs that users customize via brand tokens and content slots. They follow established SaaS conventions—professional and familiar, not experimental.

**Consistency principle:** All 5 templates MUST feel like a cohesive system. They share the same:
- Directory structure
- Tech stack and dependencies
- Auth flow implementation
- Stripe billing integration
- Brand token naming conventions
- Content slot structure
- Design system (spacing, typography scale, color tokens)

Only the dashboard-specific components differ between templates.

**Reference:** See `SKILL-full.md` in this directory when you need:
- Complete code examples and boilerplate
- Detailed SQL schema migrations
- Full Stripe webhook implementations
- Every content slot definition

## When to Use

- Creating the 5 core templates for the meta-project (one-time internal use)
- Building a new template category
- Regenerating templates after significant research updates

## Pre-Requisites

```bash
# Verify required materials exist
ls -la SaaS_Frontend_Template_Research.md
ls -la .shared/scripts/benchmarking/scrape_results/
ls -la frontend_template_idea.md
```

## The 5 Templates

| Template | Directory | Personality | Research Section |
|----------|-----------|-------------|------------------|
| Analytics Dashboard | `templates/analytics-dashboard/` | Clean, trustworthy | Part I |
| Productivity Tool | `templates/productivity-tool/` | Fast, keyboard-first | Part II |
| Content Creator | `templates/content-creator/` | Creative, editorial | Part III |
| Utility Processor | `templates/utility-processor/` | Minimal, focused | 4th template benchmarking |
| Digital Download Portal | `templates/digital-download/` | Clean, trustworthy | 4th template benchmarking |

### Template-Specific Pages

Each template has shared pages (landing, auth, dashboard, settings) plus category-specific pages:

| Template | Extra Pages | Purpose |
|----------|-------------|---------|
| Analytics | `/settings/snippet` | Tracking code/embed snippet for users to install |
| Analytics | `/dashboard/public` | Public dashboard toggle and share settings |
| Productivity | (none extra) | SidePeek component handles item detail views |
| Content | `/connect`, `/queue` | Social account connect + scheduled queue |
| Utility Processor | `/dashboard/history` | Job history/logs |
| Digital Download | `/downloads`, `/billing` | Download locker + billing portal |

### Auth Page Personality

Auth pages (login, signup) must match the template's personality:

| Template | Auth Style | Details |
|----------|------------|---------|
| Analytics | Clean, minimal, light default | Simple centered card, trustworthy feel, light background with subtle grid |
| Productivity | Fast, dark mode default, keyboard hints | Dark theme, \"Press Enter to continue\" hints, minimal animation |
| Content | Creative, friendly, warm | Welcoming copy, possibly illustration, warm color accents |
| Utility Processor | Minimal, focused | Light/dark toggle optional, single CTA emphasis |
| Digital Download | Clean, trustworthy | Light theme, clear value props, social proof optional |

All auth pages share the same structure:
1. Google OAuth button (prominent, top)
2. "or" divider
3. Magic link email input (bottom)
4. Link to alternate action (Login ↔ Signup)

### Billing Model Differentiation

Each template should have billing that matches its use case:

| Template | Billing Model | Stripe Implementation |
|----------|---------------|----------------------|
| Analytics | Usage-based (events/month) | Metered pricing with usage records, overage charges |
| Productivity | Seat-based (per team member) | Per-seat subscription, quantity updates on member add/remove |
| Content | Feature limits (posts/month, channels) | Tiered plans with feature flags, usage tracking |

**products.json should reflect these models:**
- Analytics: Tiers based on event quotas (1K, 50K, unlimited)
- Productivity: Tiers based on team size + features (5 seats, 20 seats, unlimited)
- Content: Tiers based on post limits + channels (50 posts/mo, 500 posts/mo, unlimited)

## Tech Stack (All Templates)

- **Frontend:** Next.js 14+ (App Router)
- **Styling:** Tailwind CSS with brand token CSS variables
- **Database:** Supabase (PostgreSQL with RLS)
- **Auth:** Supabase Auth (Google OAuth + Magic Link)
- **Payments:** Stripe (Subscriptions + Customer Portal)
- **Icons:** Lucide React

## Process Workflow

### Phase 1: Research Analysis
Read `SaaS_Frontend_Template_Research.md` to understand:
- Component patterns for each template category (Parts I-III)
- Universal SaaS infrastructure (Part IV)
- Design system requirements (Part V)

### Phase 2: Create Directory Structure
Each template needs this structure:
```
templates/{name}/
├── manifest.json
├── README.md
├── .env.example            # Required environment variables
├── frontend/               # Next.js app
│   ├── app/               # App Router pages
│   ├── components/        # React components
│   ├── lib/               # Supabase/Stripe clients
│   └── styles/            # tokens.css for brand variables
├── supabase/
│   └── migrations/        # SQL schema with RLS
├── stripe/
│   └── products.json      # Billing products (template-specific)
└── content/
    └── slots.json         # Content injection points
```

**Required .env.example variables:**
```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
```

See `SKILL-full.md` for complete directory structure details.

### Phase 3: Implement Core Files

**For each template, create:**

1. **manifest.json** — Template metadata with name, version, features, brandTokens
2. **package.json** — Next.js dependencies (see SKILL-full.md for exact versions)
3. **Landing page** — Complete marketing page with hero, features, pricing, CTA (uses content slots)
4. **tokens.css** — CSS variables for brand customization
5. **Supabase migrations** — Auth schema, billing schema, app-specific schema
6. **Stripe products.json** — Pricing tiers
7. **slots.json** — Content injection points for copywriter skill
8. **Auth components** — Google OAuth button, Magic Link, callback handler
9. **Dashboard components** — Template-specific UI components
10. **Settings pages** — General, Team, Billing settings

### Phase 4: Implement Template-Specific Components

**Analytics Template:**
- BigNumberCard (metric + sparkline)
- DateRangeController (global state)
- BreakdownList (with progress bars)
- ActivityTicker (real-time feed)

**Productivity Template:**
- CommandPalette (Cmd+K)
- KanbanBoard (drag-drop)
- SidePeek (Linear-style drawer)
- RichTextEditor (slash commands)

**Content Template:**
- SplitComposer (editor + preview)
- ThreadEditor (block-based)
- CalendarGrid (scheduling)
- ChannelToggle (multi-platform)

### Phase 5: Validate Each Template

Run after completing each template:
```bash
.shared/scripts/templates/validate-template.sh templates/{template-name}
```

**Additionally, verify template integrity:**
```bash
# Check against the feature matrix in docs/template-integrity-checklist.md
# For digital-download, verify NO calendar/queue/media/connect pages exist:
ls -la templates/digital-download/frontend/app/\(dashboard\)/dashboard/
# Expected: only page.tsx

# Check for content-creator contamination:
find templates/digital-download -type f -name "*.tsx" | xargs grep -l "RichTextEditor\|MediaUploader\|ContentCalendar"
# Expected: no results
```

Fix any blockers before proceeding to the next template.

## Template Design Guidelines

### Template Integrity: Critical Principle

**BEFORE implementing any template, review the Template Integrity Checklist:**
```
docs/template-integrity-checklist.md
```

This checklist defines exactly what features, pages, and components belong to each template. It prevents "contamination" where features from one template are mistakenly included in another.

**Key rules:**
1. **Digital Download** = Simple, single-user download locker (NO calendar, queue, media, social features)
2. **Content Creator** = Full content management with publishing workflow (YES to all content features)
3. **Analytics Dashboard** = Data visualization only (NO content creation features)
4. **Productivity Tool** = Task/project management (NO publishing features)
5. **Utility Processor** = File processing workflows (NO collaboration features)

**When scaffolding:**
- Start with the minimal feature set defined in the checklist
- Add ONLY features listed for that specific template
- Resist the urge to copy features between templates
- Validate against the checklist after completion

**Example of contamination:**
- ❌ Adding a publishing calendar to digital-download template
- ❌ Adding workspace/team features to single-user templates
- ❌ Adding content creation features to analytics templates

### Visual Standards
- Clean, grid-based layouts (no experimental asymmetry)
- Professional color palettes with semantic colors (success/warning/error)
- Typography: Inter or system fonts as defaults (replaceable via tokens)
- Spacing: 8px scale (4, 8, 16, 24, 32, 48, 64)
- Dark mode: #121212 background (not pure black)

### Polish Elements
- Micro-interactions: 200ms transitions, subtle hover states
- Loading states: Skeleton screens for data tables
- Empty states: Helpful illustrations + CTAs
- Error states: Clear messaging + recovery actions
- Toast notifications: Non-intrusive, auto-dismiss

### Production Requirements
- TypeScript strict mode
- WCAG AA accessibility (4.5:1 contrast)
- Mobile-first responsive design

## Key Reference Files

| File | Purpose |
|------|---------|
| `SaaS_Frontend_Template_Research.md` | UI patterns, component specs |
| `.shared/scripts/benchmarking/scrape_results/` | Visual reference captures |
| `SKILL-full.md` (this directory) | Detailed code examples |
| `docs/template-scaffolding-guide.md` | Execution overview |

## Required Brand Tokens

Every template's `tokens.css` must define:
```css
:root {
  /* Colors */
  --color-primary: ...;
  --color-secondary: ...;
  --color-accent: ...;
  --color-background: ...;
  --color-foreground: ...;
  
  /* Semantic */
  --color-success: #28A745;
  --color-warning: #FFC107;
  --color-error: #DC3545;
  --color-info: #17A2B8;
  
  /* Typography */
  --font-display: 'Inter', sans-serif;
  --font-body: 'Inter', sans-serif;
  
  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
}
```

## Required Content Slots

Every template's `slots.json` must include:
- `landing.*` — Hero, features, CTA
- `dashboard.*` — Empty states
- `errors.*` — Error messages
- `auth.*` — Login/signup copy

## Required Supabase Tables

Every template must have migrations for:
- `profiles` — User profiles (extends auth.users)
- `teams` — Multi-tenant support
- `team_members` — Team membership
- `customers` — Stripe customer mapping
- `subscriptions` — Subscription tracking
- Template-specific tables

**RLS Required:** Every user-data table must have Row Level Security enabled with proper policies.

## Auth Implementation

**Google OAuth Button:**
```typescript
await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: {
    redirectTo: `${window.location.origin}/auth/callback`
  }
})
```

**OAuth Callback Handler:** Exchange code for session in `app/(auth)/callback/route.ts`.

See `SKILL-full.md` for complete implementation.

## Stripe Implementation

**Products structure:**
```json
{
  "products": [
    { "id": "starter", "name": "Starter", "prices": {...} },
    { "id": "pro", "name": "Pro", "prices": {...}, "highlighted": true },
    { "id": "enterprise", "name": "Enterprise", "custom": true }
  ]
}
```

**Webhook handler:** Process subscription events in `app/api/stripe/webhook/route.ts`.

**Required webhook events to handle:**
- `checkout.session.completed` — User completed checkout
- `customer.subscription.created` — New subscription started
- `customer.subscription.updated` — Plan changed, renewed, or payment method updated
- `customer.subscription.deleted` — Subscription cancelled
- `invoice.payment_succeeded` — Payment successful (update subscription status)
- `invoice.payment_failed` — Payment failed (trigger dunning flow)
- `customer.created` — New Stripe customer (link to Supabase profile)

See `SKILL-full.md` for complete implementation.

## Output

After execution, you should have:
```
templates/
├── analytics-dashboard/
├── productivity-tool/
└── content-creator/
```

Each passing validation with no blockers.

## Common Mistakes

| Mistake | Prevention |
|---------|------------|
| **Template contamination** | Review docs/template-integrity-checklist.md before starting |
| Hard-coded colors | Use CSS variables from tokens.css |
| Missing RLS policies | Add policies for every user-data table |
| No error boundaries | Add React error boundaries to layouts |
| Hardcoded secrets | Use environment variables (see .env.example) |
| Missing loading states | Add Suspense boundaries and skeletons |
| Generic auth pages | Match auth UI to template personality |
| Same billing for all | Differentiate billing model per template type |
| Missing category pages | Include snippet page (Analytics), connect page (Content) |
| Copy-pasting between templates | Build each template independently based on its feature matrix |

## Next Steps After Scaffolding

1. Run `template-validator` skill on all 3 templates
2. Fix any blockers or warnings
3. Create Phase B skills: `template-selector`, `template-personalizer`, `copywriter`
4. Update Co-CEO process documentation
