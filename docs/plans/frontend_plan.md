# TrendScope Frontend Implementation Plan

**Project:** Trendscope - The Bloomberg Terminal for Short-Form Video Trends  
**Platform:** Next.js 15 App Router + shadcn + Tailwind v4  
**Status:** Phase 1 Complete - Foundation Established  
**Last Updated:** 2026-02-16

---

## Executive Summary

This document outlines the complete frontend implementation strategy for TrendScope, a real-time TikTok trend intelligence platform. The application serves three primary user personas (Solo Creators, Agencies, Brands) with a professional B2B SaaS dashboard, real-time alerts, velocity analytics, and comprehensive SEO content marketing.

**Current Status:** ✅ Foundation complete with Next.js 15, Tailwind v4, Supabase, and core architecture in place.

---

## Tech Stack Rationale

| Technology | Choice | Justification |
|------------|--------|---------------|
| **Framework** | Next.js 15 (App Router) | SSR/SSG for SEO content strategy, Server Components for performance, built-in API routes |
| **UI Library** | shadcn | Customizable, accessible components matching "Sharp, Professional" brand personality |
| **Styling** | Tailwind v4 + Vanilla CSS | Rapid development, design token system, theme customization |
| **State** | Zustand | Lightweight global state for user preferences, niche selections, alert configs |
| **Data Fetching** | TanStack Query | Real-time trend data caching, optimistic updates, automatic refetching |
| **Charts** | Recharts (via shadcn) | Velocity graphs, saturation curves, 24-hour trend analytics |
| **Auth** | Supabase Auth | Pre-decided in PRD, RLS policies, tier-based access |
| **Icons** | Lucide | Clean, professional icons matching shadcn ecosystem |
| **Deployment** | Vercel | Zero-config Next.js deployment, edge functions, analytics |

---

## Phase 1: Foundation (✅ Complete)

### Completed Items

- [x] Next.js 15 project initialized with App Router
- [x] TypeScript configuration with strict mode
- [x] Tailwind v4 setup with PostCSS
- [x] Design tokens from brand kit configured in globals.css
- [x] Custom typography utilities (heading-1 through heading-4, body variants)
- [x] Supabase client configuration (server & browser)
- [x] Authentication middleware for route protection
- [x] Zustand stores (auth, user preferences, sidebar)
- [x] TanStack Query hooks (trends, trend detail, alerts)
- [x] Basic landing page with hero section
- [x] Project structure and folder organization
- [x] Environment variable configuration
- [x] TypeScript type definitions for database schema
- [x] Utility functions (cn for className merging)
- [x] Build verification (successful production build)

### Deliverables

```
frontend/
├── app/
│   ├── globals.css (Tailwind v4 + design tokens)
│   ├── layout.tsx (root layout with metadata)
│   └── page.tsx (landing page)
├── components/
│   ├── common/
│   │   ├── Logo.tsx
│   │   └── EmptyState.tsx
│   └── providers/
│       └── QueryProvider.tsx
├── hooks/
│   ├── useTrends.ts
│   ├── useTrendDetail.ts
│   └── useAlerts.ts
├── lib/
│   ├── utils.ts
│   └── supabase/
│       ├── client.ts
│       └── server.ts
├── stores/
│   ├── authStore.ts
│   ├── userPreferencesStore.ts
│   └── sidebarStore.ts
├── types/
│   └── database.types.ts
├── middleware.ts
├── next.config.ts
├── tailwind.config.ts
├── postcss.config.mjs
├── tsconfig.json
└── package.json
```

---

## Phase 2: Core UI Components (Next)

### 2.1 shadcn Installation & Configuration

**Install core components:**
```bash
npx shadcn@latest init
npx shadcn@latest add button card badge input label separator
npx shadcn@latest add dialog sheet dropdown-menu
npx shadcn@latest add table sidebar avatar
npx shadcn@latest add form select checkbox switch
npx shadcn@latest add alert toast skeleton
```

**Custom variants needed:**
- Button variant: `ghost-primary` (sidebar menu items)
- Card variant: `trend-card` (trend list items)
- Badge variant: `velocity` (color-coded 0-100 scores)
- Alert variant: `trend-alert` (Slack-style cards)

### 2.2 Layout Components

**Dashboard Layout** (`app/(dashboard)/layout.tsx`):
- Sidebar navigation with collapse functionality
- Header with user profile dropdown
- Mobile-responsive with bottom sheet drawer

**Public Layout** (`app/(public)/layout.tsx`):
- Marketing header with navigation
- Footer with links and legal pages

