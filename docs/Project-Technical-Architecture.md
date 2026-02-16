# TrendScope Technical PRD

**The Bloomberg Terminal for Short-Form Video Trends**

Version: 1.0.0 | Status: Draft | Owner: Technical Architect
Date: 2026-02-16

---

## 1. Executive Summary

TrendScope is a real-time TikTok trend detection and alerting platform that monitors velocity at the micro-influencer layer (<10k followers) to identify emerging trends 6-24 hours before mainstream saturation. The platform uses a self-hosted scraping architecture with IPRoyal proxies to achieve 10-50x cost savings over managed APIs.

**Core Value Proposition:** Transform 4+ hours of daily manual "doomscrolling" into automated, actionable intelligence delivered via Slack, email, and dashboard alerts.

**Technical Approach:**
- **Data Collection:** Self-hosted TikTok-Api (Python + Playwright) with IPRoyal rotating residential proxies
- **Processing:** Producer-consumer pattern with Redis queue for 72-hour hot window analysis
- **Storage:** Redis (hot cache with TTL) + PostgreSQL (persistent trends)
- **API:** FastAPI for synchronous endpoints
- **Detection:** Exponential growth algorithms (R² > 0.85) with adaptive percentile thresholds

**Cost Target:** $7-45/month (existing VPS + IPRoyal at $7.50/GB)

---

## 2. Steel Thread (MVP Scope)

### 2.1 Critical User Journeys

#### [CUJ-01] User Registration & Onboarding

- **Trigger:** User visits landing page and clicks "Get Started"
- **Frontend:** Signup form → Supabase Auth → Email verification
- **Backend:** Auth trigger creates user profile with default tier (Free)
- **Flow:** 
  1. User enters email/password
  2. Supabase Auth creates account
  3. Database trigger creates `public.profiles` row
  4. User selects niches (1 for Free, up to 5 for Solo)
  5. User configures alert channel (Slack webhook or email)
  6. Dashboard shows "Monitoring Active" status
- **Success:** User receives first trend alert within 24 hours

#### [CUJ-02] Trend Detection & Alert Delivery

- **Trigger:** Scraper ingests new video data
- **Backend:** 
  1. Producer pushes video metadata to Redis queue
  2. Consumer processes batch and updates trend velocity
  3. Detection engine evaluates growth patterns
  4. Alert pipeline evaluates user preferences and thresholds
  5. Alerts dispatched via configured channels
- **Frontend:** Dashboard updates with new trends, alert history logged
- **Success:** User receives relevant trend alert within tier latency (Free: weekly digest, Solo: 2-hour, Agency: 30-min)

#### [CUJ-03] Trend Review & Action

- **Trigger:** User clicks trend alert or navigates to trend detail
- **Frontend:** 
  1. Display trend header (name, velocity score, saturation %)
  2. Show velocity graph (24-hour history)
  3. List example videos (3 thumbnails linking to TikTok)
  4. Display related hashtags/sounds
- **Backend:** API serves aggregated trend data from PostgreSQL
- **Actions:**
  - "Create Video" → External link to TikTok
  - "Bookmark" → Save to user bookmarks
  - "Dismiss" → Mark as not interested
- **Success:** User decides to act on trend within 30 seconds

#### [CUJ-04] Subscription Upgrade

- **Trigger:** User clicks "Upgrade" from Free tier
- **Frontend:** Pricing page with tier comparison
- **Backend:**
  1. Stripe Checkout session created
  2. User completes payment
  3. Stripe webhook updates subscription status
  4. Database reflects new tier and feature access
- **Success:** User immediately gains access to paid features

#### [CUJ-05] Agency Client Management

- **Trigger:** Agency user navigates to Clients section
- **Frontend:** Client list with add/edit capabilities
- **Backend:**
  1. Create client workspace with unique configuration
  2. Assign niche preferences per client
  3. Configure separate alert destinations
  4. Generate white-label trend reports
- **Success:** Agency manages 5 client workspaces with isolated alert streams

---

## 3. Technical Specifications

### 3.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TRENDSCOPE PLATFORM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       DATA COLLECTION LAYER                          │   │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │   │
│  │  │ TikTok-Api   │───▶│ Redis Queue  │───▶│ PostgreSQL (Trends)  │  │   │
│  │  │ (Playwright) │    │ (Hot Cache)  │    │ (Persistent)         │  │   │
│  │  └──────────────┘    └──────────────┘    └──────────────────────┘  │   │
│  │         │                   │                    │                 │   │
│  │         ▼                   ▼                    ▼                 │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │              PROCESSING LAYER (Python/FastAPI)               │  │   │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │  │   │
│  │  │  │ Producer     │  │ Consumer     │  │ Trend Detector   │   │  │   │
│  │  │  │ (Scraper)    │  │ (Processor)  │  │ (Growth Engine)  │   │  │   │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────┘   │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌─────────────────────────────────┼─────────────────────────────────────┐  │
│  │                    ALERT & DELIVERY LAYER                             │  │
│  │                         │                                            │  │
│  │    ┌────────────────────┼────────────────────┐                       │  │
│  │    ▼                    ▼                    ▼                       │  │
│  │ ┌─────────┐       ┌──────────┐       ┌──────────┐                   │  │
│  │ │ Slack   │       │ Email    │       │ Webhook  │                   │  │
│  │ │ Service │       │ Service  │       │ Service  │                   │  │
│  │ └─────────┘       └──────────┘       └──────────┘                   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│  ┌─────────────────────────────────┼─────────────────────────────────────┐  │
│  │                         USER LAYER                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐      │  │
│  │  │ Web Dashboard│  │ Supabase Auth│  │ Stripe Integration     │      │  │
│  │  │ (Template)   │  │ (Template)   │  │ (Webhook Handlers)     │      │  │
│  │  └──────────────┘  └──────────────┘  └────────────────────────┘      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Database Schema

**Schema Design Principles:**
- All tables use UUID primary keys
- All tables have `created_at` and `updated_at` timestamps
- RLS policies enforce user data isolation
- JSONB for flexible configuration fields

#### Core Tables

