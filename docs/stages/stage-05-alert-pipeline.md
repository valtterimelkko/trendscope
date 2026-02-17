# Stage 05: Alert Pipeline

**Stage ID:** 05
**Name:** Alert Pipeline
**Duration:** 6-8 hours
**Status:** Not Started
**Dependencies:** Stage 02 (Stripe Webhooks), Stage 04 (Trend Detection Engine)

---

## 1. Overview

### Purpose
Implement the alert delivery pipeline that notifies users of detected trends based on their preferences and subscription tier.

### Key Deliverables
- Alert deduplication service (1-hour window)
- Tier-based latency routing and batching
- Slack webhook delivery service
- Email alert service integration
- Alert throttling (prevent fatigue)
- Alert engagement tracking
- Digest worker for batched alerts

### Success Criteria
- [ ] Alerts delivered within tier latency bounds
- [ ] No duplicate alerts within 1-hour window
- [ ] Slack messages formatted correctly with Block Kit
- [ ] Email digests generate properly
- [ ] Alert engagement tracked (opened, clicked)
- [ ] Throttling prevents alert fatigue

---

## 2. Dependencies

### Must Complete First
- **Stage 02 (Stripe Webhooks)** - For tier information and feature gates
- **Stage 04 (Trend Detection Engine)** - For detected trends to alert on

### External Dependencies
- Redis for alert batching and deduplication
- Slack Webhook URLs (configured by users)
- Email service (SendGrid/Resend)

### Can Run In Parallel
- Stage 06 (Monitoring & Observability)

### Blocks
- None (this is a terminal stage for alerting)

---

## 3. Technical Components

### 3.1 Directory Structure

```
/backend/app/services/alerts/
├── __init__.py
├── alert_pipeline.py       # Main orchestration
├── deduplication.py        # 1-hour window deduplication
├── tier_router.py          # Tier-based latency routing
├── throttling.py           # Alert fatigue prevention
├── slack_service.py        # Slack webhook delivery
├── email_service.py        # Email delivery
├── digest_worker.py        # Batched digest generation
├── engagement_tracker.py   # Open/click tracking
└── models.py               # Pydantic models
```

### 3.2 Alert Pipeline Service

```python
# alert_pipeline.py
"""
Main alert orchestration service.
Coordinates deduplication, routing, and delivery.
"""

class AlertPipeline:
    """Orchestrates alert delivery pipeline."""

    def __init__(
        self,
        db: asyncpg.Pool,
        redis: redis.Redis,
        slack_service: SlackService,
        email_service: EmailService,
        digest_worker: DigestWorker
    ):
        self.db = db
        self.redis = redis
        self.slack = slack_service
        self.email = email_service
        self.digest = digest_worker
        self.dedup = DeduplicationService(redis)
        self.throttle = ThrottlingService(redis)
        self.router = TierRouter()

    async def process_trend_alert(self, trend: Trend) -> List[AlertResult]:
        """
        Main entry point for trend alerting.

        1. Find users subscribed to trend's niche
        2. Check deduplication (1-hour window)
        3. Apply throttling (prevent fatigue)
        4. Route by tier (latency batching)
        5. Deliver via appropriate channels
        6. Track engagement
        """
        # Get subscribed users
        users = await self._get_subscribed_users(trend.niche_id)

        results = []
        for user in users:
            # Deduplication check
            if await self.dedup.is_duplicate(user.id, trend.id):
                continue

            # Throttling check
            if await self.throttle.should_throttle(user.id, trend.niche_id):
                continue

            # Route by tier
            routing = self.router.get_routing(user.tier)

            if routing.is_immediate:
                # Real-time delivery
                result = await self._deliver_immediate(user, trend)
            else:
                # Batch for digest
                await self.digest.queue_alert(user.id, trend, routing.delay_seconds)
                result = AlertResult(queued=True)

            results.append(result)

        return results

    async def _get_subscribed_users(self, niche_id: UUID) -> List[User]:
        """Get users subscribed to niche with alert enabled."""
        return await self.db.fetch("""
            SELECT u.id, u.email, u.tier, u.email_notifications,
                   ai.id as integration_id, ai.type as integration_type,
                   ai.config as integration_config
            FROM profiles u
            JOIN user_niches un ON u.id = un.user_id
            LEFT JOIN alert_integrations ai ON u.id = ai.user_id AND ai.is_active = true
            WHERE un.niche_id = $1
            AND un.alert_enabled = true
            AND u.status = 'active'
        """, niche_id)
```

