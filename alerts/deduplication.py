"""
Deduplication Service

Prevents duplicate alerts within time windows using Redis.
Ensures users don't receive repeated notifications for the same trend.

Default window: 1 hour
"""

from datetime import datetime
from typing import Optional
import uuid
import redis.asyncio as redis
import structlog

from alerts.config import settings


logger = structlog.get_logger(__name__)


class DeduplicationService:
    """Redis-based alert deduplication.

    Uses Redis keys with TTL to prevent duplicate alerts within
    a configurable time window (default: 1 hour).

    Key format: alert:dedup:{user_id}:{trend_id}

    Example:
        dedup = DeduplicationService(redis_client)

        # Check if alert was recently sent
        if await dedup.is_duplicate(user_id, trend_id):
            logger.info("alert_skipped_duplicate", user_id=user_id)
            return

        # Send alert...

        # Mark as sent
        await dedup.mark_sent(user_id, trend_id)
    """

    # Key prefix for deduplication keys
    KEY_PREFIX = "alert:dedup"

    # Default TTL from settings (1 hour)
    DEFAULT_TTL = 3600

    def __init__(
        self,
        redis_client: redis.Redis,
        ttl_seconds: Optional[int] = None
    ):
        """Initialize deduplication service.

        Args:
            redis_client: Redis client instance
            ttl_seconds: Custom TTL (default: from settings)
        """
        self.redis = redis_client
        self.ttl = ttl_seconds or settings.dedup_window_seconds

    def _make_key(self, user_id: uuid.UUID, trend_id: uuid.UUID) -> str:
        """Generate deduplication key.

        Args:
            user_id: User UUID
            trend_id: Trend UUID

        Returns:
            Redis key string
        """
        return f"{self.KEY_PREFIX}:{user_id}:{trend_id}"

    async def is_duplicate(
        self,
        user_id: uuid.UUID,
        trend_id: uuid.UUID
    ) -> bool:
        """Check if alert was recently sent for this user+trend.

        Args:
            user_id: User UUID
            trend_id: Trend UUID

        Returns:
            True if duplicate (alert already sent within window)
        """
        key = self._make_key(user_id, trend_id)
        exists = await self.redis.exists(key)

        if exists:
            logger.debug(
                "deduplication_hit",
                user_id=str(user_id),
                trend_id=str(trend_id),
                key=key
            )

        return exists > 0

    async def mark_sent(
        self,
        user_id: uuid.UUID,
        trend_id: uuid.UUID
    ) -> bool:
        """Mark alert as sent to prevent duplicates.

        Sets a key with TTL to track that this user+trend combination
        has been alerted within the deduplication window.

        Args:
            user_id: User UUID
            trend_id: Trend UUID

        Returns:
            True if successfully marked
        """
        key = self._make_key(user_id, trend_id)

        try:
            await self.redis.setex(key, self.ttl, datetime.utcnow().isoformat())

            logger.debug(
                "deduplication_marked",
                user_id=str(user_id),
                trend_id=str(trend_id),
                ttl_seconds=self.ttl
            )

            return True

        except redis.RedisError as e:
            logger.error(
                "deduplication_mark_failed",
                user_id=str(user_id),
                trend_id=str(trend_id),
                error=str(e)
            )
            return False

    async def get_sent_time(
        self,
        user_id: uuid.UUID,
        trend_id: uuid.UUID
    ) -> Optional[datetime]:
        """Get when alert was last sent for this user+trend.

        Args:
            user_id: User UUID
            trend_id: Trend UUID

        Returns:
            Datetime when marked, or None if not found
        """
        key = self._make_key(user_id, trend_id)
        value = await self.redis.get(key)

        if value:
            try:
                return datetime.fromisoformat(value.decode())
            except (ValueError, AttributeError):
                return None

        return None

    async def clear(
        self,
        user_id: uuid.UUID,
        trend_id: uuid.UUID
    ) -> bool:
        """Clear deduplication for a user+trend.

        Useful for testing or manual override.

        Args:
            user_id: User UUID
            trend_id: Trend UUID

        Returns:
            True if key was deleted
        """
        key = self._make_key(user_id, trend_id)
        deleted = await self.redis.delete(key)

        return deleted > 0

    async def clear_all_for_user(self, user_id: uuid.UUID) -> int:
        """Clear all deduplication keys for a user.

        Useful when user changes preferences or for testing.

        Args:
            user_id: User UUID

        Returns:
            Number of keys deleted
        """
        pattern = f"{self.KEY_PREFIX}:{user_id}:*"
        keys = []

        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            deleted = await self.redis.delete(*keys)
            logger.info(
                "deduplication_cleared_user",
                user_id=str(user_id),
                keys_deleted=deleted
            )
            return deleted

        return 0

    async def get_ttl_remaining(
        self,
        user_id: uuid.UUID,
        trend_id: uuid.UUID
    ) -> Optional[int]:
        """Get remaining TTL for a deduplication key.

        Args:
            user_id: User UUID
            trend_id: Trend UUID

        Returns:
            TTL in seconds, or None if key doesn't exist
        """
        key = self._make_key(user_id, trend_id)
        ttl = await self.redis.ttl(key)

        if ttl > 0:
            return ttl
        return None

    async def get_stats(self) -> dict:
        """Get deduplication statistics.

        Returns:
            Dict with stats (total keys, etc.)
        """
        pattern = f"{self.KEY_PREFIX}:*"
        count = 0

        async for _ in self.redis.scan_iter(match=pattern):
            count += 1

        return {
            "total_dedup_keys": count,
            "ttl_seconds": self.ttl
        }