```sql
-- Users and Profiles (extends Supabase Auth)
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'solo', 'agency', 'enterprise')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'cancelled')),
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    email_notifications BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User Niche Preferences
CREATE TABLE public.user_niches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    niche_id UUID NOT NULL REFERENCES public.niches(id) ON DELETE CASCADE,
    alert_enabled BOOLEAN DEFAULT true,
    velocity_threshold INTEGER DEFAULT 50, -- 0-100 scale
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, niche_id)
);

-- Available Niches
CREATE TABLE public.niches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    hashtag_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alert Integrations (Slack, Webhook)
CREATE TABLE public.alert_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('slack', 'webhook', 'discord')),
    name TEXT NOT NULL,
    config JSONB NOT NULL, -- {webhook_url, channel, format}
    is_active BOOLEAN DEFAULT true,
    last_tested_at TIMESTAMPTZ,
    last_test_status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Detected Trends
CREATE TABLE public.trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL CHECK (type IN ('sound', 'hashtag', 'format')),
    name TEXT NOT NULL,
    platform_id TEXT NOT NULL, -- TikTok's internal ID
    niche_id UUID REFERENCES public.niches(id),
    first_detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    peak_detected_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'emerging' CHECK (status IN ('emerging', 'peaking', 'saturated', 'expired')),
    velocity_score INTEGER CHECK (velocity_score >= 0 AND velocity_score <= 100),
    saturation_percent INTEGER CHECK (saturation_percent >= 0 AND saturation_percent <= 100),
    video_count_start INTEGER,
    video_count_current INTEGER,
    growth_rate DECIMAL(5,2), -- percentage per hour
    metadata JSONB, -- {example_videos, related_hashtags, creator_samples}
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(type, platform_id)
);

-- Trend Velocity History (time-series data)
CREATE TABLE public.trend_velocity_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trend_id UUID NOT NULL REFERENCES public.trends(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    video_count INTEGER NOT NULL,
    velocity_score INTEGER,
    growth_rate DECIMAL(5,2),
    saturation_percent INTEGER
);

-- User Alerts
CREATE TABLE public.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    trend_id UUID NOT NULL REFERENCES public.trends(id) ON DELETE CASCADE,
    channel TEXT NOT NULL CHECK (channel IN ('email', 'slack', 'webhook')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'failed')),
    sent_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    dismissed BOOLEAN DEFAULT false,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User Bookmarks
CREATE TABLE public.bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    trend_id UUID NOT NULL REFERENCES public.trends(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, trend_id)
);

-- Agency Client Workspaces
CREATE TABLE public.clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    logo_url TEXT,
    config JSONB DEFAULT '{}', -- {niches, alert_preferences}
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Client Alert Configurations
CREATE TABLE public.client_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES public.clients(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES public.alert_integrations(id) ON DELETE CASCADE,
    niche_filter JSONB, -- Array of niche IDs to monitor
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- System Configuration
CREATE TABLE public.system_config (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Indexes

```sql
-- Performance indexes
CREATE INDEX idx_profiles_tier ON public.profiles(tier);
CREATE INDEX idx_profiles_stripe_customer ON public.profiles(stripe_customer_id);

CREATE INDEX idx_user_niches_user_id ON public.user_niches(user_id);
CREATE INDEX idx_user_niches_niche_id ON public.user_niches(niche_id);

CREATE INDEX idx_trends_type ON public.trends(type);
CREATE INDEX idx_trends_status ON public.trends(status);
CREATE INDEX idx_trends_niche ON public.trends(niche_id);
CREATE INDEX idx_trends_velocity ON public.trends(velocity_score DESC);
CREATE INDEX idx_trends_detected ON public.trends(first_detected_at DESC);

CREATE INDEX idx_trend_velocity_history_trend ON public.trend_velocity_history(trend_id);
CREATE INDEX idx_trend_velocity_history_timestamp ON public.trend_velocity_history(timestamp DESC);

CREATE INDEX idx_alerts_user_id ON public.alerts(user_id);
CREATE INDEX idx_alerts_trend_id ON public.alerts(trend_id);
CREATE INDEX idx_alerts_status ON public.alerts(status);
CREATE INDEX idx_alerts_created ON public.alerts(created_at DESC);

CREATE INDEX idx_alert_integrations_user ON public.alert_integrations(user_id);

CREATE INDEX idx_clients_agency ON public.clients(agency_id);
```

#### RLS Policies

```sql
-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_niches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alert_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.client_alerts ENABLE ROW LEVEL SECURITY;

-- Note: trends and niches are readable by all authenticated users
-- trend_velocity_history is readable by all authenticated users

-- Profiles: Users can only see/edit own profile
CREATE POLICY "Users can view own profile" 
    ON public.profiles FOR SELECT 
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
    ON public.profiles FOR UPDATE 
    USING (auth.uid() = id);

-- User Niches: Users can only see/edit own niche preferences
CREATE POLICY "Users can view own niches" 
    ON public.user_niches FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own niches" 
    ON public.user_niches FOR ALL 
    USING (auth.uid() = user_id);

-- Alert Integrations: Users can only see/edit own integrations
CREATE POLICY "Users can view own integrations" 
    ON public.alert_integrations FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own integrations" 
    ON public.alert_integrations FOR ALL 
    USING (auth.uid() = user_id);

-- Alerts: Users can only see own alerts
CREATE POLICY "Users can view own alerts" 
    ON public.alerts FOR SELECT 
    USING (auth.uid() = user_id);

-- Bookmarks: Users can only see/manage own bookmarks
CREATE POLICY "Users can view own bookmarks" 
    ON public.bookmarks FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own bookmarks" 
    ON public.bookmarks FOR ALL 
    USING (auth.uid() = user_id);

-- Clients: Agency users can only see own clients
CREATE POLICY "Agencies can view own clients" 
    ON public.clients FOR SELECT 
    USING (auth.uid() = agency_id);

CREATE POLICY "Agencies can manage own clients" 
    ON public.clients FOR ALL 
    USING (auth.uid() = agency_id);

-- Client Alerts: Agencies can only see own client alerts
CREATE POLICY "Agencies can view own client alerts" 
    ON public.client_alerts FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.clients c 
            WHERE c.id = client_alerts.client_id 
            AND c.agency_id = auth.uid()
        )
    );