### 3.3 Tier-Based Latency Router

```python
# tier_router.py
"""
Routes alerts based on subscription tier.
"""

from dataclasses import dataclass
from enum import Enum

class Tier(Enum):
    FREE = "free"
    SOLO = "solo"
    AGENCY = "agency"
    ENTERPRISE = "enterprise"

@dataclass
class RoutingDecision:
    is_immediate: bool
    delay_seconds: int
    batch_type: str  # "realtime", "hourly", "daily", "weekly"
    max_alerts_per_batch: int

class TierRouter:
    """Determines alert routing based on tier."""

    TIER_CONFIG = {
        Tier.FREE: RoutingDecision(
            is_immediate=False,
            delay_seconds=7 * 24 * 3600,  # Weekly
            batch_type="weekly",
            max_alerts_per_batch=10
        ),
        Tier.SOLO: RoutingDecision(
            is_immediate=False,
            delay_seconds=2 * 3600,  # 2 hours
            batch_type="hourly",
            max_alerts_per_batch=20
        ),
        Tier.AGENCY: RoutingDecision(
            is_immediate=False,
            delay_seconds=30 * 60,  # 30 minutes
            batch_type="hourly",
            max_alerts_per_batch=50
        ),
        Tier.ENTERPRISE: RoutingDecision(
            is_immediate=True,
            delay_seconds=0,
            batch_type="realtime",
            max_alerts_per_batch=0  # No limit
        )
    }

    def get_routing(self, tier: str) -> RoutingDecision:
        return self.TIER_CONFIG.get(Tier(tier), self.TIER_CONFIG[Tier.FREE])
```

### 3.4 Deduplication Service

```python
# deduplication.py
"""
Prevents duplicate alerts within time windows.
"""

class DeduplicationService:
    """Redis-based alert deduplication."""

    DEDUP_TTL = 3600  # 1 hour

    def __init__(self, redis: redis.Redis):
        self.redis = redis

    async def is_duplicate(self, user_id: UUID, trend_id: UUID) -> bool:
        """Check if alert was recently sent for this user+trend."""
        key = f"alert:dedup:{user_id}:{trend_id}"
        return await self.redis.exists(key) > 0

    async def mark_sent(self, user_id: UUID, trend_id: UUID):
        """Mark alert as sent to prevent duplicates."""
        key = f"alert:dedup:{user_id}:{trend_id}"
        await self.redis.setex(key, self.DEDUP_TTL, "1")
```

### 3.5 Throttling Service