**Auth Layout** (`app/(auth)/layout.tsx`):
- Centered card layout
- Logo and branding

---

## Phase 3: Authentication Flow

### 3.1 Auth Pages

**Routes:**
- `/auth/login` - Login form with email/password
- `/auth/signup` - Registration with niche selection
- `/auth/verify-email` - Email verification landing page
- `/auth/callback` - Supabase OAuth callback handler

**Flow:**
1. User submits signup form
2. Supabase creates account
3. Email verification sent
4. User verifies → redirect to onboarding
5. User selects niches (min 1 for Free tier)
6. User connects Slack/email alerts
7. Dashboard shows "Monitoring Active"

### 3.2 Protected Routes

**Middleware enforcement:**
- `/app/*` requires authentication
- Redirect unauthenticated users to `/auth/login?redirectTo=/app`
- Redirect authenticated users from auth pages to `/app`

---

## Phase 4: Dashboard Implementation

### 4.1 Dashboard Overview (`/app`)

**Components:**
- `StatsOverview` - 3 stat cards (active trends, detected today, alerts this week)
- `HotTrends` - Top 5 trends by velocity
- `RecentAlerts` - Last 5 alerts with timestamps
- `QuickActions` - CTAs for common tasks

**Data:**
- Fetch from `/api/dashboard` endpoint
- Update every 60 seconds with TanStack Query
- Show loading skeletons during fetch

### 4.2 Trends Pages

**Trends List** (`/app/trends`):
- Filter by niche, status, velocity threshold
- Sort by velocity score, detection time
- Card grid layout (responsive)
- Pagination or infinite scroll

**Trend Detail** (`/app/trends/[id]`):
- Velocity graph (Recharts line chart)
- Saturation meter (progress bar with color coding)
- Example videos (3 thumbnails → TikTok links)
- Related hashtags/sounds
- Actions: Bookmark, Dismiss, Share

**Components:**
- `TrendCard` - List item with velocity bar
- `TrendDetail` - Full page view
- `VelocityGraph` - 24-hour chart
- `SaturationMeter` - Color-coded progress (green <30%, yellow 30-70%, red >70%)
- `ExampleVideos` - Video thumbnail grid
- `TrendFilters` - Filter panel

### 4.3 Alerts Pages

**Alerts List** (`/app/alerts`):
- Alert history with filtering
- Status indicators (sent, failed, dismissed)
- Click through to trend detail

**Alert Stats** (`/app/alerts/stats`):
- Weekly/monthly alert counts
- Alert distribution by niche (bar chart)
- Engagement metrics (click-through rate)

### 4.4 Settings Pages

**Profile** (`/app/settings/profile`):
- User info editor
- Avatar upload
- Email preferences

**Niches** (`/app/settings/niches`):
- Multi-select with search
- Tier limits enforced (Free: 1, Solo: unlimited)
- Velocity threshold per niche

**Integrations** (`/app/settings/integrations`):
- Slack webhook configuration
- Test connection button
- Webhook URL validation

**Billing** (`/app/settings/billing`):
- Current tier display
- Upgrade CTA
- Stripe billing portal link
- Invoice history

---

## Phase 5: Agency Features (Tier-Gated)

### 5.1 Client Management (`/app/clients`)

**Client List:**
- Grid of client cards
- Add new client modal
- Edit/delete actions

**Client Detail** (`/app/clients/[id]`):
- Client-specific niche configuration
- Alert destination setup
- Trend history for this client
- Generate white-label report

**Report Generator:**
- PDF export with agency branding
- Trend summary with velocity graphs
- Example videos embedded
- Download or share link

### 5.2 Components

- `ClientList` - Grid layout
- `ClientForm` - Add/edit modal
- `ClientWorkspace` - Isolated view
- `ReportGenerator` - PDF builder

---

## Phase 6: Marketing & SEO Content

### 6.1 Landing Page Enhancement

**Sections:**
- Hero (headline, subheadline, CTA)
- Social proof (user testimonials, stats)
- Features (3-column grid with icons)
- How it works (step-by-step visual)
- Pricing (tier comparison table)
- FAQ (accordion)
- Final CTA

**Components:**
- `Hero` - Above-the-fold section
- `Features` - Icon + text grid
- `PricingTable` - Tier comparison with feature checkmarks
- `Testimonials` - Quote carousel
- `FAQ` - Accordion from shadcn
- `CTASection` - Final conversion push

### 6.2 Pricing Page (`/pricing`)

**Tier comparison table:**
- Free, Solo, Agency, Enterprise columns
- Feature checkmarks per tier
- Monthly pricing
- "Get Started" CTAs
- Stripe Checkout integration