-- Trends: All authenticated users can read
CREATE POLICY "Authenticated users can view trends" 
    ON public.trends FOR SELECT 
    TO authenticated 
    USING (true);

-- Niches: All authenticated users can read
CREATE POLICY "Authenticated users can view niches" 
    ON public.niches FOR SELECT 
    TO authenticated 
    USING (true);

-- Trend Velocity History: All authenticated users can read
CREATE POLICY "Authenticated users can view velocity history" 
    ON public.trend_velocity_history FOR SELECT 
    TO authenticated 
    USING (true);
```

#### Triggers

```sql
-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER alert_integrations_updated_at
    BEFORE UPDATE ON public.alert_integrations
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER trends_updated_at
    BEFORE UPDATE ON public.trends
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER clients_updated_at
    BEFORE UPDATE ON public.clients
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Profile creation on auth signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

### 3.3 API Contracts

#### Authentication Endpoints

```yaml
POST /auth/signup
  Request:
    email: string (required)
    password: string (required, min 8 chars)
    full_name: string (optional)
  Response:
    201: { user: { id, email, tier }, message: "Check email for verification" }
    400: { error: "Invalid email format" }
    409: { error: "Email already registered" }

POST /auth/login
  Request:
    email: string (required)
    password: string (required)
  Response:
    200: { access_token, refresh_token, user: { id, email, tier } }
    401: { error: "Invalid credentials" }
```

#### Trend Endpoints

```yaml
GET /api/v1/trends
  Query:
    status: string (optional) - 'emerging' | 'peaking' | 'saturated'
    niche: uuid (optional) - filter by niche
    limit: integer (optional, default 20, max 100)
    offset: integer (optional, default 0)
  Response:
    200: {
      trends: [
        {
          id: uuid,
          type: 'sound' | 'hashtag' | 'format',
          name: string,
          velocity_score: integer (0-100),
          saturation_percent: integer (0-100),
          video_count: integer,
          growth_rate: number,
          niche: { id, name },
          first_detected_at: ISO8601,
          status: string
        }
      ],
      total: integer,
      limit: integer,
      offset: integer
    }

GET /api/v1/trends/{id}
  Response:
    200: {
      id: uuid,
      type: string,
      name: string,
      platform_id: string,
      velocity_score: integer,
      saturation_percent: integer,
      video_count_start: integer,
      video_count_current: integer,
      growth_rate: number,
      status: string,
      niche: { id, name },
      first_detected_at: ISO8601,
      peak_detected_at: ISO8601 | null,
      metadata: {
        example_videos: [{ id, url, thumbnail, views }],
        related_hashtags: [string],
        creator_samples: [{ username, follower_count }]
      },
      velocity_history: [
        { timestamp: ISO8601, video_count: integer, velocity_score: integer }
      ]
    }
    404: { error: "Trend not found" }
```

#### User Preference Endpoints

```yaml
GET /api/v1/user/niches
  Response:
    200: {
      niches: [
        { id, name, display_name, is_selected: boolean, alert_enabled: boolean }
      ],
      max_allowed: integer,
      current_count: integer
    }

POST /api/v1/user/niches
  Request:
    niche_id: uuid (required)
  Response:
    201: { id, user_id, niche_id, alert_enabled }
    400: { error: "Maximum niches reached for your tier" }
    409: { error: "Niche already selected" }

DELETE /api/v1/user/niches/{niche_id}
  Response:
    204: No content
    404: { error: "Niche not found in preferences" }

GET /api/v1/user/integrations
  Response:
    200: {
      integrations: [
        { id, type, name, is_active, last_tested_at, last_test_status }
      ]
    }

POST /api/v1/user/integrations
  Request:
    type: 'slack' | 'webhook' (required)
    name: string (required)
    config: {
      webhook_url: string (required for slack/webhook),
      channel: string (optional, for slack),
      format: 'compact' | 'detailed' (default: 'detailed')
    }
  Response:
    201: { id, type, name, config, is_active }
    400: { error: "Invalid webhook URL format" }

POST /api/v1/user/integrations/{id}/test
  Response:
    200: { success: true, message: "Test alert sent successfully" }
    400: { error: "Failed to send test alert", details: string }

DELETE /api/v1/user/integrations/{id}
  Response:
    204: No content
```

#### Alert Endpoints

```yaml
GET /api/v1/alerts
  Query:
    status: string (optional) - 'pending' | 'sent' | 'delivered'
    limit: integer (optional, default 20)
    offset: integer (optional, default 0)
  Response:
    200: {
      alerts: [
        {
          id: uuid,
          trend: { id, name, type, velocity_score },
          channel: string,
          status: string,
          sent_at: ISO8601 | null,
          confidence_score: number
        }
      ],
      total: integer
    }

PATCH /api/v1/alerts/{id}/dismiss
  Response:
    200: { dismissed: true }

GET /api/v1/alerts/stats
  Response:
    200: {
      total_this_week: integer,
      total_this_month: integer,
      by_niche: [{ niche_id, niche_name, count }],
      action_rate: number -- percentage of alerts acted upon
    }
```

#### Bookmark Endpoints

```yaml
GET /api/v1/bookmarks
  Response:
    200: {
      bookmarks: [
        {
          id: uuid,
          trend: { id, name, type, velocity_score, saturation_percent },
          notes: string | null,
          created_at: ISO8601
        }
      ]
    }

POST /api/v1/bookmarks
  Request:
    trend_id: uuid (required)
    notes: string (optional)
  Response:
    201: { id, trend_id, notes, created_at }
    409: { error: "Trend already bookmarked" }

DELETE /api/v1/bookmarks/{id}
  Response:
    204: No content
```

#### Client Management (Agency Tier)