```python
# throttling.py
"""
Prevents alert fatigue by limiting frequency.
"""

class ThrottlingService:
    """Alert throttling to prevent fatigue."""

    MAX_ALERTS_PER_HOUR = {
        "free": 5,
        "solo": 15,
        "agency": 30,
        "enterprise": 100
    }
    MAX_ALERTS_PER_DAY_PER_NICHE = 3

    def __init__(self, redis: redis.Redis):
        self.redis = redis

    async def should_throttle(self, user_id: UUID, niche_id: UUID) -> bool:
        """Check if user should be throttled."""
        # Check hourly limit
        hourly_key = f"alert:throttle:{user_id}:hourly"
        hourly_count = int(await self.redis.get(hourly_key) or 0)

        # Get user tier from cache or DB
        tier = await self._get_user_tier(user_id)
        hourly_limit = self.MAX_ALERTS_PER_HOUR.get(tier, 5)

        if hourly_count >= hourly_limit:
            return True

        # Check per-niche daily limit
        niche_key = f"alert:throttle:{user_id}:niche:{niche_id}:daily"
        niche_count = int(await self.redis.get(niche_key) or 0)

        if niche_count >= self.MAX_ALERTS_PER_DAY_PER_NICHE:
            return True

        return False

    async def increment_counters(self, user_id: UUID, niche_id: UUID):
        """Increment throttle counters after sending alert."""
        hourly_key = f"alert:throttle:{user_id}:hourly"
        niche_key = f"alert:throttle:{user_id}:niche:{niche_id}:daily"

        pipe = self.redis.pipeline()
        pipe.incr(hourly_key)
        pipe.expire(hourly_key, 3600)  # 1 hour TTL
        pipe.incr(niche_key)
        pipe.expire(niche_key, 86400)  # 24 hour TTL
        await pipe.execute()
```

### 3.6 Slack Service

```python
# slack_service.py
"""
Slack webhook delivery service.
Formats and sends trend alerts to Slack channels.
"""

class SlackService:
    """Sends trend alerts to Slack webhooks."""

    async def send_trend_alert(
        self,
        webhook_url: str,
        trend: Trend,
        format: str = 'detailed'
    ) -> bool:
        """Send trend alert to Slack webhook."""

        message = self._format_detailed(trend)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    webhook_url,
                    json=message,
                    timeout=30.0
                )
                response.raise_for_status()
                return True
            except Exception as e:
                logger.error(f"Slack delivery failed: {e}")
                return False

    def _format_detailed(self, trend: Trend) -> dict:
        """Format detailed Slack message using Block Kit."""
        saturation_emoji = self._get_saturation_emoji(trend.saturation_percent)

        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🔥 TREND ALERT: {trend.name[:50]}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Niche:*\n#{trend.niche.name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Growth:*\n+{trend.growth_rate}% in 3hrs"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Videos:*\n{trend.video_count_current:,}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Saturation:*\n{saturation_emoji} {trend.saturation_percent}%"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Velocity Score:* {trend.velocity_score}/100\n*Window:* ~6-8 hours"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Details"},
                            "url": f"https://trendscope.io/trends/{trend.id}"
                        }
                    ]
                }
            ]
        }

    def _get_saturation_emoji(self, saturation: int) -> str:
        if saturation < 30:
            return '🟢'  # Low - good opportunity
        elif saturation < 70:
            return '🟡'  # Medium - still viable
        else:
            return '🔴'  # High - may be saturated
```

### 3.7 Email Service

```python
# email_service.py
"""
Email alert delivery service.
"""

class EmailService:
    """Sends trend alerts via email."""

    def __init__(self, api_key: str, from_email: str):
        self.api_key = api_key
        self.from_email = from_email
        # Use SendGrid or Resend client

    async def send_trend_alert(
        self,
        to_email: str,
        trend: Trend
    ) -> bool:
        """Send individual trend alert email."""
        subject = f"🔥 Trend Alert: {trend.name[:40]}"
        html_content = self._render_trend_email(trend)

        # Send via email provider
        # ...

    async def send_digest(
        self,
        to_email: str,
        trends: List[Trend],
        digest_type: str  # "daily", "weekly"
    ) -> bool:
        """Send batched digest email."""
        subject = f"📊 Your {digest_type.title()} Trend Digest"
        html_content = self._render_digest_email(trends, digest_type)

        # Send via email provider
        # ...
```

### 3.8 Digest Worker

