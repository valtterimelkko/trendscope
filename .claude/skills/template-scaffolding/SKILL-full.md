---
name: template-scaffolding
description: Generates complete MVP template directories (Analytics, Productivity, Content, Utility Processor, Digital Download) with Next.js frontend, Supabase backend, Google OAuth authentication, and Stripe billing. Use this skill to create the 5 core templates from research and benchmark materials.
---

# Template Scaffolding

## Overview

Generate production-ready MVP template directories from research documentation and benchmark captures. Each template includes a complete stack: Next.js 14+ frontend, Supabase database with RLS policies, authentication (including Google OAuth), and Stripe billing integration.

**Core principle:** Templates should be 80% complete MVPs that users customize via brand tokens and content slots. They follow established SaaS conventions—professional and familiar, not experimental.

## When to Use

- Creating the 5 core templates for the meta-project (one-time internal use)
- Building a new template category
- Regenerating templates after significant research updates

## Pre-Requisites

**CRITICAL: Before starting, verify these materials exist:**

```bash
# Check research documentation exists
ls -la SaaS_Frontend_Template_Research.md

# Check benchmark captures exist
ls -la .shared/scripts/benchmarking/scrape_results/
```

**Required inputs:**
- [ ] `SaaS_Frontend_Template_Research.md` — UI patterns, components, design systems (417 lines)
- [ ] `.shared/scripts/benchmarking/scrape_results/` — HTML captures and screenshots
- [ ] `frontend_template_idea.md` — Template structure specification

## The 5 Templates to Create

### 1. Analytics Dashboard Template
**Personality:** Clean, data-focused, trustworthy (Plausible/Baremetrics vibes)
**Key Features:**
- Big Number Cards with sparklines
- Date Range Controller (global state)
- Breakdown Lists with progress bars
- Real-time activity ticker
- Public dashboard toggle

**Reference Materials:**
- Research: Part I (Analytics & Dashboard)
- Captures: `plausible`, `posthog_demo`, `baremetrics`, `simpleanalytics`

### 2. Productivity Tool Template
**Personality:** Fast, efficient, keyboard-first (Linear/Notion vibes)
**Key Features:**
- Command Palette (Cmd+K)
- Kanban Board with drag-and-drop
- Side Peek viewer (Linear-style drawer)
- Rich text editor with slash commands
- View switcher (List/Board/Calendar)

**Reference Materials:**
- Research: Part II (Productivity & Tool)
- Captures: `notion`, `craft`, `coda`, `linear`

### 3. Content Creator Template
**Personality:** Creative, editorial, flow-focused (Typefully/Ghost vibes)
**Key Features:**
- Split-screen composer (editor + preview)
- Thread/block editor for social posts
- Calendar grid with drag-and-drop scheduling
- Channel toggles for multi-platform
- Posting streak visualization

**Reference Materials:**
- Research: Part III (Content & Creator)
- Captures: `typefully`, `kit`, `feedhive`, `hypefury`

### 4. Utility Processor Template
**Personality:** Minimal, focused, light/dark optional (CloudConvert/ProductMotion vibes)
**Key Features:**
- Upload → Process → Download primary flow
- Drag-and-drop upload with validation
- Progress + status tracker for jobs
- Recent history list with download links
- Usage/quota meter and CTA-first layout

**Reference Materials:**
- Research: `.shared/scripts/benchmarking/4th_template/` (ProductMotion, CloudConvert)

### 5. Digital Download Portal Template
**Personality:** Clean, trustworthy, commerce-friendly
**Key Features:**
- Landing + pricing + FAQ + social proof
- Secure gated download locker with license key display
- Order history/receipts and billing portal links
- Download limits per tier with Stripe
- Storage-backed delivery via signed URLs

**Reference Materials:**
- Research: `.shared/scripts/benchmarking/4th_template/` (minimal download/store flows)

---

## Template Directory Structure

Each template must follow this exact structure:

```
templates/
├── analytics-dashboard/
│   ├── manifest.json              # Template metadata
│   ├── README.md                  # Setup & customization guide
│   │
│   ├── frontend/                  # Next.js 14+ App Router
│   │   ├── package.json
│   │   ├── next.config.js
│   │   ├── tsconfig.json
│   │   ├── tailwind.config.js
│   │   │
│   │   ├── app/
│   │   │   ├── layout.tsx         # Root layout with providers
│   │   │   ├── page.tsx           # Landing page
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   ├── signup/page.tsx
│   │   │   │   └── callback/route.ts   # OAuth callback handler
│   │   │   ├── (dashboard)/
│   │   │   │   ├── layout.tsx     # Dashboard layout with sidebar
│   │   │   │   ├── page.tsx       # Main dashboard view
│   │   │   │   └── settings/
│   │   │   │       ├── page.tsx   # General settings
│   │   │   │       ├── team/page.tsx
│   │   │   │       └── billing/page.tsx
│   │   │   └── api/
│   │   │       ├── stripe/
│   │   │       │   └── webhook/route.ts
│   │   │       └── [...catchall]/route.ts
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                # Base components (buttons, inputs, etc.)
│   │   │   ├── layout/            # Header, Sidebar, Footer
│   │   │   ├── auth/              # Login forms, OAuth buttons
│   │   │   ├── dashboard/         # Template-specific components
│   │   │   └── billing/           # Pricing cards, subscription status
│   │   │
│   │   ├── lib/
│   │   │   ├── supabase/
│   │   │   │   ├── client.ts      # Browser client
│   │   │   │   ├── server.ts      # Server client
│   │   │   │   └── middleware.ts  # Auth middleware
│   │   │   ├── stripe/
│   │   │   │   ├── client.ts      # Stripe.js loader
│   │   │   │   └── actions.ts     # Server actions for billing
│   │   │   └── utils.ts           # Helper functions
│   │   │
│   │   └── styles/
│   │       ├── globals.css        # Tailwind imports + custom styles
│   │       └── tokens.css         # Brand token CSS variables
│   │
│   ├── supabase/
│   │   ├── config.toml            # Supabase project config
│   │   ├── migrations/
│   │   │   ├── 00001_auth_schema.sql      # User profiles, teams
│   │   │   ├── 00002_billing_schema.sql   # Subscriptions, usage
│   │   │   └── 00003_app_schema.sql       # Template-specific tables
│   │   └── seed.sql               # Demo data for development
│   │
│   ├── stripe/
│   │   ├── products.json          # Product & price definitions
│   │   ├── portal-config.json     # Customer portal settings
│   │   └── fixtures/              # Stripe CLI fixtures for testing
│   │       └── setup.json
│   │
│   └── content/
│       └── slots.json             # Content injection point definitions
```

---

## Process Workflow

### Phase 1: Research Analysis (Read-Only)

Study the reference materials to extract patterns:

```bash
# Read research documentation
cat SaaS_Frontend_Template_Research.md

# List available benchmark captures
ls -la .shared/scripts/benchmarking/scrape_results/

# Read specific HTML captures for component extraction
cat .shared/scripts/benchmarking/scrape_results/notion/notion_*.html
```

**Extract from research:**
- Component specifications (Part I-III)
- Design system requirements (Part V)
- Universal infrastructure patterns (Part IV)

### Phase 2: Create Template Manifests

Each template needs a `manifest.json`:

```json
{
  "name": "analytics-dashboard",
  "displayName": "Analytics Dashboard",
  "description": "Clean, data-focused SaaS template with metrics visualization",
  "version": "1.0.0",
  "category": "analytics",
  "personality": "trustworthy",
  "techStack": {
    "frontend": "next@14",
    "database": "supabase",
    "auth": "supabase-auth",
    "payments": "stripe"
  },
  "features": [
    "big-number-cards",
    "date-range-controller",
    "breakdown-lists",
    "real-time-ticker",
    "public-dashboard"
  ],
  "brandTokens": [
    "--color-primary",
    "--color-secondary",
    "--color-accent",
    "--font-display",
    "--font-body"
  ],
  "contentSlots": 42,
  "estimatedSetupTime": "15 minutes"
}
```