```yaml
GET /api/v1/clients
  Response:
    200: {
      clients: [
        { id, name, logo_url, is_active, created_at }
      ],
      total: integer,
      max_allowed: integer
    }

POST /api/v1/clients
  Request:
    name: string (required)
    logo_url: string (optional)
    config: {
      niches: [uuid],
      alert_preferences: object
    }
  Response:
    201: { id, name, config, created_at }
    400: { error: "Maximum clients reached for your tier" }

GET /api/v1/clients/{id}
  Response:
    200: {
      id: uuid,
      name: string,
      logo_url: string | null,
      config: object,
      is_active: boolean,
      created_at: ISO8601,
      alert_integrations: [...],
      recent_trends: [...]
    }

PUT /api/v1/clients/{id}
  Request:
    name: string (optional)
    logo_url: string (optional)
    config: object (optional)
    is_active: boolean (optional)
  Response:
    200: Updated client object

DELETE /api/v1/clients/{id}
  Response:
    204: No content
```

#### Stripe Webhook Endpoints

```yaml
POST /webhooks/stripe
  Description: Stripe webhook endpoint for subscription events
  Headers:
    Stripe-Signature: string (required)
  Body: Stripe event payload
  Events Handled:
    - checkout.session.completed
    - invoice.paid
    - invoice.payment_failed
    - customer.subscription.updated
    - customer.subscription.deleted
  Response:
    200: { received: true }
    400: { error: "Invalid signature" }
```

### 3.4 Scraper Architecture

**Reference:** Detailed implementation in `SELF_HOSTED.md` and `TECH_FEASIBILITY.md`

#### Producer (Scraper)

```python
# scrape/producer.py - Core scraper implementation
"""
TikTok data producer using TikTok-Api library.
Runs continuously, pushing video metadata to Redis queue.

Rate Limits (per SELF_HOSTED.md):
- Trending: 10-20 req/min
- Hashtag: 5-10 req/min  
- User: 2-5 req/min
"""

class TikTokProducer:
    """Produces video data to Redis queue."""
    
    def __init__(self, redis_client: redis.Redis, proxy: str = None):
        self.redis = redis_client
        self.proxy = proxy
        self.rate_limiter = RateLimiter(rate=0.17, burst=5)  # ~10 req/min
        
    async def scrape_trending(self, count: int = 100):
        """Fetch trending videos and push to Redis."""
        async with TikTokApi() as api:
            async for video in api.trending.videos(count=count):
                await self.rate_limiter.acquire()
                
                data = {
                    "id": video.id,
                    "desc": video.desc,
                    "createTime": video.create_time,
                    "stats": {
                        "playCount": video.stats.play_count,
                        "diggCount": video.stats.digg_count,
                        "shareCount": video.stats.share_count,
                        "commentCount": video.stats.comment_count,
                    },
                    "author": {
                        "uniqueId": video.author.unique_id,
                        "followerCount": video.author.stats.follower_count,
                    },
                    "music": {
                        "id": video.sound.id if video.sound else None,
                        "title": video.sound.title if video.sound else None,
                    },
                    "hashtags": [t.name for t in video.hashtags],
                    "scrapedAt": datetime.utcnow().isoformat(),
                }
                
                # Push to Redis with 72-hour TTL
                await self.redis.lpush("tiktok:videos", json.dumps(data))
                await self.redis.expire("tiktok:videos", 72 * 3600)
                
    async def scrape_hashtag(self, hashtag: str, count: int = 100):
        """Fetch videos for specific hashtag."""
        async with TikTokApi() as api:
            tag = api.hashtag(name=hashtag)
            async for video in tag.videos(count=count):
                await self.rate_limiter.acquire()
                # Process and push to Redis...
```

#### Consumer (Processor)

```python
# scrape/consumer.py - Data processing and trend detection
"""
Consumes video data from Redis, detects trends, triggers alerts.
"""

class TrendConsumer:
    """Consumes video data and detects trends."""
    
    def __init__(self, redis_client: redis.Redis, db: asyncpg.Pool):
        self.redis = redis_client
        self.db = db
        
    async def consume(self, batch_size: int = 50):
        """Main consumption loop."""
        while True:
            batch = await self.redis.lrange("tiktok:videos", 0, batch_size - 1)
            
            if not batch:
                await asyncio.sleep(5)
                continue
            
            # Remove processed items
            await self.redis.ltrim("tiktok:videos", batch_size, -1)
            
            # Process batch
            for item in batch:
                video = json.loads(item)
                await self.process_video(video)
    
    async def process_video(self, video: dict):
        """Process single video and update trends."""
        # 1. Extract sound/hashtag trends from video
        trends = self.extract_trends(video)
        
        for trend in trends:
            # 2. Update trend velocity
            await self.update_trend_velocity(trend, video)
            
            # 3. Check if alert should be triggered
            if await self.should_alert(trend):
                await self.trigger_alerts(trend)
    
    async def update_trend_velocity(self, trend: dict, video: dict):
        """Update trend metrics and calculate velocity."""
        # Store in Redis for hot window analysis
        trend_key = f"trend:{trend['type']}:{trend['platform_id']}"
        
        # Get existing data
        existing = await self.redis.get(trend_key)
        if existing:
            data = json.loads(existing)
            data['videos'].append(video)
        else:
            data = {
                'type': trend['type'],
                'platform_id': trend['platform_id'],
                'name': trend['name'],
                'first_seen': video['scrapedAt'],
                'videos': [video]
            }
        
        # Update with 72-hour TTL
        await self.redis.setex(trend_key, 72 * 3600, json.dumps(data))
        
        # Calculate velocity (see TECH_FEASIBILITY.md Section 2)
        velocity = self.calculate_velocity(data['videos'])
        
        # Persist to PostgreSQL if significant
        if velocity['score'] > 50:
            await self.persist_trend(trend, velocity)
    
    def calculate_velocity(self, videos: list) -> dict:
        """
        Calculate trend velocity using exponential growth detection.
        
        Algorithm from TECH_FEASIBILITY.md Section 2:
        1. Fit exponential curve to video count over time
        2. Calculate R² to determine exponential fit quality
        3. If R² > 0.85, growth is exponential
        4. Calculate growth rate and doubling time
        """
        # Extract timestamps and counts
        times = []
        counts = []
        
        for i, video in enumerate(sorted(videos, key=lambda x: x['scrapedAt'])):
            times.append(i)
            counts.append(video['stats']['playCount'])
        
        if len(times) < 3:
            return {'score': 0, 'growth_rate': 0}
        
        # Log-transform for exponential fitting
        log_counts = np.log(counts)
        
        # Linear regression on log-transformed data
        slope, intercept, r_value, _, _ = linregress(times, log_counts)
        r_squared = r_value ** 2
        
        # Growth rate from slope
        growth_rate = slope * 100  # Convert to percentage
        
        # Doubling time (Rule of 70)
        doubling_time = 70 / growth_rate if growth_rate > 0 else float('inf')
        
        # Velocity score (0-100)
        if r_squared > 0.85 and growth_rate > 50:
            velocity_score = min(100, int(growth_rate))
        else:
            velocity_score = int(growth_rate * r_squared)
        
        return {
            'score': velocity_score,
            'growth_rate': round(growth_rate, 2),
            'doubling_time': round(doubling_time, 2),
            'r_squared': round(r_squared, 3),
            'is_exponential': r_squared > 0.85
        }
    
    async def should_alert(self, trend: dict) -> bool:
        """Determine if trend should trigger alerts."""
        # Check if alert already sent recently
        recent_alert = await self.db.fetchval(
            """
            SELECT 1 FROM alerts 
            WHERE trend_id = $1 
            AND created_at > NOW() - INTERVAL '1 hour'
            """,
            trend['id']
        )
        
        if recent_alert:
            return False
        
        # Check velocity threshold
        # (Additional logic for per-user thresholds)
        
        return True
    
    async def trigger_alerts(self, trend: dict):
        """Send alerts to subscribed users."""
        # Get users subscribed to this niche
        users = await self.db.fetch(
            """
            SELECT u.id, u.email, u.tier, un.velocity_threshold
            FROM profiles u
            JOIN user_niches un ON u.id = un.user_id
            WHERE un.niche_id = $1
            AND un.alert_enabled = true
            """,
            trend['niche_id']
        )
        
        for user in users:
            # Check tier-based latency
            if not self.should_send_for_tier(user['tier'], trend):
                continue
            
            # Create alert record
            alert_id = await self.db.fetchval(
                """
                INSERT INTO alerts (user_id, trend_id, channel, confidence_score)
                VALUES ($1, $2, 'slack', $3)
                RETURNING id
                """,
                user['id'], trend['id'], trend['velocity']['score'] / 100
            )
            
            # Send via appropriate channel
            await self.send_alert(alert_id, user, trend)
    
    def should_send_for_tier(self, tier: str, trend: dict) -> bool:
        """Check if alert should be sent based on tier latency."""
        tier_latency = {
            'free': 24 * 3600,      # Daily digest
            'solo': 2 * 3600,       # 2 hours
            'agency': 30 * 60,      # 30 minutes
            'enterprise': 0         # Real-time
        }
        
        latency = tier_latency.get(tier, 24 * 3600)
        
        # For non-real-time tiers, check if within digest window
        if latency > 0:
            # Logic for batching alerts
            pass
        
        return True
```