```python
# digest_worker.py
"""
Background worker for batched alert digests.
"""

class DigestWorker:
    """Processes batched alerts for non-realtime tiers."""

    async def queue_alert(
        self,
        user_id: UUID,
        trend: Trend,
        delay_seconds: int
    ):
        """Queue alert for batched delivery."""
        queue_key = f"digest:queue:{user_id}"

        alert_data = {
            "trend_id": str(trend.id),
            "trend_name": trend.name,
            "velocity_score": trend.velocity_score,
            "niche_name": trend.niche.name,
            "queued_at": datetime.utcnow().isoformat()
        }

        await self.redis.rpush(queue_key, json.dumps(alert_data))
        await self.redis.expire(queue_key, 7 * 86400)  # 7 days max

    async def process_hourly_digests(self):
        """Process all hourly digests (Solo tier)."""
        # Find users with pending hourly digests
        # Send batched email/Slack
        pass

    async def process_daily_digests(self):
        """Process all daily digests (Free tier)."""
        # Find users with pending daily digests
        # Send batched email
        pass

    async def process_weekly_digests(self):
        """Process all weekly digests (Free tier)."""
        # Find users with pending weekly digests
        # Send batched email summary
        pass
```

### 3.9 Engagement Tracker

```python
# engagement_tracker.py
"""
Tracks alert engagement for analytics.
"""

class EngagementTracker:
    """Tracks when users open/click alerts."""

    async def record_sent(self, alert_id: UUID):
        """Record that alert was sent."""
        await self.db.execute("""
            UPDATE alerts
            SET status = 'sent', sent_at = NOW()
            WHERE id = $1
        """, alert_id)

    async def record_opened(self, alert_id: UUID):
        """Record that alert was opened."""
        await self.db.execute("""
            UPDATE alerts
            SET status = 'delivered', opened_at = NOW()
            WHERE id = $1
        """, alert_id)

    async def record_clicked(self, alert_id: UUID):
        """Record that alert link was clicked."""
        await self.db.execute("""
            UPDATE alerts
            SET clicked_at = NOW()
            WHERE id = $1
        """, alert_id)

    async def get_engagement_stats(self, user_id: UUID) -> dict:
        """Get engagement statistics for user."""
        return await self.db.fetchrow("""
            SELECT
                COUNT(*) as total_alerts,
                COUNT(opened_at) as opened,
                COUNT(clicked_at) as clicked,
                ROUND(COUNT(opened_at)::numeric / NULLIF(COUNT(*), 0) * 100, 1) as open_rate,
                ROUND(COUNT(clicked_at)::numeric / NULLIF(COUNT(*), 0) * 100, 1) as click_rate
            FROM alerts
            WHERE user_id = $1
            AND created_at > NOW() - INTERVAL '30 days'
        """, user_id)
```

---

## 4. API Contracts

### Internal Service Interfaces

```yaml
# Alert Pipeline Service
alert_pipeline.process_trend_alert(trend: Trend) -> List[AlertResult]

# Deduplication
deduplication.is_duplicate(user_id: UUID, trend_id: UUID) -> bool
deduplication.mark_sent(user_id: UUID, trend_id: UUID) -> void

# Throttling
throttling.should_throttle(user_id: UUID, niche_id: UUID) -> bool
throttling.increment_counters(user_id: UUID, niche_id: UUID) -> void

# Slack
slack_service.send_trend_alert(webhook_url: str, trend: Trend) -> bool

# Email
email_service.send_trend_alert(to_email: str, trend: Trend) -> bool
email_service.send_digest(to_email: str, trends: List[Trend], digest_type: str) -> bool
```

### Tracking Endpoints

```yaml
GET /api/alerts/track/{alert_id}/open
  Description: Pixel tracking for email opens
  Response: 1x1 transparent GIF

GET /api/alerts/track/{alert_id}/click
  Description: Redirect tracking for link clicks
  Query: redirect_url (required)
  Response: 302 redirect to destination
```

---

## 5. Database Interactions

### Tables Used

- `alerts` - Alert records with status tracking
- `profiles` - User tier and email settings
- `user_niches` - Alert preferences per niche
- `alert_integrations` - Slack webhook configurations

