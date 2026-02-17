"""
Throttling Service

Prevents alert fatigue by limiting frequency of alerts.
Implements per-hour and per-niche-per-day limits based on tier.
"""

from typing import Optional, Dict
import uuid
import redis.asyncio as redis
import structlog

from alerts.config import settings
from alerts.models import Tier


logger = structlog.get_logger(__name__)


class ThrottlingService:
    """Alert throttling to prevent fatigue.

    Implements two types of limits:
    1. Per-hour limit: Maximum alerts per hour by tier
    2. Per-niche per-day limit: Maximum alerts per niche per day

    Throttle Limits by Tier:
    - Free: 5 alerts/hour, 3 per niche per day
    - Solo: 15 alerts/hour, 3 per niche per day
    - Agency: 30 alerts/hour, 3 per niche per day
    - Enterprise: 100 alerts/hour, 3 per niche per day

    Example:
        throttle = ThrottlingService(redis_client)

        # Check if user should be throttled
        if await throttle.should_throttle(user_id, niche_id, tier):
            logger.info("alert_throttled", user_id=user_id)
            return

        # Send alert...

        # Increment counters
        await throttle.increment_counters(user_id, niche_id)
    """

    # Key prefixes
    HOURLY_KEY_PREFIX = "alert:throttle:hourly"
    NICHE_DAILY_KEY_PREFIX = "alert:throttle:niche"

    # TTL constants
    HOUR_TTL = 3600  # 1 hour
    DAY_TTL = 86400  # 24 hours

    def __init__(
        self,
        redis_client: redis.Redis,
        custom_limits: Optional[Dict[str, int]] = None
    ):
        """Initialize throttling service.

        Args:
            redis_client: Redis client instance
            custom_limits: Optional custom hourly limits by tier
        """
        self.redis = redis_client
        self.hourly_limits = custom_limits or settings.throttle_max_alerts_per_hour
        self.daily_niche_limit = settings.throttle_max_alerts_per_day_per_niche

    def _hourly_key(self, user_id: uuid.UUID) -> str:
        """Generate hourly throttle key."""
        return f"{self.HOURLY_KEY_PREFIX}:{user_id}"

    def _niche_daily_key(self, user_id: uuid.UUID, niche_id: uuid.UUID) -> str:
        """Generate per-niche daily throttle key."""
        return f"{self.NICHE_DAILY_KEY_PREFIX}:{user_id}:{niche_id}:daily"

    async def should_throttle(
        self,
        user_id: uuid.UUID,
        niche_id: uuid.UUID,
        tier: str
    ) -> bool:
        """Check if user should be throttled.

        Checks both hourly limit and per-niche daily limit.

        Args:
            user_id: User UUID
            niche_id: Niche UUID
            tier: User tier

        Returns:
            True if should be throttled
        """
        # Check hourly limit
        hourly_count = await self.get_hourly_count(user_id)
        hourly_limit = self.get_hourly_limit(tier)

        if hourly_count >= hourly_limit:
            logger.info(
                "throttle_hourly_limit_reached",
                user_id=str(user_id),
                hourly_count=hourly_count,
                hourly_limit=hourly_limit
            )
            return True

        # Check per-niche daily limit
        niche_count = await self.get_niche_daily_count(user_id, niche_id)

        if niche_count >= self.daily_niche_limit:
            logger.info(
                "throttle_niche_daily_limit_reached",
                user_id=str(user_id),
                niche_id=str(niche_id),
                niche_count=niche_count,
                niche_limit=self.daily_niche_limit
            )
            return True

        return False

    def get_hourly_limit(self, tier: str) -> int:
        """Get hourly alert limit for a tier.

        Args:
            tier: User tier

        Returns:
            Maximum alerts per hour
        """
        tier_lower = tier.lower()
        return self.hourly_limits.get(tier_lower, self.hourly_limits["free"])

    async def get_hourly_count(self, user_id: uuid.UUID) -> int:
        """Get current hourly alert count for user.

        Args:
            user_id: User UUID

        Returns:
            Current count (0 if not set)
        """
        key = self._hourly_key(user_id)
        value = await self.redis.get(key)

        if value:
            try:
                return int(value)
            except ValueError:
                return 0

        return 0

    async def get_niche_daily_count(
        self,
        user_id: uuid.UUID,
        niche_id: uuid.UUID
    ) -> int:
        """Get current daily alert count for user+niche.

        Args:
            user_id: User UUID
            niche_id: Niche UUID

        Returns:
            Current count (0 if not set)
        """
        key = self._niche_daily_key(user_id, niche_id)
        value = await self.redis.get(key)

        if value:
            try:
                return int(value)
            except ValueError:
                return 0

        return 0

    async def increment_counters(
        self,
        user_id: uuid.UUID,
        niche_id: uuid.UUID
    ) -> bool:
        """Increment throttle counters after sending alert.

        Increments both hourly and per-niche daily counters.

        Args:
            user_id: User UUID
            niche_id: Niche UUID

        Returns:
            True if successful
        """
        hourly_key = self._hourly_key(user_id)
        niche_key = self._niche_daily_key(user_id, niche_id)

        try:
            # Use pipeline for atomic operations
            pipe = self.redis.pipeline()

            # Increment hourly counter
            pipe.incr(hourly_key)
            pipe.expire(hourly_key, self.HOUR_TTL)

            # Increment niche daily counter
            pipe.incr(niche_key)
            pipe.expire(niche_key, self.DAY_TTL)

            results = await pipe.execute()

            logger.debug(
                "throttle_counters_incremented",
                user_id=str(user_id),
                niche_id=str(niche_id),
                hourly_count=results[0],
                niche_daily_count=results[2]
            )

            return True

        except redis.RedisError as e:
            logger.error(
                "throttle_increment_failed",
                user_id=str(user_id),
                niche_id=str(niche_id),
                error=str(e)
            )
            return False

    async def reset_hourly(self, user_id: uuid.UUID) -> bool:
        """Reset hourly counter for a user.

        Useful for testing or manual override.

        Args:
            user_id: User UUID

        Returns:
            True if key was deleted
        """
        key = self._hourly_key(user_id)
        deleted = await self.redis.delete(key)

        return deleted > 0

    async def reset_niche_daily(
        self,
        user_id: uuid.UUID,
        niche_id: uuid.UUID
    ) -> bool:
        """Reset daily niche counter.

        Args:
            user_id: User UUID
            niche_id: Niche UUID

        Returns:
            True if key was deleted
        """
        key = self._niche_daily_key(user_id, niche_id)
        deleted = await self.redis.delete(key)

        return deleted > 0

    async def reset_all_for_user(self, user_id: uuid.UUID) -> int:
        """Reset all throttle counters for a user.

        Args:
            user_id: User UUID

        Returns:
            Number of keys deleted
        """
        patterns = [
            f"{self.HOURLY_KEY_PREFIX}:{user_id}",
            f"{self.NICHE_DAILY_KEY_PREFIX}:{user_id}:*"
        ]

        deleted_total = 0

        for pattern in patterns:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                deleted_total += await self.redis.delete(*keys)

        if deleted_total > 0:
            logger.info(
                "throttle_reset_user",
                user_id=str(user_id),
                keys_deleted=deleted_total
            )

        return deleted_total

    async def get_throttle_status(
        self,
        user_id: uuid.UUID,
        niche_id: uuid.UUID,
        tier: str
    ) -> Dict:
        """Get current throttle status for a user+niche.

        Useful for debugging and UI display.

        Args:
            user_id: User UUID
            niche_id: Niche UUID
            tier: User tier

        Returns:
            Dict with throttle status information
        """
        hourly_count = await self.get_hourly_count(user_id)
        hourly_limit = self.get_hourly_limit(tier)
        niche_count = await self.get_niche_daily_count(user_id, niche_id)

        return {
            "user_id": str(user_id),
            "niche_id": str(niche_id),
            "tier": tier,
            "hourly": {
                "count": hourly_count,
                "limit": hourly_limit,
                "remaining": max(0, hourly_limit - hourly_count),
                "is_limited": hourly_count >= hourly_limit
            },
            "niche_daily": {
                "count": niche_count,
                "limit": self.daily_niche_limit,
                "remaining": max(0, self.daily_niche_limit - niche_count),
                "is_limited": niche_count >= self.daily_niche_limit
            },
            "is_throttled": await self.should_throttle(user_id, niche_id, tier)
        }

    async def get_stats(self) -> dict:
        """Get throttling statistics.

        Returns:
            Dict with stats
        """
        hourly_pattern = f"{self.HOURLY_KEY_PREFIX}:*"
        niche_pattern = f"{self.NICHE_DAILY_KEY_PREFIX}:*"

        hourly_count = 0
        niche_count = 0

        async for _ in self.redis.scan_iter(match=hourly_pattern):
            hourly_count += 1

        async for _ in self.redis.scan_iter(match=niche_pattern):
            niche_count += 1

        return {
            "hourly_keys": hourly_count,
            "niche_daily_keys": niche_count,
            "limits": {
                "hourly": self.hourly_limits,
                "daily_niche": self.daily_niche_limit
            }
        }