### 3.5 Alert Delivery Services

```python
# services/slack_service.py
"""
Slack alert delivery service.
Formats and sends trend alerts to configured Slack webhooks.
"""

class SlackService:
    """Sends trend alerts to Slack channels."""
    
    async def send_trend_alert(self, webhook_url: str, trend: dict, format: str = 'detailed'):
        """Send trend alert to Slack webhook."""
        
        if format == 'compact':
            message = self._format_compact(trend)
        else:
            message = self._format_detailed(trend)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=message,
                timeout=30.0
            )
            response.raise_for_status()
    
    def _format_detailed(self, trend: dict) -> dict:
        """Format detailed Slack message."""
        saturation_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🔴'
        }
        
        saturation_level = 'low' if trend['saturation_percent'] < 30 else \
                          'medium' if trend['saturation_percent'] < 70 else 'high'
        
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🔥 TREND ALERT: {trend['name'][:50]}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Niche:*\n#{trend['niche']['name']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Growth:*\n+{trend['growth_rate']}% in 3hrs"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Videos:*\n{trend['video_count_current']:,}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Saturation:*\n{saturation_emoji[saturation_level]} {trend['saturation_percent']}%"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Velocity Score:* {trend['velocity_score']}/100\n*Window:* {trend.get('window_hours', '6-8')} hours"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Details"
                            },
                            "url": f"https://trendscope.io/trends/{trend['id']}"
                        }
                    ]
                }
            ]
        }
```

---

## 4. Non-Functional Requirements

### 4.1 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Scraper Throughput** | 10K-50K videos/day | Processed videos |
| **Trend Detection Latency** | < 5 minutes | Time from ingestion to detection |
| **Alert Delivery Latency** | < 2 minutes | Time from detection to delivery |
| **API Response Time** | < 200ms p95 | API endpoint latency |
| **Dashboard Load Time** | < 3 seconds | Initial page load |
| **Redis Query Time** | < 10ms | Hot cache lookups |

### 4.2 Scalability Limits (MVP)

| Resource | MVP Limit | Growth Path |
|----------|-----------|-------------|
| **Concurrent Users** | 1,000 | Horizontal scaling |
| **Videos/Day** | 50,000 | Add workers |
| **Trends/Day** | 500 | Optimize queries |
| **Redis Memory** | 1GB (hot window) | Increase TTL precision |
| **PostgreSQL Size** | 10GB | Partition history tables |

### 4.3 Security Requirements

#### Authentication & Authorization
- Supabase Auth with email/password
- JWT tokens with 1-hour access, 7-day refresh
- RLS policies enforce data isolation
- Service role key never exposed to client

#### Data Protection
- Proxy credentials in `.env` (never committed)
- Database credentials via environment variables
- Stripe webhook signature verification
- No PII in logs

#### Rate Limiting
| Endpoint | Limit |
|----------|-------|
| Auth endpoints | 5 req/min per IP |
| API endpoints | 100 req/min per user |
| Stripe webhooks | 100 req/min |

### 4.4 Reliability Requirements

| Component | Uptime Target | Recovery Time |
|-----------|---------------|---------------|
| API | 99.9% | < 5 minutes |
| Scraper | 95% | Auto-restart |
| Alert Delivery | 99% | Retry queue |

### 4.5 Data Retention

| Data Type | Retention | Storage |
|-----------|-----------|---------|
| Video metadata (hot) | 72 hours | Redis |
| Trend data | 90 days | PostgreSQL |
| Alert history | 1 year | PostgreSQL |
| User activity | 2 years | PostgreSQL |
| System logs | 30 days | Files |