### Key Queries

```sql
-- Get subscribed users for niche
SELECT u.id, u.email, u.tier, u.email_notifications,
       ai.id as integration_id, ai.type, ai.config
FROM profiles u
JOIN user_niches un ON u.id = un.user_id
LEFT JOIN alert_integrations ai ON u.id = ai.user_id AND ai.is_active = true
WHERE un.niche_id = $1
AND un.alert_enabled = true
AND u.status = 'active';

-- Create alert record
INSERT INTO alerts (user_id, trend_id, channel, confidence_score)
VALUES ($1, $2, $3, $4)
RETURNING id;

-- Update alert status
UPDATE alerts
SET status = $2, sent_at = NOW()
WHERE id = $1;

-- Get engagement stats
SELECT COUNT(*) as total,
       COUNT(opened_at) as opened,
       COUNT(clicked_at) as clicked
FROM alerts
WHERE user_id = $1
AND created_at > NOW() - INTERVAL '30 days';
```

---

## 6. Testing Requirements

### Unit Tests

- [ ] `test_tier_router` - Verify tier latency mapping
- [ ] `test_deduplication` - Verify 1-hour window dedup
- [ ] `test_throttling` - Verify alert fatigue limits
- [ ] `test_slack_formatter` - Verify Block Kit formatting
- [ ] `test_email_formatter` - Verify email rendering
- [ ] `test_digest_queue` - Verify queue operations
- [ ] `test_engagement_tracking` - Verify open/click tracking

### Integration Tests

- [ ] `test_full_pipeline` - End-to-end alert flow
- [ ] `test_slack_delivery` - Actual webhook delivery
- [ ] `test_email_delivery` - Actual email sending (mock)
- [ ] `test_digest_processing` - Hourly/daily batch processing

### Manual Verification

- [ ] Slack alert appears with correct formatting
- [ ] Email alert delivers to inbox
- [ ] Digest emails batch correctly
- [ ] No duplicate alerts received
- [ ] Throttling kicks in after limits
- [ ] Engagement tracked in dashboard

---

## 7. Critical Constraints

### Security

- **DO NOT** expose webhook URLs in API responses (mask them)
- **DO NOT** log full webhook URLs or email addresses
- **VERIFY** user ownership before sending to integration

### Performance

- Process alerts within 5 minutes of trend detection
- Deliver real-time alerts within 2 minutes of processing
- Batch digest emails efficiently (max 100 per batch)

### Reliability

- Retry failed deliveries with exponential backoff
- Queue alerts for retry if external services fail
- Never lose alerts - persist before delivery

---

## 8. Progress Log

| Date | Status | Notes |
|------|--------|-------|
| _ | Not Started | Stage not yet started |

---

## 9. Issues & Blockers

| Issue | Severity | Status | Resolution |
|-------|----------|--------|------------|
| _ | _ | _ | _ |

---

## 10. Completion Checklist

- [ ] Alert pipeline service implemented
- [ ] Deduplication service implemented
- [ ] Throttling service implemented
- [ ] Tier router implemented
- [ ] Slack service implemented
- [ ] Email service implemented
- [ ] Digest worker implemented
- [ ] Engagement tracker implemented
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Manual verification complete
- [ ] Documentation updated

---

## 11. Reference Documents

- [Technical PRD - Alert Services](../Project-Technical-Architecture.md#35-alert-delivery-services)
- [UX Design - Alerts](../mvp-ux-trendscope.md)
- [Master Concept - Tier Latency](../concept/master-concept.md)

---

## 12. Integration Points

| Stage | Integration |
|-------|-------------|
| Stage 01 | Uses user niche preferences |
| Stage 02 | Uses tier information from billing |
| Stage 04 | Receives detected trends |
| Stage 06 | Exposes alert metrics |

---

*Document Version: 1.0.0*
*Created: 2026-02-17*
*Status: Ready for Implementation*