### 6.3 SEO Content Architecture

**Pillar Pages (4 total):**
1. `/tiktok-trend-detection-guide` (5000+ words)
2. `/creator-productivity-system` (4500+ words)
3. `/tiktok-analytics-guide` (6000+ words)
4. `/agency-tiktok-strategy` (5500+ words)

**Cluster Articles (32 total):**
- `/blog/[slug]` dynamic route
- MDX files in `content/blog/`
- Auto-generated table of contents
- Internal linking to pillars

**Implementation:**
- Use `next-mdx-remote` or `contentlayer`
- Generate static pages with `generateStaticParams`
- SEO metadata per page
- Structured data (JSON-LD)

---

## Phase 7: Charts & Data Visualization

### 7.1 Recharts Integration

**Velocity Graph:**
```typescript
<ChartContainer>
  <LineChart data={velocityData}>
    <XAxis dataKey="timestamp" />
    <YAxis />
    <Line dataKey="velocity" stroke="var(--color-primary)" />
    <ChartTooltip content={<ChartTooltipContent />} />
  </LineChart>
</ChartContainer>
```

**Charts needed:**
- Velocity line chart (trend detail)
- Saturation progress bar (trend cards)
- Alert stats bar chart (alert analytics)
- Niche distribution pie chart (settings)

### 7.2 Real-Time Updates

**WebSocket or polling:**
- TanStack Query refetchInterval: 60s for Solo tier
- 30s for Agency tier
- Real-time indicator (pulsing dot)

---

## Phase 8: Responsive Design

### 8.1 Breakpoints

| Device | Width | Adjustments |
|--------|-------|-------------|
| Mobile | <768px | Single column, bottom nav, stacked cards |
| Tablet | 768-1279px | 2 columns, collapsible sidebar |
| Desktop | >1280px | Full sidebar, multi-column dashboard |

### 8.2 Mobile Optimization

- Sidebar → Bottom sheet drawer
- Trend cards → Vertical stack
- Velocity graphs → Simplified labels
- Tables → Horizontal scroll with sticky column

---

## Phase 9: Performance & Optimization

### 9.1 Code Splitting

```typescript
const ClientList = dynamic(() => import('@/components/agency/ClientList'))
const VelocityGraph = dynamic(() => import('@/components/trends/VelocityGraph'))
```

### 9.2 Image Optimization

- Use Next.js `<Image>` component
- Remote patterns configured for picsum.photos, pravatar.cc
- Lazy loading for below-the-fold images

### 9.3 Caching Strategy

- Static pages: ISR with 60s revalidation
- Dashboard: Client-side with 60s stale time
- Trends: Poll every 60s (Solo), 30s (Agency)

---

## Phase 10: Testing & Quality Assurance

### 10.1 Unit Tests (Vitest)

- Component rendering tests
- Hook behavior tests
- Utility function tests

### 10.2 E2E Tests (Playwright)

- Auth flow (signup → verify → onboarding)
- Dashboard navigation
- Trend detail view
- Settings updates
- Billing upgrade

### 10.3 Accessibility

- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader support
- Color contrast checks
- ARIA labels

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Build time | <30s | ✅ 7.6s |
| First Load JS | <120kB | ✅ 102kB |
| Lighthouse Performance | >90 | Pending |
| Lighthouse Accessibility | 100 | Pending |
| Type safety | No errors | ✅ Pass |

---

## Next Steps (Priority Order)

1. **Install shadcn components** (1-2 hours)
2. **Build dashboard layout** (2-3 hours)
3. **Implement trends pages** (4-5 hours)
4. **Create auth flows** (3-4 hours)
5. **Add settings pages** (2-3 hours)
6. **Build landing page** (3-4 hours)
7. **Agency features** (4-5 hours)
8. **SEO content** (8-10 hours)
9. **Testing & QA** (4-6 hours)
10. **Deployment** (1-2 hours)

**Estimated total:** 32-45 hours

---

## Deployment Checklist

- [ ] Environment variables configured in Vercel
- [ ] Supabase RLS policies tested
- [ ] Stripe webhook endpoint verified
- [ ] Domain DNS configured (trendscope.io)
- [ ] Analytics installed (Vercel Analytics, PostHog)
- [ ] Error tracking configured (Sentry)
- [ ] Performance monitoring enabled
- [ ] SSL certificate active
- [ ] SEO meta tags verified
- [ ] Sitemap.xml generated

---

*Last Updated: 2026-02-16*  
*Status: Phase 1 Complete - Ready for Phase 2*  
*Next Review: After shadcn installation*