---

## 5. Security Architecture

### 5.1 Function Classification

| Function Type | Access Level | Examples |
|---------------|--------------|----------|
| **Internal-Only** | Server-side only | Scraper, trend detection, Stripe webhooks |
| **Public RPC** | Authenticated users | Trend queries, user preferences |
| **Admin-Only** | Service role | System config, user management |

### 5.2 RPC Exposure Policy

**ALLOWED for client RPC:**
- `get_trends()` - Read-only trend data
- `get_user_niches()` - User's own preferences
- `update_user_profile()` - Own profile updates

**DENIED for client RPC (server-side only):**
- `create_trend()` - Internal scraper only
- `process_payment()` - Stripe webhooks only
- `update_subscription()` - Server-side validation required

### 5.3 SECURITY DEFINER Policy

All SECURITY DEFINER functions MUST include:
```sql
SET search_path = 'public'
```

**Example:**
```sql
CREATE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = 'public'  -- REQUIRED
AS $$
BEGIN
    INSERT INTO public.profiles (id, email)
    VALUES (NEW.id, NEW.email);
    RETURN NEW;
END;
$$;
```

### 5.4 RLS Policy Matrix

| Table | SELECT | INSERT | UPDATE | DELETE |
|-------|--------|--------|--------|--------|
| profiles | Own row | Auth trigger | Own row | No |
| user_niches | Own rows | Own rows | Own rows | Own rows |
| alert_integrations | Own rows | Own rows | Own rows | Own rows |
| alerts | Own rows | System only | System only | No |
| bookmarks | Own rows | Own rows | Own rows | Own rows |
| clients | Agency only | Agency only | Agency only | Agency only |
| trends | All auth | System only | System only | No |
| niches | All auth | Admin only | Admin only | No |

### 5.5 High-Risk Operations

**Server-side enforcement required:**
- Subscription tier changes (validate via Stripe)
- Credit/debit operations
- Feature flag changes
- Bulk data exports

**DO NOT:**
- Allow direct client updates to `profiles.tier`
- Expose `stripe_customer_id` in API responses
- Permit cross-user data access
- Skip webhook signature verification

---

## 6. Implementation Stages

**Template-Aware Note:** Phase 4.3 deploys: Frontend UI, Database schema, Auth, Stripe products. These stages focus on backend business logic, scraper integration, and webhook handlers.

### Stage 01: Backend API Core
**Duration:** 6-8 hours
**Dependencies:** None (template provides foundation)

**Scope:**
- Implement API endpoint logic for:
  - Trend queries with filtering/sorting
  - User niche preferences CRUD
  - Alert integrations (Slack webhook management)
  - Bookmark management
  - Client workspace management (Agency tier)
- Create database service layer
- Implement RLS policy validation

**Output:**
- `/backend/app/api/v1/trends.py`
- `/backend/app/api/v1/user.py`
- `/backend/app/api/v1/alerts.py`
- `/backend/app/services/database.py`

**Success Criteria:**
- All API endpoints return correct data
- RLS policies prevent cross-user access
- Unit tests pass for service layer

---

### Stage 02: Stripe Webhook Handlers
**Duration:** 4-6 hours
**Dependencies:** Stage 01

**Scope:**
- Implement webhook endpoint at `/webhooks/stripe`
- Handle subscription lifecycle events:
  - `checkout.session.completed` - Activate subscription
  - `invoice.paid` - Confirm payment, update tier
  - `invoice.payment_failed` - Grace period handling
  - `customer.subscription.updated` - Tier changes
  - `customer.subscription.deleted` - Cancellation
- Implement tier-based feature gates
- Create subscription status sync

**Output:**
- `/backend/app/api/webhooks/stripe.py`
- `/backend/app/services/billing.py`
- `/backend/app/models/subscription.py`

**Success Criteria:**
- Stripe signature verification works
- Subscription changes reflect in database
- Tier-based access control functional

---

### Stage 03: Scraper Integration
**Duration:** 8-10 hours
**Dependencies:** Stage 01

**Scope:**
- Implement TikTok-Api producer with IPRoyal proxy
- Create Redis queue producer-consumer pattern
- Implement rate limiting (per SELF_HOSTED.md):
  - Trending: 10-20 req/min
  - Hashtag: 5-10 req/min
  - User: 2-5 req/min
- Add retry logic with tenacity
- Implement circuit breaker pattern
- Create scraper health monitoring

**Output:**
- `/scraper/producer.py`
- `/scraper/rate_limiter.py`
- `/scraper/retry_handler.py`
- `/scraper/circuit_breaker.py`
- `/scraper/health_check.py`

**Success Criteria:**
- Scraper runs continuously without blocks
- Rate limits respected
- Failed requests retry correctly
- Health check endpoint functional

---

### Stage 04: Trend Detection Engine
**Duration:** 8-10 hours
**Dependencies:** Stage 03

**Scope:**
- Implement velocity calculation (per TECH_FEASIBILITY.md):
  - Exponential growth detection (R² > 0.85)
  - Doubling time analysis
  - Adaptive percentile thresholds
- Create trend persistence logic
- Implement saturation scoring
- Build trend lifecycle management (emerging → peaking → saturated)
- Create velocity history tracking

**Output:**
- `/backend/app/services/trend_detector.py`
- `/backend/app/services/velocity_engine.py`
- `/backend/app/models/trend.py`

**Success Criteria:**
- Trends detected within 5 minutes of velocity threshold
- Velocity scores accurate (validated against sample data)
- Saturation calculation reflects trend lifecycle

---

### Stage 05: Alert Pipeline
**Duration:** 6-8 hours
**Dependencies:** Stage 02, Stage 04

**Scope:**
- Implement alert deduplication (1-hour window)
- Create tier-based latency routing:
  - Free: Daily digest
  - Solo: 2-hour latency
  - Agency: 30-minute latency
  - Enterprise: Real-time
- Build Slack webhook delivery service
- Implement email alert service (via n8n or direct)
- Create alert throttling (prevent fatigue)
- Add alert engagement tracking

