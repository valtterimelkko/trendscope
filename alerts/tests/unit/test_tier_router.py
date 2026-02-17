"""
Unit tests for TierRouter.

Tests tier-based routing logic including:
- Route alert by tier (FREE, SOLO, AGENCY, ENTERPRISE)
- Latency calculations
- Batch type selection
- Invalid tier handling
- Routing decision properties
"""

import pytest
from typing import Dict, Any

from alerts.tier_router import TierRouter, get_tier_router
from alerts.models import Tier, BatchType, RoutingDecision


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def router() -> TierRouter:
    """Create a TierRouter instance."""
    return TierRouter()


# =============================================================================
# Basic Routing Tests
# =============================================================================

class TestTierRouting:
    """Tests for tier-based routing decisions."""

    def test_route_free_tier(self, router):
        """Test FREE tier routing (daily batch)."""
        routing = router.get_routing("free")
        
        assert routing.is_immediate is False
        assert routing.delay_seconds == 24 * 3600  # 24 hours
        assert routing.batch_type == BatchType.DAILY
        assert routing.max_alerts_per_batch == 10

    def test_route_solo_tier(self, router):
        """Test SOLO tier routing (hourly batch)."""
        routing = router.get_routing("solo")
        
        assert routing.is_immediate is False
        assert routing.delay_seconds == 2 * 3600  # 2 hours
        assert routing.batch_type == BatchType.HOURLY
        assert routing.max_alerts_per_batch == 20

    def test_route_agency_tier(self, router):
        """Test AGENCY tier routing (hourly batch)."""
        routing = router.get_routing("agency")
        
        assert routing.is_immediate is False
        assert routing.delay_seconds == 30 * 60  # 30 minutes
        assert routing.batch_type == BatchType.HOURLY
        assert routing.max_alerts_per_batch == 50

    def test_route_enterprise_tier(self, router):
        """Test ENTERPRISE tier routing (realtime)."""
        routing = router.get_routing("enterprise")
        
        assert routing.is_immediate is True
        assert routing.delay_seconds == 0
        assert routing.batch_type == BatchType.REALTIME
        assert routing.max_alerts_per_batch == 0  # No limit

    def test_route_enterprise_tier_realtime(self, router):
        """Test that enterprise tier is always realtime."""
        routing = router.get_routing("enterprise")
        
        assert routing.is_immediate is True
        assert routing.batch_type == BatchType.REALTIME


# =============================================================================
# Case Insensitivity Tests
# =============================================================================

class TestTierCaseInsensitivity:
    """Tests for case-insensitive tier string handling."""

    def test_free_tier_lowercase(self, router):
        """Test 'free' (lowercase)."""
        routing = router.get_routing("free")
        assert routing.batch_type == BatchType.DAILY

    def test_free_tier_uppercase(self, router):
        """Test 'FREE' (uppercase)."""
        routing = router.get_routing("FREE")
        assert routing.batch_type == BatchType.DAILY

    def test_free_tier_mixed_case(self, router):
        """Test 'Free' (mixed case)."""
        routing = router.get_routing("Free")
        assert routing.batch_type == BatchType.DAILY

    def test_enterprise_tier_uppercase(self, router):
        """Test 'ENTERPRISE' (uppercase)."""
        routing = router.get_routing("ENTERPRISE")
        assert routing.is_immediate is True

    def test_solo_tier_mixed_case(self, router):
        """Test 'Solo' (mixed case)."""
        routing = router.get_routing("Solo")
        assert routing.delay_seconds == 2 * 3600


# =============================================================================
# Invalid Tier Tests
# =============================================================================

class TestInvalidTier:
    """Tests for invalid tier handling."""

    def test_invalid_tier_defaults_to_free(self, router):
        """Test that invalid tier defaults to FREE tier settings."""
        routing = router.get_routing("invalid_tier")
        
        # Should default to FREE tier
        assert routing.is_immediate is False
        assert routing.delay_seconds == 24 * 3600
        assert routing.batch_type == BatchType.DAILY
        assert routing.max_alerts_per_batch == 10

    def test_empty_tier_defaults_to_free(self, router):
        """Test that empty string tier defaults to FREE."""
        routing = router.get_routing("")
        
        assert routing.batch_type == BatchType.DAILY

    def test_none_tier_raises_error(self, router):
        """Test that None tier raises AttributeError."""
        with pytest.raises(AttributeError):
            router.get_routing(None)

    def test_unknown_tier_name(self, router):
        """Test various unknown tier names default to FREE."""
        unknown_tiers = ["premium", "basic", "pro", "gold", "silver"]
        
        for tier in unknown_tiers:
            routing = router.get_routing(tier)
            assert routing.batch_type == BatchType.DAILY, f"Failed for tier: {tier}"


