"""
Alert Pipeline Coordinator

Main orchestration service for the alert delivery pipeline.
Coordinates deduplication, routing, throttling, and delivery.

Flow:
1. Find users subscribed to trend's niche
2. Check deduplication (1-hour window)
3. Apply throttling (prevent fatigue)
4. Route by tier (latency batching)
5. Deliver via appropriate channels
6. Track engagement
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
import redis.asyncio as redis
import structlog

from alerts.models import (
    Alert,
    AlertChannel,
    AlertResult,
    AlertStatus,
    UserAlertConfig,
    TrendForAlert,
    Tier,
)
from alerts.config import settings
from alerts.tier_router import TierRouter, get_tier_router
from alerts.deduplication import DeduplicationService
from alerts.throttling import ThrottlingService
from alerts.slack_service import SlackService, get_slack_service
from alerts.email_service import EmailService, get_email_service
from alerts.digest_worker import DigestWorker
from alerts.engagement import EngagementTracker


logger = structlog.get_logger(__name__)


class AlertPipeline:
    """Orchestrates alert delivery pipeline.

    This is the main entry point for sending trend alerts.
    It coordinates all the alert services to deliver notifications
    based on user preferences and subscription tier.

    Example:
        pipeline = AlertPipeline(db, redis)

        trend = TrendForAlert(
            id=uuid.uuid4(),
            type="sound",
            name="Trending Sound",
            velocity_score=85,
            saturation_percent=25,
            video_count_current=1500,
            growth_rate=120.5
        )

        results = await pipeline.process_trend_alert(
            trend=trend,
            niche_id=niche_uuid
        )
    """

    def __init__(
        self,
        db_pool,
        redis_client: redis.Redis,
        slack_service: Optional[SlackService] = None,
        email_service: Optional[EmailService] = None,
        tier_router: Optional[TierRouter] = None
    ):
        """Initialize alert pipeline.

        Args:
            db_pool: Database connection pool (asyncpg)
            redis_client: Redis client for caching
            slack_service: Optional SlackService instance
            email_service: Optional EmailService instance
            tier_router: Optional TierRouter instance
        """
        self.db = db_pool
        self.redis = redis_client

        # Initialize services
        self.slack = slack_service or get_slack_service()
        self.email = email_service or get_email_service()
        self.router = tier_router or get_tier_router()
        self.dedup = DeduplicationService(redis_client)
        self.throttle = ThrottlingService(redis_client)
        self.digest = DigestWorker(redis_client, self.slack, self.email)
        self.engagement: Optional[EngagementTracker] = None  # Lazy init

    def _get_engagement_tracker(self) -> EngagementTracker:
        """Get or create engagement tracker."""
        if self.engagement is None:
            self.engagement = EngagementTracker(self.db)
        return self.engagement

    async def process_trend_alert(
        self,
        trend: TrendForAlert,
        niche_id: uuid.UUID
    ) -> List[AlertResult]:
        """Process alert for a detected trend.

        Main entry point for trend alerting. This method:
        1. Finds users subscribed to the trend's niche
        2. Applies deduplication and throttling
        3. Routes by tier
        4. Delivers or queues for digest
        5. Records engagement

        Args:
            trend: Trend data to alert on
            niche_id: Niche UUID

        Returns:
            List of AlertResult for each subscribed user
        """
        logger.info(
            "pipeline_processing_trend",
            trend_id=str(trend.id),
            trend_name=trend.name,
            niche_id=str(niche_id),
            velocity_score=trend.velocity_score
        )

        # Get subscribed users
        users = await self._get_subscribed_users(niche_id)

        if not users:
            logger.info(
                "pipeline_no_subscribers",
                niche_id=str(niche_id)
            )
            return []

        logger.info(
            "pipeline_found_subscribers",
            niche_id=str(niche_id),
            subscriber_count=len(users)
        )

        results = []

        for user in users:
            try:
                result = await self._process_user_alert(user, trend, niche_id)
                results.append(result)
            except Exception as e:
                logger.error(
                    "pipeline_user_alert_error",
                    user_id=str(user.user_id),
                    trend_id=str(trend.id),
                    error=str(e)
                )
                results.append(AlertResult(
                    sent=False,
                    skipped=True,
                    skip_reason=f"Processing error: {str(e)}"
                ))

        # Log summary
        sent_count = sum(1 for r in results if r.sent)
        queued_count = sum(1 for r in results if r.queued)
        skipped_count = sum(1 for r in results if r.skipped)

        logger.info(
            "pipeline_complete",
            trend_id=str(trend.id),
            total_users=len(users),
            sent=sent_count,
            queued=queued_count,
            skipped=skipped_count
        )

        return results

    async def _process_user_alert(
        self,
        user: UserAlertConfig,
        trend: TrendForAlert,
        niche_id: uuid.UUID
    ) -> AlertResult:
        """Process alert for a single user.

        Args:
            user: User alert configuration
            trend: Trend data
            niche_id: Niche UUID

        Returns:
            AlertResult with delivery status
        """
        user_id = user.user_id
        trend_id = trend.id

        # Check velocity threshold for user
        if trend.velocity_score < user.velocity_threshold:
            logger.debug(
                "pipeline_velocity_below_threshold",
                user_id=str(user_id),
                velocity_score=trend.velocity_score,
                threshold=user.velocity_threshold
            )
            return AlertResult(
                skipped=True,
                skip_reason="velocity_below_threshold"
            )

        # Check deduplication
        if await self.dedup.is_duplicate(user_id, trend_id):
            logger.debug(
                "pipeline_duplicate",
                user_id=str(user_id),
                trend_id=str(trend_id)
            )
            return AlertResult(
                skipped=True,
                skip_reason="duplicate"
            )

        # Check throttling
        if await self.throttle.should_throttle(user_id, niche_id, user.tier.value):
            logger.debug(
                "pipeline_throttled",
                user_id=str(user_id),
                niche_id=str(niche_id)
            )
            return AlertResult(
                skipped=True,
                skip_reason="throttled"
            )

        # Get routing decision based on tier
        routing = self.router.get_routing(user.tier.value)

        # Create alert record
        alert = await self._create_alert_record(user, trend)

        if not alert:
            return AlertResult(
                sent=False,
                error="Failed to create alert record"
            )

        # Route delivery
        if routing.is_immediate:
            # Real-time delivery
            success = await self._deliver_immediate(user, trend, alert.id)
            if success:
                await self.dedup.mark_sent(user_id, trend_id)
                await self.throttle.increment_counters(user_id, niche_id)
                return AlertResult(
                    alert_id=alert.id,
                    sent=True
                )
            else:
                return AlertResult(
                    alert_id=alert.id,
                    sent=False,
                    error="Delivery failed"
                )
        else:
            # Queue for digest
            queued = await self.digest.queue_alert(
                user_id=user_id,
                trend=trend,
                delay_seconds=routing.delay_seconds,
                niche_id=niche_id
            )

            if queued:
                await self.dedup.mark_sent(user_id, trend_id)
                return AlertResult(
                    alert_id=alert.id,
                    queued=True
                )
            else:
                return AlertResult(
                    alert_id=alert.id,
                    sent=False,
                    error="Failed to queue for digest"
                )

    async def _get_subscribed_users(
        self,
        niche_id: uuid.UUID
    ) -> List[UserAlertConfig]:
        """Get users subscribed to a niche with alerts enabled.

        Args:
            niche_id: Niche UUID

        Returns:
            List of UserAlertConfig objects
        """
        try:
            rows = await self.db.fetch("""
                SELECT
                    u.id as user_id,
                    u.email,
                    u.tier,
                    u.email_notifications,
                    un.niche_id,
                    un.alert_enabled,
                    un.velocity_threshold,
                    ai.id as integration_id,
                    ai.type as integration_type,
                    ai.config as integration_config
                FROM profiles u
                JOIN user_niches un ON u.id = un.user_id
                LEFT JOIN alert_integrations ai ON u.id = ai.user_id AND ai.is_active = true
                WHERE un.niche_id = $1
                AND un.alert_enabled = true
                AND u.status = 'active'
            """, niche_id)

            users = []
            for row in rows:
                users.append(UserAlertConfig(
                    user_id=row["user_id"],
                    email=row["email"],
                    tier=Tier(row["tier"]) if row["tier"] else Tier.FREE,
                    email_notifications=row["email_notifications"],
                    niche_id=row["niche_id"],
                    alert_enabled=row["alert_enabled"],
                    velocity_threshold=row["velocity_threshold"] or 50,
                    integration_id=row["integration_id"],
                    integration_type=row["integration_type"],
                    integration_config=row["integration_config"]
                ))

            return users

        except Exception as e:
            logger.error(
                "pipeline_get_users_failed",
                niche_id=str(niche_id),
                error=str(e)
            )
            return []

    async def _create_alert_record(
        self,
        user: UserAlertConfig,
        trend: TrendForAlert
    ) -> Optional[Alert]:
        """Create alert record in database.

        Args:
            user: User configuration
            trend: Trend data

        Returns:
            Created Alert or None
        """
        # Determine channel
        channel = AlertChannel.EMAIL
        if user.integration_type == "slack":
            channel = AlertChannel.SLACK
        elif user.integration_type == "webhook":
            channel = AlertChannel.WEBHOOK

        try:
            row = await self.db.fetchrow("""
                INSERT INTO alerts (
                    user_id,
                    trend_id,
                    channel,
                    status,
                    confidence_score,
                    created_at
                )
                VALUES ($1, $2, $3, 'pending', $4, NOW())
                RETURNING id, user_id, trend_id, channel, status, created_at
            """,
                user.user_id,
                trend.id,
                channel.value,
                trend.velocity_score / 100.0
            )

            if row:
                return Alert(
                    id=row["id"],
                    user_id=row["user_id"],
                    trend_id=row["trend_id"],
                    channel=AlertChannel(row["channel"]),
                    status=AlertStatus(row["status"]),
                    created_at=row["created_at"]
                )

            return None

        except Exception as e:
            logger.error(
                "pipeline_create_alert_failed",
                user_id=str(user.user_id),
                trend_id=str(trend.id),
                error=str(e)
            )
            return None

    async def _deliver_immediate(
        self,
        user: UserAlertConfig,
        trend: TrendForAlert,
        alert_id: uuid.UUID
    ) -> bool:
        """Deliver alert immediately (Enterprise tier).

        Args:
            user: User configuration
            trend: Trend data
            alert_id: Alert UUID for tracking

        Returns:
            True if delivered successfully
        """
        success = False

        # Try Slack if configured
        if (
            user.integration_type == "slack"
            and user.integration_config
        ):
            webhook_url = user.integration_config.get("webhook_url", "")
            if webhook_url:
                success = await self.slack.send_trend_alert(
                    webhook_url=webhook_url,
                    trend=trend,
                    format="detailed",
                    alert_id=alert_id
                )

        # Try webhook if configured
        elif (
            user.integration_type == "webhook"
            and user.integration_config
        ):
            webhook_url = user.integration_config.get("webhook_url", "")
            if webhook_url:
                success = await self._send_webhook(
                    webhook_url,
                    trend,
                    alert_id
                )

        # Fallback to email
        if not success and user.email_notifications:
            success = await self.email.send_trend_alert(
                to_email=user.email,
                trend=trend,
                alert_id=alert_id
            )

        # Update alert status
        if success:
            tracker = self._get_engagement_tracker()
            await tracker.record_sent(alert_id)

        return success

    async def _send_webhook(
        self,
        webhook_url: str,
        trend: TrendForAlert,
        alert_id: uuid.UUID
    ) -> bool:
        """Send alert to generic webhook.

        Args:
            webhook_url: Webhook URL
            trend: Trend data
            alert_id: Alert UUID

        Returns:
            True if sent successfully
        """
        import httpx

        payload = {
            "alert_id": str(alert_id),
            "trend": {
                "id": str(trend.id),
                "type": trend.type,
                "name": trend.name,
                "velocity_score": trend.velocity_score,
                "saturation_percent": trend.saturation_percent,
                "video_count": trend.video_count_current,
                "growth_rate": trend.growth_rate,
                "niche": trend.niche_name,
                "status": trend.status
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(webhook_url, json=payload)
                return response.status_code in (200, 201, 202, 204)

        except Exception as e:
            logger.error(
                "webhook_delivery_failed",
                alert_id=str(alert_id),
                error=str(e)
            )
            return False

    async def trigger_digest_processing(
        self,
        batch_type: str = "hourly"
    ) -> Dict[str, int]:
        """Manually trigger digest processing.

        Useful for testing or manual intervention.

        Args:
            batch_type: 'hourly' or 'daily'

        Returns:
            Dict with processing stats
        """
        if batch_type == "hourly":
            return await self.digest.process_hourly_digests()
        elif batch_type == "daily":
            return await self.digest.process_daily_digests()
        else:
            return {
                "error": f"Unknown batch type: {batch_type}",
                "users_processed": 0,
                "alerts_sent": 0
            }

    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get statistics about the pipeline.

        Returns:
            Dict with pipeline stats
        """
        dedup_stats = await self.dedup.get_stats()
        throttle_stats = await self.throttle.get_stats()
        digest_stats = await self.digest.get_queue_stats()

        return {
            "deduplication": dedup_stats,
            "throttling": throttle_stats,
            "digest": digest_stats,
            "timestamp": datetime.utcnow().isoformat()
        }


# Singleton instance
_alert_pipeline: AlertPipeline | None = None


def get_alert_pipeline(
    db_pool=None,
    redis_client: Optional[redis.Redis] = None
) -> AlertPipeline:
    """Get the singleton AlertPipeline instance.

    Args:
        db_pool: Database pool (required on first call)
        redis_client: Redis client (required on first call)

    Returns:
        AlertPipeline instance
    """
    global _alert_pipeline
    if _alert_pipeline is None:
        if db_pool is None or redis_client is None:
            raise ValueError("db_pool and redis_client required for first initialization")
        _alert_pipeline = AlertPipeline(db_pool, redis_client)
    return _alert_pipeline