**Output:**
- `/backend/app/services/alert_pipeline.py`
- `/backend/app/services/slack_service.py`
- `/backend/app/services/email_service.py`
- `/backend/app/workers/digest_worker.py`

**Success Criteria:**
- Alerts delivered within tier latency
- No duplicate alerts within 1-hour window
- Slack messages formatted correctly
- Email digests generate properly

---

### Stage 06: Monitoring & Observability
**Duration:** 4-6 hours
**Dependencies:** Stage 03, Stage 05

**Scope:**
- Implement Prometheus metrics collection:
  - Scraper: videos_processed, errors, rate_limit_hits
  - API: request_count, latency, error_rate
  - Trends: detection_count, alert_count
  - Alerts: delivery_success, delivery_latency
- Create health check endpoints
- Add structured logging with structlog
- Build dashboard alerts for system health

**Output:**
- `/backend/app/monitoring/metrics.py`
- `/backend/app/monitoring/logging_config.py`
- `/backend/app/api/health.py`

**Success Criteria:**
- Metrics exposed on `/metrics` endpoint
- Logs structured and queryable
- Health checks reflect system state

---

## 7. Git Workflow for AI Agents

### 7.1 Branch Structure

**Strategy:** Linear with Stage Prefixes (3-4 sequential stages)

```
main
├── ai/feat/<agent>/S01-<ticket>/trend-api-endpoints
├── ai/feat/<agent>/S02-<ticket>/stripe-webhooks
├── ai/feat/<agent>/S03-<ticket>/scraper-integration
├── ai/feat/<agent>/S04-<ticket>/trend-detection
├── ai/feat/<agent>/S05-<ticket>/alert-pipeline
└── ai/feat/<agent>/S06-<ticket>/monitoring
```

### 7.2 Branch Naming Convention

```
ai/<type>/<agent>/S<stage>-<ticket>/<description>

Examples:
ai/feat/coder/S01-TASK-101/trend-api-crud
ai/feat/coder/S02-TASK-201/stripe-checkout-webhook
ai/feat/coder/S03-TASK-301/tiktok-scraper-producer
ai/fix/coder/S04-TASK-401/velocity-calculation-bug
```

### 7.3 Stage-to-Branch Mapping

| Stage | Base Branch | AI Branch Pattern | Merge Target |
|-------|-------------|-------------------|--------------|
| 01 API Core | `main` | `ai/feat/*/S01-*/description` | `main` |
| 02 Stripe | `main` | `ai/feat/*/S02-*/description` | `main` |
| 03 Scraper | `main` | `ai/feat/*/S03-*/description` | `main` |
| 04 Detection | `main` | `ai/feat/*/S04-*/description` | `main` |
| 05 Alerts | `main` | `ai/feat/*/S05-*/description` | `main` |
| 06 Monitoring | `main` | `ai/feat/*/S06-*/description` | `main` |

### 7.4 Commit Strategy

- Use Conventional Commits
- Format: `<type>(<scope>): <subject>`

```
feat(api): add trend filtering by niche and status
fix(scraper): handle rate limit errors with exponential backoff
docs(api): add OpenAPI spec for user endpoints
test(detection): add velocity calculation unit tests
```

### 7.5 Module Assignment

| Agent | Modules | Responsibilities |
|-------|---------|------------------|
| **Agent 1** | `/backend/app/api/*`, `/backend/app/services/database.py` | API endpoints, database layer |
| **Agent 2** | `/backend/app/api/webhooks/*`, `/backend/app/services/billing.py` | Stripe integration |
| **Agent 3** | `/scraper/*` | TikTok scraper, producer-consumer |
| **Agent 4** | `/backend/app/services/trend_detector.py`, `/backend/app/services/velocity_engine.py` | Trend detection algorithms |
| **Agent 5** | `/backend/app/services/alert_pipeline.py`, `/backend/app/services/*_service.py` | Alert delivery |
| **Agent 6** | `/backend/app/monitoring/*`, `/backend/app/api/health.py` | Observability |

### 7.6 Pull Request Checklist

- [ ] Tests passing (`pytest`)
- [ ] Type checking passing (`mypy`)
- [ ] Linting passing (`ruff check`)
- [ ] RLS policies verified (if DB changes)
- [ ] API documentation updated (if endpoint changes)
- [ ] No sensitive data exposed in code
- [ ] Links to PRD section implemented

---

## 8. Environment & Deployment

### 8.1 Environment Strategy

| Environment | Purpose | Database | Redis |
|-------------|---------|----------|-------|
| **Local** | Development | Supabase local | Local Docker |
| **Staging** | Integration testing | Supabase staging | Upstash staging |
| **Production** | Live users | Supabase production | Upstash production |

### 8.2 Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/trendscope
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx

# Redis
REDIS_URL=redis://host:6379/0

# Proxy (IPRoyal - credentials in .env)
PROXY_URL=http://user:pass@geo.iproyal.com:12321

# Stripe
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_SOLO=price_xxx
STRIPE_PRICE_AGENCY=price_xxx
STRIPE_PRICE_ENTERPRISE=price_xxx

# App
APP_ENV=development|staging|production
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
API_PORT=8000
METRICS_PORT=9090