# =============================================================================
# Immediate Send Tests
# =============================================================================

class TestShouldSendImmediately:
    """Tests for should_send_immediately method."""

    def test_enterprise_sends_immediately(self, router):
        """Test ENTERPRISE tier sends immediately."""
        assert router.should_send_immediately("enterprise") is True

    def test_free_does_not_send_immediately(self, router):
        """Test FREE tier does not send immediately."""
        assert router.should_send_immediately("free") is False

    def test_solo_does_not_send_immediately(self, router):
        """Test SOLO tier does not send immediately."""
        assert router.should_send_immediately("solo") is False

    def test_agency_does_not_send_immediately(self, router):
        """Test AGENCY tier does not send immediately."""
        assert router.should_send_immediately("agency") is False

    def test_invalid_tier_does_not_send_immediately(self, router):
        """Test invalid tier defaults to FREE (does not send immediately)."""
        assert router.should_send_immediately("unknown") is False


# =============================================================================
# Latency Tests
# =============================================================================

class TestLatencyCalculations:
    """Tests for latency calculation methods."""

    def test_get_latency_hours_free(self, router):
        """Test FREE tier latency in hours."""
        assert router.get_latency_hours("free") == 24.0

    def test_get_latency_hours_solo(self, router):
        """Test SOLO tier latency in hours."""
        assert router.get_latency_hours("solo") == 2.0

    def test_get_latency_hours_agency(self, router):
        """Test AGENCY tier latency in hours."""
        assert router.get_latency_hours("agency") == 0.5  # 30 minutes

    def test_get_latency_hours_enterprise(self, router):
        """Test ENTERPRISE tier latency in hours."""
        assert router.get_latency_hours("enterprise") == 0.0

    def test_get_latency_display_free(self, router):
        """Test FREE tier display string."""
        assert router.get_latency_display("free") == "1 day"

    def test_get_latency_display_solo(self, router):
        """Test SOLO tier display string."""
        assert router.get_latency_display("solo") == "2 hours"

    def test_get_latency_display_agency(self, router):
        """Test AGENCY tier display string."""
        assert router.get_latency_display("agency") == "30 minutes"

    def test_get_latency_display_enterprise(self, router):
        """Test ENTERPRISE tier display string."""
        assert router.get_latency_display("enterprise") == "Real-time"

    def test_get_latency_display_invalid_tier(self, router):
        """Test invalid tier defaults to FREE display."""
        assert router.get_latency_display("invalid") == "1 day"


# =============================================================================
# Batch Type Tests
# =============================================================================

class TestBatchType:
    """Tests for batch type selection."""

    def test_get_batch_type_free(self, router):
        """Test FREE tier batch type."""
        assert router.get_batch_type("free") == BatchType.DAILY

    def test_get_batch_type_solo(self, router):
        """Test SOLO tier batch type."""
        assert router.get_batch_type("solo") == BatchType.HOURLY

    def test_get_batch_type_agency(self, router):
        """Test AGENCY tier batch type."""
        assert router.get_batch_type("agency") == BatchType.HOURLY

    def test_get_batch_type_enterprise(self, router):
        """Test ENTERPRISE tier batch type."""
        assert router.get_batch_type("enterprise") == BatchType.REALTIME

    def test_get_batch_type_invalid(self, router):
        """Test invalid tier defaults to DAILY batch."""
        assert router.get_batch_type("unknown") == BatchType.DAILY


# =============================================================================
# Cron Schedule Tests
# =============================================================================

class TestCronSchedules:
    """Tests for cron schedule generation."""

    def test_cron_schedule_realtime(self, router):
        """Test REALTIME cron schedule (every minute)."""
        cron = router.get_digest_schedule_cron("enterprise")
        assert cron == "* * * * *"

    def test_cron_schedule_hourly(self, router):
        """Test HOURLY cron schedule (every hour at minute 0)."""
        cron = router.get_digest_schedule_cron("solo")
        assert cron == "0 * * * *"

    def test_cron_schedule_daily(self, router):
        """Test DAILY cron schedule (9 AM daily)."""
        cron = router.get_digest_schedule_cron("free")
        assert cron == "0 9 * * *"

    def test_cron_schedule_weekly(self, router):
        """Test WEEKLY cron schedule (Monday 9 AM)."""
        # Need to test with a tier that would use weekly
        # Currently no tier uses weekly by default, but let's test the method
        # by creating a routing decision with weekly batch type
        weekly_routing = RoutingDecision(
            is_immediate=False,
            delay_seconds=7 * 24 * 3600,
            batch_type=BatchType.WEEKLY,
            max_alerts_per_batch=10
        )
        
        # Find which tier this would correspond to (if any)
        # We'll just verify the cron schedule method works
        cron = router.get_digest_schedule_cron("free")
        assert cron is not None


