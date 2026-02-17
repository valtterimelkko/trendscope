"""
Digest Worker

Background worker for processing batched alert digests.
Queues alerts for non-realtime tiers and processes them on schedule.

Digest Schedules:
- Hourly: Solo and Agency tiers
- Daily: Free tier
- Weekly: Free tier fallback
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import uuid
import redis.asyncio as redis
import structlog

from alerts.models import DigestEntry, TrendForAlert, UserAlertConfig, BatchType
from alerts.config import settings
from alerts.slack_service import SlackService, get_slack_service
from alerts.email_service import EmailService, get_email_service


logger = structlog.get_logger(__name__)


class DigestWorker:
    """Processes batched alerts for non-realtime tiers.

    This worker handles alert batching for tiers that don't get
    real-time delivery:
    - Free tier: Daily digest
    - Solo tier: Hourly digest (2-hour latency)
    - Agency tier: Hourly digest (30-minute latency)

    Alerts are queued in Redis and processed by the appropriate
    digest schedule.

    Example:
        worker = DigestWorker(redis_client, db)

        # Queue an alert
        await worker.queue_alert(
            user_id=user.id,
            trend=trend,
            delay_seconds=7200  # 2 hours
        )

        # Process hourly digests (run by cron/scheduler)
        await worker.process_hourly_digests()
    """

    # Redis key prefixes
    QUEUE_PREFIX = "digest:queue"
    USER_QUEUE_PREFIX = "digest:user"

    def __init__(
        self,
        redis_client: redis.Redis,
        slack_service: Optional[SlackService] = None,
        email_service: Optional[EmailService] = None
    ):
        """Initialize digest worker.

        Args:
            redis_client: Redis client for queue storage
            slack_service: Optional SlackService instance
            email_service: Optional EmailService instance
        """
        self.redis = redis_client
        self.slack = slack_service or get_slack_service()
        self.email = email_service or get_email_service()

    def _user_queue_key(self, user_id: uuid.UUID) -> str:
        """Get Redis key for user's digest queue."""
        return f"{self.USER_QUEUE_PREFIX}:{user_id}"

    async def queue_alert(
        self,
        user_id: uuid.UUID,
        trend: TrendForAlert,
        delay_seconds: int,
        niche_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Queue an alert for batched delivery.

        Args:
            user_id: User UUID
            trend: Trend data to queue
            delay_seconds: Delay before delivery (determines batch)
            niche_id: Optional niche UUID for grouping

        Returns:
            True if queued successfully
        """
        entry = DigestEntry(
            trend_id=str(trend.id),
            trend_name=trend.name,
            velocity_score=trend.velocity_score,
            saturation_percent=trend.saturation_percent,
            growth_rate=trend.growth_rate,
            niche_name=trend.niche_name,
            queued_at=datetime.utcnow(),
            niche_id=str(niche_id) if niche_id else None
        )

        queue_key = self._user_queue_key(user_id)

        try:
            # Push to user's queue
            await self.redis.rpush(
                queue_key,
                entry.model_dump_json()
            )

            # Set TTL for queue cleanup
            await self.redis.expire(queue_key, settings.digest_queue_ttl_seconds)

            logger.debug(
                "digest_alert_queued",
                user_id=str(user_id),
                trend_id=str(trend.id),
                trend_name=trend.name,
                delay_seconds=delay_seconds
            )

            return True

        except redis.RedisError as e:
            logger.error(
                "digest_queue_failed",
                user_id=str(user_id),
                trend_id=str(trend.id),
                error=str(e)
            )
            return False

    async def get_user_queue(
        self,
        user_id: uuid.UUID,
        limit: int = 100
    ) -> List[DigestEntry]:
        """Get queued alerts for a user.

        Args:
            user_id: User UUID
            limit: Maximum entries to return

        Returns:
            List of DigestEntry objects
        """
        queue_key = self._user_queue_key(user_id)

        try:
            entries = await self.redis.lrange(queue_key, 0, limit - 1)

            result = []
            for entry_data in entries:
                try:
                    entry_dict = json.loads(entry_data)
                    result.append(DigestEntry(**entry_dict))
                except (json.JSONDecodeError, TypeError):
                    continue

            return result

        except redis.RedisError as e:
            logger.error(
                "digest_get_queue_failed",
                user_id=str(user_id),
                error=str(e)
            )
            return []

    async def clear_user_queue(self, user_id: uuid.UUID) -> int:
        """Clear all queued alerts for a user.

        Called after digest is sent.

        Args:
            user_id: User UUID

        Returns:
            Number of entries cleared
        """
        queue_key = self._user_queue_key(user_id)

        try:
            # Get count before deleting
            count = await self.redis.llen(queue_key)
            await self.redis.delete(queue_key)

            logger.info(
                "digest_queue_cleared",
                user_id=str(user_id),
                entries_cleared=count
            )

            return count

        except redis.RedisError as e:
            logger.error(
                "digest_clear_queue_failed",
                user_id=str(user_id),
                error=str(e)
            )
            return 0

    async def process_hourly_digests(self) -> Dict[str, int]:
        """Process all hourly digests.

        This should be called by a scheduler every hour.
        It processes users with pending hourly digests (Solo, Agency tiers).

        Returns:
            Dict with processing stats
        """
        logger.info("digest_processing_hourly_start")

        stats = {
            "users_processed": 0,
            "alerts_sent": 0,
            "errors": 0
        }

        # Find users with pending hourly digests
        # In production, this would query the database for users
        # with tier='solo' or tier='agency' and pending alerts

        # For now, scan Redis for user queues
        pattern = f"{self.USER_QUEUE_PREFIX}:*"
        user_ids = set()

        async for key in self.redis.scan_iter(match=pattern):
            # Extract user_id from key
            key_str = key.decode() if isinstance(key, bytes) else key
            parts = key_str.split(":")
            if len(parts) >= 3:
                user_ids.add(parts[2])

        for user_id_str in user_ids:
            try:
                user_id = uuid.UUID(user_id_str)
                sent = await self._process_user_digest(
                    user_id,
                    BatchType.HOURLY
                )
                if sent > 0:
                    stats["users_processed"] += 1
                    stats["alerts_sent"] += sent

            except ValueError:
                continue
            except Exception as e:
                logger.error(
                    "digest_user_processing_error",
                    user_id=user_id_str,
                    error=str(e)
                )
                stats["errors"] += 1

        logger.info(
            "digest_processing_hourly_complete",
            **stats
        )

        return stats

    async def process_daily_digests(self) -> Dict[str, int]:
        """Process all daily digests.

        This should be called by a scheduler once per day.
        It processes users with pending daily digests (Free tier).

        Returns:
            Dict with processing stats
        """
        logger.info("digest_processing_daily_start")

        stats = {
            "users_processed": 0,
            "alerts_sent": 0,
            "errors": 0
        }

        # Find users with pending daily digests
        pattern = f"{self.USER_QUEUE_PREFIX}:*"
        user_ids = set()

        async for key in self.redis.scan_iter(match=pattern):
            key_str = key.decode() if isinstance(key, bytes) else key
            parts = key_str.split(":")
            if len(parts) >= 3:
                user_ids.add(parts[2])

        for user_id_str in user_ids:
            try:
                user_id = uuid.UUID(user_id_str)
                sent = await self._process_user_digest(
                    user_id,
                    BatchType.DAILY
                )
                if sent > 0:
                    stats["users_processed"] += 1
                    stats["alerts_sent"] += sent

            except ValueError:
                continue
            except Exception as e:
                logger.error(
                    "digest_user_processing_error",
                    user_id=user_id_str,
                    error=str(e)
                )
                stats["errors"] += 1

        logger.info(
            "digest_processing_daily_complete",
            **stats
        )

        return stats

    async def _process_user_digest(
        self,
        user_id: uuid.UUID,
        batch_type: BatchType,
        user_config: Optional[UserAlertConfig] = None
    ) -> int:
        """Process digest for a single user.

        Args:
            user_id: User UUID
            batch_type: Type of digest to process
            user_config: Optional user config (would be fetched from DB in production)

        Returns:
            Number of alerts sent
        """
        queue = await self.get_user_queue(user_id)

        if not queue:
            return 0

        # Convert queue entries to TrendForAlert format
        trends = []
        for entry in queue:
            trends.append(TrendForAlert(
                id=uuid.UUID(entry.trend_id),
                type="sound",  # Default, would be stored in entry
                name=entry.trend_name,
                velocity_score=entry.velocity_score,
                saturation_percent=entry.saturation_percent,
                video_count_current=0,  # Not stored in queue
                growth_rate=entry.growth_rate,
                niche_name=entry.niche_name,
                window_hours="6-8"
            ))

        # Determine delivery channel based on config
        # In production, fetch user preferences from database
        sent_count = 0

        # Try Slack first if configured
        if user_config and user_config.integration_type == "slack":
            webhook_url = user_config.integration_config.get("webhook_url", "")
            if webhook_url:
                success = await self.slack.send_digest(
                    webhook_url,
                    trends,
                    batch_type.value
                )
                if success:
                    sent_count = len(trends)

        # Fallback to email
        if sent_count == 0 and user_config and user_config.email_notifications:
            success = await self.email.send_digest(
                user_config.email,
                trends,
                batch_type.value
            )
            if success:
                sent_count = len(trends)

        # Clear queue after sending
        if sent_count > 0:
            await self.clear_user_queue(user_id)

        logger.info(
            "digest_user_processed",
            user_id=str(user_id),
            batch_type=batch_type.value,
            alerts_sent=sent_count
        )

        return sent_count

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics about digest queues.

        Returns:
            Dict with queue stats
        """
        pattern = f"{self.USER_QUEUE_PREFIX}:*"
        user_queues = 0
        total_entries = 0

        async for key in self.redis.scan_iter(match=pattern):
            user_queues += 1
            queue_len = await self.redis.llen(key)
            total_entries += queue_len

        return {
            "user_queues": user_queues,
            "total_queued_alerts": total_entries,
            "avg_queue_size": total_entries / user_queues if user_queues > 0 else 0
        }

    async def cleanup_stale_queues(
        self,
        max_age_hours: int = 72
    ) -> int:
        """Remove stale queues that haven't been processed.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of queues removed
        """
        pattern = f"{self.USER_QUEUE_PREFIX}:*"
        removed = 0
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

        async for key in self.redis.scan_iter(match=pattern):
            # Check if queue has any entries
            entries = await self.redis.lrange(key, 0, 0)

            if entries:
                try:
                    entry_dict = json.loads(entries[0])
                    queued_at = datetime.fromisoformat(entry_dict.get("queued_at", ""))

                    if queued_at < cutoff:
                        await self.redis.delete(key)
                        removed += 1

                except (json.JSONDecodeError, ValueError, TypeError):
                    # Invalid entry, remove the queue
                    await self.redis.delete(key)
                    removed += 1

        if removed > 0:
            logger.info(
                "digest_cleanup",
                queues_removed=removed
            )

        return removed


# Singleton instance
_digest_worker: DigestWorker | None = None


def get_digest_worker(redis_client: Optional[redis.Redis] = None) -> DigestWorker:
    """Get the singleton DigestWorker instance.

    Args:
        redis_client: Optional Redis client (required on first call)

    Returns:
        DigestWorker instance
    """
    global _digest_worker
    if _digest_worker is None:
        if redis_client is None:
            raise ValueError("Redis client required for first initialization")
        _digest_worker = DigestWorker(redis_client)
    return _digest_worker