# Scraping
SCRAPE_RATE_LIMIT_TRENDING=10
SCRAPE_RATE_LIMIT_HASHTAG=5
SCRAPE_RATE_LIMIT_USER=2
SCRAPE_BATCH_SIZE=100
```

### 8.3 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRODUCTION                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐ │
│  │  FastAPI    │        │  Scraper    │        │  Worker     │ │
│  │  (API)      │        │  (Producer) │        │  (Consumer) │ │
│  │  Container  │        │  Container  │        │  Container  │ │
│  └──────┬──────┘        └──────┬──────┘        └──────┬──────┘ │
│         │                      │                      │        │
│         └──────────────────────┼──────────────────────┘        │
│                                ▼                                │
│                    ┌─────────────────────┐                      │
│                    │   Supabase          │                      │
│                    │   (Auth + DB + RLS) │                      │
│                    └─────────────────────┘                      │
│                                ▲                                │
│         ┌──────────────────────┼──────────────────────┐        │
│         │                      │                      │        │
│  ┌──────┴──────┐        ┌──────┴──────┐        ┌──────┴──────┐ │
│  │  Upstash    │        │  Stripe     │        │  Slack      │ │
│  │  Redis      │        │  (Billing)  │        │  (Alerts)   │ │
│  └─────────────┘        └─────────────┘        └─────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Monitoring & Observability

### 9.1 Metrics Collection

**Scraper Metrics:**
- `scraper_videos_processed_total` - Counter
- `scraper_errors_total` - Counter (by error type)
- `scraper_rate_limit_hits_total` - Counter
- `scraper_processing_duration_seconds` - Histogram

**API Metrics:**
- `api_requests_total` - Counter (by endpoint, method, status)
- `api_request_duration_seconds` - Histogram
- `api_errors_total` - Counter (by endpoint, error type)

**Trend Detection Metrics:**
- `trends_detected_total` - Counter (by niche, type)
- `trend_velocity_score` - Gauge
- `trend_detection_latency_seconds` - Histogram

**Alert Metrics:**
- `alerts_sent_total` - Counter (by channel, tier)
- `alert_delivery_duration_seconds` - Histogram
- `alert_delivery_failures_total` - Counter

### 9.2 Health Checks

**Endpoint:** `GET /health`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "pass", "latency_ms": 12},
    "redis": {"status": "pass", "latency_ms": 3},
    "scraper": {"status": "pass", "last_run": "2026-02-16T20:45:00Z"}
  },
  "timestamp": "2026-02-16T20:48:00Z"
}
```

### 9.3 Alerting Rules

| Condition | Severity | Action |
|-----------|----------|--------|
| Scraper down > 10 min | Critical | Page on-call |
| API error rate > 5% | Warning | Slack alert |
| Redis memory > 80% | Warning | Slack alert |
| Alert delivery failures > 10% | Critical | Page on-call |
| Trend detection latency > 10 min | Warning | Slack alert |

### 9.4 Logging Standards

**Structured JSON logging:**
```json
{
  "timestamp": "2026-02-16T20:48:00Z",
  "level": "INFO",
  "message": "Trend detected",
  "service": "trend-detector",
  "trace_id": "abc123",
  "context": {
    "trend_id": "uuid",
    "trend_name": "Sound Name",
    "velocity_score": 89,
    "niche": "beauty"
  }
}
```

---

## 10. Open Questions

| Question | Status | Impact | Decision Needed By |
|----------|--------|--------|-------------------|
| Which niches to seed initially? | Open | MVP scope | Before Stage 04 |
| Email service provider? | Open | Alert delivery | Before Stage 05 |
| Alert digest frequency? | Open | User experience | Before Stage 05 |
| White-label report format? | Open | Agency tier | Post-MVP |
| Visual similarity detection? | Open | Feature scope | Post-MVP |

---

## 11. Architecture Decision Records

### ADR-001: Self-Hosted Scraping Over Managed APIs

**Status:** Accepted

**Context:** Official TikTok APIs are ineligible for commercial use. Managed alternatives (Apify, Exolyt) cost $400-950/month.

**Decision:** Use self-hosted TikTok-Api with IPRoyal proxies (~$7-45/month).

**Consequences:**
- (+) 10-50x cost reduction
- (+) Full control over rate limiting
- (-) Maintenance burden for scraper
- (-) Risk of TikTok blocking

### ADR-002: Redis Hot Window + PostgreSQL Persistence

**Status:** Accepted

**Context:** Video metadata is only relevant for 72-hour trend detection window.

**Decision:** Use Redis with 72-hour TTL for hot data, PostgreSQL for persistent trends only.

**Consequences:**
- (+) Minimal storage costs (~100MB vs GBs)
- (+) Fast velocity calculations
- (-) Cannot query historical video data

### ADR-003: FastAPI + Async Python for Backend

**Status:** Accepted

**Context:** Need async I/O for concurrent scraper processing and API requests.

**Decision:** Use FastAPI with async Python (3.11+).

**Consequences:**
- (+) High performance for I/O bound operations
- (+) Native async/await support
- (+) Automatic OpenAPI documentation
- (-) Python overhead vs Go/Rust

### ADR-004: Supabase for Auth and Database

**Status:** Accepted

**Context:** Need managed auth, database, and RLS policies.

**Decision:** Use Supabase (PostgreSQL + Auth + RLS).

**Consequences:**
- (+) Managed authentication
- (+) Built-in RLS
- (+) Real-time subscriptions available
- (-) Vendor lock-in

---

## 12. Critical Constraints

### 12.1 Database Schema - Critical Constraints

**DO NOT:**
- Remove `user_id` from WHERE clauses on user-owned tables
- Use `SELECT *` without WHERE on `profiles`, `user_niches`, `alert_integrations`
- Store proxy credentials in database (use environment variables)
- Expose `stripe_customer_id` in API responses
- Allow direct client updates to `profiles.tier`

### 12.2 Scraper - Critical Constraints

**DO NOT:**
- Scrape without IPRoyal proxy rotation
- Exceed rate limits (will trigger blocks)
- Store video content (only metadata)
- Run scraper without circuit breaker
- Log full video URLs with user data

**NEVER:**
- Commit `.env` file with proxy credentials
- Hardcode proxy URLs in source code
- Disable SSL verification for proxy connections

### 12.3 API - Critical Constraints

**DO NOT:**
- Return sensitive fields (`stripe_customer_id`, `email` for other users)
- Skip authentication on user data endpoints
- Allow unbounded query results (always use LIMIT)
- Expose internal error details to client

### 12.4 Stripe - Critical Constraints

**NEVER:**
- Process webhooks without signature verification
- Update tier without validating Stripe event
- Trust client-sent tier changes
- Log full webhook payloads (may contain PII)

---

## References

- Master Concept: `docs/concept/master-concept.md`
- Brand Kit: `docs/brand/brand-kit-guide.md`
- UX Design: `docs/mvp-ux-trendscope.md`
- Technical Feasibility: `TECH_FEASIBILITY.md`
- Self-Hosted Guide: `SELF_HOSTED.md`

---

*Document Version: 1.0.0*
*Last Updated: 2026-02-16*
*Next Review: After Stage 01 completion*