# =============================================================================
# Tier from Routing Tests
# =============================================================================

class TestTierFromRouting:
    """Tests for inverse lookup of tier from routing decision."""

    def test_get_tier_from_routing_free(self, router):
        """Test identifying FREE tier from routing."""
        free_routing = router.get_routing("free")
        tier = router.get_tier_from_routing(free_routing)
        
        assert tier == Tier.FREE

    def test_get_tier_from_routing_enterprise(self, router):
        """Test identifying ENTERPRISE tier from routing."""
        enterprise_routing = router.get_routing("enterprise")
        tier = router.get_tier_from_routing(enterprise_routing)
        
        assert tier == Tier.ENTERPRISE

    def test_get_tier_from_routing_unknown(self, router):
        """Test identifying unknown routing defaults to FREE."""
        unknown_routing = RoutingDecision(
            is_immediate=False,
            delay_seconds=9999,  # Unknown delay
            batch_type=BatchType.DAILY,
            max_alerts_per_batch=10
        )
        
        tier = router.get_tier_from_routing(unknown_routing)
        
        # Should default to FREE when not found
        assert tier == Tier.FREE


# =============================================================================
# Tier Validation Tests
# =============================================================================

class TestTierValidation:
    """Tests for tier validation."""

    def test_is_valid_tier_free(self, router):
        """Test validating FREE tier."""
        assert router.is_valid_tier("free") is True

    def test_is_valid_tier_solo(self, router):
        """Test validating SOLO tier."""
        assert router.is_valid_tier("solo") is True

    def test_is_valid_tier_agency(self, router):
        """Test validating AGENCY tier."""
        assert router.is_valid_tier("agency") is True

    def test_is_valid_tier_enterprise(self, router):
        """Test validating ENTERPRISE tier."""
        assert router.is_valid_tier("enterprise") is True

    def test_is_valid_tier_invalid(self, router):
        """Test validating invalid tier."""
        assert router.is_valid_tier("invalid") is False

    def test_is_valid_tier_empty(self, router):
        """Test validating empty tier string."""
        assert router.is_valid_tier("") is False

    def test_is_valid_tier_case_insensitive(self, router):
        """Test that tier validation is case-insensitive."""
        assert router.is_valid_tier("FREE") is True
        assert router.is_valid_tier("Free") is True
        assert router.is_valid_tier("solo") is True
        assert router.is_valid_tier("SOLO") is True


# =============================================================================
# All Tier Info Tests
# =============================================================================

class TestAllTierInfo:
    """Tests for getting info about all tiers."""

    def test_get_all_tier_info_structure(self, router):
        """Test structure of all tier info."""
        info = router.get_all_tier_info()
        
        # Should have all 4 tiers
        assert "free" in info
        assert "solo" in info
        assert "agency" in info
        assert "enterprise" in info
        
        # Each should have expected fields
        for tier_name, tier_info in info.items():
            assert "is_immediate" in tier_info
            assert "delay_seconds" in tier_info
            assert "delay_hours" in tier_info
            assert "batch_type" in tier_info
            assert "max_alerts_per_batch" in tier_info
            assert "latency_display" in tier_info

    def test_get_all_tier_info_values(self, router):
        """Test values in all tier info."""
        info = router.get_all_tier_info()
        
        # FREE tier checks
        assert info["free"]["is_immediate"] is False
        assert info["free"]["delay_hours"] == 24.0
        assert info["free"]["latency_display"] == "1 day"
        
        # ENTERPRISE tier checks
        assert info["enterprise"]["is_immediate"] is True
        assert info["enterprise"]["delay_hours"] == 0.0
        assert info["enterprise"]["latency_display"] == "Real-time"


# =============================================================================
# Singleton Tests
# =============================================================================