### Phase 3: Scaffold Frontend Structure

Create Next.js 14+ App Router structure with:

**Core Dependencies:**
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@supabase/supabase-js": "^2.39.0",
    "@supabase/ssr": "^0.1.0",
    "@stripe/stripe-js": "^2.2.0",
    "stripe": "^14.0.0",
    "tailwindcss": "^3.4.0",
    "clsx": "^2.0.0",
    "lucide-react": "^0.300.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/react": "^18.2.0",
    "@types/node": "^20.0.0"
  }
}
```

**Tailwind Config with Brand Tokens:**
```javascript
// tailwind.config.js
module.exports = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        secondary: 'var(--color-secondary)',
        accent: 'var(--color-accent)',
      },
      fontFamily: {
        display: 'var(--font-display)',
        body: 'var(--font-body)',
      },
    },
  },
};
```

### Phase 4: Implement Authentication

Use Supabase Auth with Google OAuth:

**OAuth Callback Handler (`app/(auth)/callback/route.ts`):**
```typescript
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')

  if (code) {
    const supabase = createClient()
    await supabase.auth.exchangeCodeForSession(code)
  }

  return NextResponse.redirect(new URL('/dashboard', requestUrl.origin))
}
```

**Google OAuth Button Component:**
```typescript
'use client'
import { createClient } from '@/lib/supabase/client'

export function GoogleSignIn() {
  const supabase = createClient()

  const handleSignIn = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
  }

  return (
    <button onClick={handleSignIn} className="flex items-center gap-2 ...">
      <GoogleIcon />
      <span>Continue with Google</span>
    </button>
  )
}
```

### Phase 5: Create Supabase Schemas

**Auth Schema (`00001_auth_schema.sql`):**
```sql
-- User profiles (extends Supabase auth.users)
CREATE TABLE public.profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email TEXT NOT NULL,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Teams for multi-tenant
CREATE TABLE public.teams (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Team memberships
CREATE TABLE public.team_members (
  team_id UUID REFERENCES public.teams(id) ON DELETE CASCADE,
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
  joined_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (team_id, user_id)
);

-- RLS Policies
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);
```

**Billing Schema (`00002_billing_schema.sql`):**
```sql
-- Stripe customer mapping
CREATE TABLE public.customers (
  id UUID REFERENCES public.profiles(id) ON DELETE CASCADE PRIMARY KEY,
  stripe_customer_id TEXT UNIQUE
);

