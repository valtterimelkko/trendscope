"""
Tier-Based Latency Router

Routes alerts based on subscription tier.
Determines delivery latency and batching strategy.

Tier Latency Configuration:
- Free: 24 hours (daily digest)
- Solo: 2 hours
- Agency: 30 minutes
- Enterprise: Real-time (0 latency)
"""

from typing import Dict
from alerts.models import Tier, RoutingDecision, BatchType
from alerts.config import settings


class TierRouter:
    """Determines alert routing based on subscription tier.

    This class encapsulates the tier-based latency logic,
    mapping user tiers to delivery parameters.

    The routing decision affects:
    - Whether to send immediately or batch
    - How long to delay before sending
    - What type of digest to use
    - Maximum alerts per batch

    Example:
        router = TierRouter()
        routing = router.get_routing("enterprise")
        if routing.is_immediate:
            await send_immediately(alert)
        else:
            await queue_for_digest(alert, routing.delay_seconds)
    """

    # Tier routing configuration
    # Matches frontend/lib/billing/feature-gates.ts TIER_LIMITS
    TIER_ROUTING: Dict[Tier, RoutingDecision] = {
        Tier.FREE: RoutingDecision(
            is_immediate=False,
            delay_seconds=24 * 3600,  # 24 hours (daily digest)
            batch_type=BatchType.DAILY,
            max_alerts_per_batch=10
        ),
        Tier.SOLO: RoutingDecision(
            is_immediate=False,
            delay_seconds=2 * 3600,  # 2 hours
            batch_type=BatchType.HOURLY,
            max_alerts_per_batch=20
        ),
        Tier.AGENCY: RoutingDecision(
            is_immediate=False,
            delay_seconds=30 * 60,  # 30 minutes
            batch_type=BatchType.HOURLY,
            max_alerts_per_batch=50
        ),
        Tier.ENTERPRISE: RoutingDecision(
            is_immediate=True,
            delay_seconds=0,  # Real-time
            batch_type=BatchType.REALTIME,
            max_alerts_per_batch=0  # No limit
        )
    }

    def get_routing(self, tier: str) -> RoutingDecision:
        """Get routing decision for a tier.

        Args:
            tier: User tier as string (free, solo, agency, enterprise)

        Returns:
            RoutingDecision with delivery parameters

        Example:
            >>> router = TierRouter()
            >>> routing = router.get_routing("solo")
            >>> routing.delay_seconds
            7200  # 2 hours
        """
        try:
            tier_enum = Tier(tier.lower())
            return self.TIER_ROUTING[tier_enum]
        except ValueError:
            # Default to free tier for unknown tiers
            return self.TIER_ROUTING[Tier.FREE]

    def should_send_immediately(self, tier: str) -> bool:
        """Check if alerts should be sent immediately for this tier.

        Args:
            tier: User tier

        Returns:
            True if alerts should be sent immediately
        """
        routing = self.get_routing(tier)
        return routing.is_immediate

    def get_latency_hours(self, tier: str) -> float:
        """Get latency in hours for a tier.

        Useful for display purposes.

        Args:
            tier: User tier

        Returns:
            Latency in hours (0 for real-time)
        """
        routing = self.get_routing(tier)
        return routing.delay_seconds / 3600

    def get_latency_display(self, tier: str) -> str:
        """Get human-readable latency string for a tier.

        Args:
            tier: User tier

        Returns:
            Human-readable latency string
        """
        routing = self.get_routing(tier)

        if routing.is_immediate:
            return "Real-time"

        hours = routing.delay_seconds / 3600

        if hours >= 24:
            days = int(hours / 24)
            return f"{days} day{'s' if days > 1 else ''}"
        elif hours >= 1:
            return f"{int(hours)} hour{'s' if hours > 1 else ''}"
        else:
            minutes = int(routing.delay_seconds / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''}"

    def get_batch_type(self, tier: str) -> BatchType:
        """Get batch type for a tier.

        Args:
            tier: User tier

        Returns:
            BatchType enum value
        """
        routing = self.get_routing(tier)
        return routing.batch_type

    def get_digest_schedule_cron(self, tier: str) -> str:
        """Get cron expression for digest schedule.

        Used by the digest worker to determine when to process batches.

        Args:
            tier: User tier

        Returns:
            Cron expression string
        """
        batch_type = self.get_batch_type(tier)

        cron_schedules = {
            BatchType.REALTIME: "* * * * *",  # Every minute (not used)
            BatchType.HOURLY: "0 * * * *",    # Every hour at minute 0
            BatchType.DAILY: "0 9 * * *",     # Every day at 9 AM
            BatchType.WEEKLY: "0 9 * * 1",    # Every Monday at 9 AM
        }

        return cron_schedules.get(batch_type, cron_schedules[BatchType.DAILY])

    def get_tier_from_routing(self, routing: RoutingDecision) -> Tier:
        """Get tier from routing decision (inverse lookup).

        Args:
            routing: Routing decision

        Returns:
            Corresponding Tier enum value
        """
        for tier, tier_routing in self.TIER_ROUTING.items():
            if (
                tier_routing.is_immediate == routing.is_immediate
                and tier_routing.delay_seconds == routing.delay_seconds
            ):
                return tier

        return Tier.FREE

    def is_valid_tier(self, tier: str) -> bool:
        """Check if a tier string is valid.

        Args:
            tier: Tier string to validate

        Returns:
            True if valid tier
        """
        try:
            Tier(tier.lower())
            return True
        except ValueError:
            return False

    def get_all_tier_info(self) -> Dict[str, Dict]:
        """Get routing info for all tiers.

        Useful for documentation/debugging.

        Returns:
            Dict mapping tier names to their routing info
        """
        result = {}
        for tier, routing in self.TIER_ROUTING.items():
            result[tier.value] = {
                "is_immediate": routing.is_immediate,
                "delay_seconds": routing.delay_seconds,
                "delay_hours": routing.delay_seconds / 3600,
                "batch_type": routing.batch_type.value,
                "max_alerts_per_batch": routing.max_alerts_per_batch,
                "latency_display": self.get_latency_display(tier.value),
            }
        return result


# Singleton instance for convenience
_router: TierRouter | None = None


def get_tier_router() -> TierRouter:
    """Get the singleton TierRouter instance.

    Returns:
        TierRouter instance
    """
    global _router
    if _router is None:
        _router = TierRouter()
    return _router