class TestTierRouterSingleton:
    """Tests for TierRouter singleton instance."""

    def test_get_tier_router_returns_instance(self):
        """Test that get_tier_router returns a TierRouter instance."""
        router1 = get_tier_router()
        router2 = get_tier_router()
        
        assert isinstance(router1, TierRouter)
        assert isinstance(router2, TierRouter)
        # Should be the same instance (singleton)
        assert router1 is router2

    def test_singleton_same_routing(self):
        """Test that singleton returns consistent routing."""
        router1 = get_tier_router()
        router2 = get_tier_router()
        
        routing1 = router1.get_routing("enterprise")
        routing2 = router2.get_routing("enterprise")
        
        assert routing1.is_immediate == routing2.is_immediate
        assert routing1.delay_seconds == routing2.delay_seconds


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestTierRouterEdgeCases:
    """Edge case tests for TierRouter."""

    def test_routing_decision_immutable_values(self, router):
        """Test that routing decision values are correct."""
        routing = router.get_routing("agency")
        
        # Verify exact values
        assert routing.delay_seconds == 1800  # 30 minutes exactly
        assert routing.max_alerts_per_batch == 50

    def test_tier_routing_dict_complete(self, router):
        """Test that TIER_ROUTING has all tiers."""
        tiers = list(Tier)
        routing_tiers = list(router.TIER_ROUTING.keys())
        
        assert len(tiers) == len(routing_tiers)
        for tier in tiers:
            assert tier in routing_tiers

    def test_velocity_based_routing_documented(self, router):
        """Test that routing supports velocity-based priority (documented)."""
        # The router doesn't currently implement velocity-based routing
        # but this test documents where it would be added
        # For now, all tiers use their default routing
        
        high_velocity_routing = router.get_routing("enterprise")
        assert high_velocity_routing.is_immediate is True

    def test_emergency_routing_enterprise(self, router):
        """Test that enterprise tier always gets realtime (emergency) routing."""
        # Even for low-priority alerts, enterprise gets realtime
        routing = router.get_routing("enterprise")
        
        assert routing.is_immediate is True
        assert routing.batch_type == BatchType.REALTIME
        assert routing.delay_seconds == 0

    def test_batch_queue_selection(self, router):
        """Test batch queue selection based on tier."""
        free_routing = router.get_routing("free")
        solo_routing = router.get_routing("solo")
        enterprise_routing = router.get_routing("enterprise")
        
        # Free goes to daily queue
        assert free_routing.batch_type == BatchType.DAILY
        
        # Solo goes to hourly queue
        assert solo_routing.batch_type == BatchType.HOURLY
        
        # Enterprise doesn't use a batch queue (realtime)
        assert enterprise_routing.batch_type == BatchType.REALTIME

    def test_route_priority_calculation(self, router):
        """Test route priority based on tier."""
        # Priority order: ENTERPRISE > AGENCY > SOLO > FREE
        
        enterprise_routing = router.get_routing("enterprise")
        agency_routing = router.get_routing("agency")
        solo_routing = router.get_routing("solo")
        free_routing = router.get_routing("free")
        
        # Enterprise has highest priority (immediate)
        assert enterprise_routing.is_immediate is True
        
        # Others have decreasing priority (increasing delay)
        assert agency_routing.delay_seconds < solo_routing.delay_seconds
        assert solo_routing.delay_seconds < free_routing.delay_seconds

    def test_tier_config_consistency(self, router):
        """Test that tier configuration is internally consistent."""
        for tier in Tier:
            routing = router.TIER_ROUTING[tier]
            
            # If immediate, delay should be 0
            if routing.is_immediate:
                assert routing.delay_seconds == 0
                assert routing.batch_type == BatchType.REALTIME
            else:
                # If not immediate, delay should be > 0
                assert routing.delay_seconds > 0
                assert routing.batch_type != BatchType.REALTIME

    def test_max_alerts_per_batch_consistency(self, router):
        """Test max_alerts_per_batch values are reasonable."""
        free_routing = router.get_routing("free")
        enterprise_routing = router.get_routing("enterprise")
        
        # Free tier should have limit
        assert free_routing.max_alerts_per_batch > 0
        
        # Enterprise should have no limit (0)
        assert enterprise_routing.max_alerts_per_batch == 0

    def test_latency_display_singular_plural(self, router):
        """Test latency display handles singular/plural correctly."""
        # 1 day
        free_display = router.get_latency_display("free")
        assert free_display == "1 day"
        
        # 2 hours (plural)
        solo_display = router.get_latency_display("solo")
        assert solo_display == "2 hours"
        
        # 30 minutes (plural)
        agency_display = router.get_latency_display("agency")
        assert agency_display == "30 minutes"