-- Subscriptions
CREATE TABLE public.subscriptions (
  id TEXT PRIMARY KEY, -- Stripe subscription ID
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  status TEXT NOT NULL,
  price_id TEXT,
  quantity INTEGER DEFAULT 1,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Usage tracking (for metered billing)
CREATE TABLE public.usage (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  metric TEXT NOT NULL,
  quantity INTEGER DEFAULT 1,
  recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS
ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage ENABLE ROW LEVEL SECURITY;
```

### Phase 6: Configure Stripe Integration

**Products Definition (`stripe/products.json`):**
```json
{
  "products": [
    {
      "id": "starter",
      "name": "Starter",
      "description": "For individuals getting started",
      "features": ["Up to 1,000 events/month", "7-day data retention", "Email support"],
      "prices": {
        "monthly": { "amount": 900, "currency": "usd" },
        "yearly": { "amount": 7900, "currency": "usd" }
      }
    },
    {
      "id": "pro",
      "name": "Pro",
      "description": "For growing teams",
      "features": ["Up to 50,000 events/month", "1-year data retention", "Priority support", "Team members"],
      "prices": {
        "monthly": { "amount": 2900, "currency": "usd" },
        "yearly": { "amount": 24900, "currency": "usd" }
      },
      "highlighted": true
    },
    {
      "id": "enterprise",
      "name": "Enterprise",
      "description": "For large organizations",
      "features": ["Unlimited events", "Unlimited retention", "Dedicated support", "Custom integrations"],
      "prices": {
        "custom": true
      }
    }
  ]
}
```

**Webhook Handler (`app/api/stripe/webhook/route.ts`):**
```typescript
import { headers } from 'next/headers'
import { NextResponse } from 'next/server'
import Stripe from 'stripe'
import { createClient } from '@/lib/supabase/server'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

export async function POST(request: Request) {
  const body = await request.text()
  const signature = headers().get('stripe-signature')!

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    )
  } catch (err) {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
  }

  const supabase = createClient()

  switch (event.type) {
    case 'customer.subscription.created':
    case 'customer.subscription.updated':
      const subscription = event.data.object as Stripe.Subscription
      await supabase.from('subscriptions').upsert({
        id: subscription.id,
        user_id: subscription.metadata.user_id,
        status: subscription.status,
        price_id: subscription.items.data[0].price.id,
        current_period_start: new Date(subscription.current_period_start * 1000),
        current_period_end: new Date(subscription.current_period_end * 1000),
      })
      break

    case 'customer.subscription.deleted':
      const deletedSub = event.data.object as Stripe.Subscription
      await supabase.from('subscriptions').delete().eq('id', deletedSub.id)
      break
  }

  return NextResponse.json({ received: true })
}
```

### Phase 7: Define Content Slots

Create `content/slots.json` with injection points:

```json
{
  "version": "1.0",
  "slots": {
    "landing": {
      "hero.headline": {
        "type": "headline",
        "maxLength": 80,
        "placeholder": "Your powerful headline here"
      },
      "hero.subheadline": {
        "type": "body",
        "maxLength": 200,
        "placeholder": "A compelling description of your product's value"
      },
      "cta.primary": {
        "type": "button",
        "maxLength": 30,
        "placeholder": "Get Started Free"
      },
      "features.title": {
        "type": "section_title",
        "maxLength": 60
      },
      "features.items": {
        "type": "array",
        "itemType": {
          "title": { "type": "feature_title", "maxLength": 40 },
          "description": { "type": "body", "maxLength": 120 }
        },
        "minItems": 3,
        "maxItems": 6
      }
    },
    "dashboard": {
      "empty.title": {
        "type": "empty_state",
        "context": "first_time_user",
        "maxLength": 60
      },
      "empty.description": {
        "type": "body",
        "maxLength": 120
      },
      "empty.cta": {
        "type": "button",
        "maxLength": 30
      }
    },
    "errors": {
      "generic.title": {
        "type": "error",
        "tone": "helpful",
        "maxLength": 60
      },
      "generic.message": {
        "type": "error",
        "tone": "helpful",
        "maxLength": 200
      },
      "network.message": {
        "type": "error",
        "tone": "reassuring",
        "maxLength": 200
      }
    },
    "auth": {
      "login.title": { "type": "headline", "maxLength": 40 },
      "login.subtitle": { "type": "body", "maxLength": 100 },
      "signup.title": { "type": "headline", "maxLength": 40 },
      "signup.subtitle": { "type": "body", "maxLength": 100 }
    }
  }
}
```

### Phase 8: Create Template README

Each template needs a comprehensive README:

```markdown
# Analytics Dashboard Template

Production-ready SaaS template for analytics and data visualization products.

## Quick Start

