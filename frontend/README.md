# Trendscope Frontend

The Bloomberg Terminal for Short-Form Video Trends - a real-time TikTok trend intelligence frontend prototype.

> This frontend belongs to a broader unfinished product experiment. Start with the root [`../README.md`](../README.md) for project status, adoption caveats, and story.

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **UI Library**: shadcn/ui
- **Styling**: Tailwind CSS v4
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Charts**: Recharts
- **Auth**: Supabase Auth
- **Icons**: Lucide React
- **Deployment**: Vercel

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
cp .env.example .env.local
```

3. Update `.env.local` with your Supabase credentials

4. Run the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000)

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── (public)/          # Public marketing pages
│   ├── (auth)/            # Authentication pages
│   ├── (dashboard)/       # Protected dashboard pages
│   └── api/               # API routes
├── components/
│   ├── ui/                # shadcn components
│   ├── dashboard/         # Dashboard-specific components
│   ├── trends/            # Trend-related components
│   ├── common/            # Shared components
│   └── marketing/         # Marketing page components
├── hooks/                 # Custom React hooks
├── lib/                   # Utility functions
│   └── supabase/          # Supabase client config
├── stores/                # Zustand state stores
├── types/                 # TypeScript type definitions
└── public/                # Static assets
```

## Features

### Implemented
- ✅ Next.js 15 setup with App Router
- ✅ Tailwind v4 with design tokens
- ✅ Supabase Auth integration
- ✅ TypeScript configuration
- ✅ Zustand stores (auth, preferences, sidebar)
- ✅ TanStack Query hooks
- ✅ Basic landing page
- ✅ Middleware for route protection

### In Progress
- 🚧 shadcn component installation
- 🚧 Dashboard layout with sidebar
- 🚧 Trend pages (list & detail)
- 🚧 Alert pages
- 🚧 Settings pages
- 🚧 Authentication flows

### Planned
- 📋 Agency workspace
- 📋 SEO content pages (pillars + clusters)
- 📋 Responsive design optimization
- 📋 Accessibility compliance
- 📋 Performance optimization

## Available Scripts

- `npm run dev` - Start development server with Turbopack
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Environment Variables

Required environment variables (see `.env.example`):

- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key (server-side only)
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` - Stripe publishable key
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret
- `NEXT_PUBLIC_APP_URL` - Application URL

## Design System

### Colors
- Primary: `#0066FF` - CTAs, brand accents
- Secondary: `#1A1A1A` - Text, headings
- Accent: `#00D9FF` - Highlights, velocity indicators
- Success: `#00C853` - Positive states
- Warning: `#FFC107` - Medium priority
- Danger: `#FF3B30` - Destructive actions

### Typography
- Display: Clash Display (headings)
- Body: Inter (text)

### Custom Utilities
- `text-heading-1` through `text-heading-4`
- `text-body-lg`, `text-body`, `text-body-sm`
- `text-caption`
- `btn-primary`
- `card`
- `velocity-bar`

## License

MIT - see the root [`../LICENSE`](../LICENSE).