### 1. Clone and Install
\`\`\`bash
cp -r templates/analytics-dashboard my-project
cd my-project/frontend
npm install
\`\`\`

### 2. Configure Environment
\`\`\`bash
cp .env.example .env.local
# Add your keys:
# NEXT_PUBLIC_SUPABASE_URL=
# NEXT_PUBLIC_SUPABASE_ANON_KEY=
# SUPABASE_SERVICE_ROLE_KEY=
# STRIPE_SECRET_KEY=
# STRIPE_WEBHOOK_SECRET=
# NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
\`\`\`

### 3. Set Up Supabase
\`\`\`bash
supabase init
supabase db push
\`\`\`

### 4. Configure Google OAuth
1. Go to Supabase Dashboard → Authentication → Providers
2. Enable Google provider
3. Add your Google OAuth credentials

### 5. Start Development
\`\`\`bash
npm run dev
\`\`\`

## Customization

### Brand Tokens
Edit `styles/tokens.css`:
\`\`\`css
:root {
  --color-primary: #3B82F6;    /* Your primary brand color */
  --color-secondary: #10B981;  /* Secondary accent */
  --font-display: 'Inter';     /* Heading font */
  --font-body: 'Inter';        /* Body font */
}
\`\`\`

### Content Slots
Run the copywriter skill or manually edit content in components.
See `content/slots.json` for all available slots.

## Included Features
- [ ] Landing page with pricing
- [ ] Google OAuth + Magic Link auth
- [ ] Dashboard with sample widgets
- [ ] Settings (General, Team, Billing)
- [ ] Stripe subscription management
- [ ] Dark mode support
- [ ] Mobile responsive

## Tech Stack
- **Frontend:** Next.js 14, React 18, Tailwind CSS
- **Database:** Supabase (PostgreSQL)
- **Auth:** Supabase Auth (Google OAuth)
- **Payments:** Stripe (Subscriptions)
```

---

## Template Design Guidelines

Follow these principles from the research documentation:

### Visual Standards
- Clean, grid-based layouts (no experimental asymmetry)
- Professional color palettes with semantic colors
- Typography: Use Inter or system fonts as DEFAULTS (replaceable via tokens)
- Spacing: 8px scale (4, 8, 16, 24, 32, 48, 64)
- Dark mode: Proper contrast (#121212 background, not pure black)

### Polish Elements
- Micro-interactions: Subtle hover states, 200ms transitions
- Loading states: Skeleton screens for data tables
- Empty states: Helpful illustrations + CTAs
- Error states: Clear messaging + recovery actions
- Toast notifications: Non-intrusive, auto-dismiss

### Production Requirements
- TypeScript strict mode
- Accessibility: WCAG AA minimum (4.5:1 contrast)
- Responsive: Mobile-first breakpoints
- Performance: < 3s initial load

---

## Output Verification

After scaffolding, run the template validator:

```bash
.shared/scripts/templates/validate-template.sh templates/analytics-dashboard
.shared/scripts/templates/validate-template.sh templates/productivity-tool
.shared/scripts/templates/validate-template.sh templates/content-creator
```

**Expected output:** All templates pass validation with no blockers.

---

## Helper Scripts

Location: `.shared/scripts/templates/`

| Script | Purpose |
|--------|---------|
| `validate-template.sh` | Master validation (runs after scaffolding) |
| `check-structure.py` | Validates directory structure |
| `check-content-slots.py` | Validates slots.json format |
| `check-brand-tokens.py` | Ensures CSS variables are replaceable |

---

## Common Mistakes

| Mistake | Prevention |
|---------|------------|
| Hard-coded colors | Always use CSS variables from tokens.css |
| Missing RLS policies | Every table needs row-level security |
| No error boundaries | Add React error boundaries to layouts |
| Forgetting webhook verification | Always verify Stripe signatures |
| Missing loading states | Add Suspense boundaries and skeletons |

---

## Integration Points

**This skill produces:**
- 5 complete template directories in `templates/`
- Ready for `template-validator` skill to check
- Ready for Phase B skills to customize (`template-personalizer`, `copywriter`)

**Dependencies:**
- `SaaS_Frontend_Template_Research.md` (patterns reference)
- `.shared/scripts/benchmarking/scrape_results/` (visual reference)
- `.shared/scripts/benchmarking/4th_template/` (minimal SaaS benchmarking for utility + download)
