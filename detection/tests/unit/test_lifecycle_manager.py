"""
Unit Tests for Lifecycle Manager

Tests state transitions, expiration logic, and lifecycle management.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from detection.lifecycle_manager import (
    LifecycleManager,
    LifecycleTransition
)
from detection.velocity_engine import VelocityResult
from detection.saturation import SaturationResult, SaturationEngine
from detection.models import TrendStatus


class TestLifecycleManager:
    """Test suite for LifecycleManager class."""

    @pytest.fixture
    def manager(self):
        """Create a LifecycleManager instance."""
        return LifecycleManager()

    @pytest.fixture
    def high_velocity_decelerating(self):
        """Create velocity result with high velocity and deceleration."""
        return VelocityResult(
            score=85,
            growth_rate=20.0,
            doubling_time=3.5,
            r_squared=0.95,
            is_exponential=True,
            acceleration=-0.05,  # Decelerating
            confidence=0.9,
            data_points=30,
            time_window_hours=48.0
        )

    @pytest.fixture
    def high_velocity_accelerating(self):
        """Create velocity result with high velocity and acceleration."""
        return VelocityResult(
            score=85,
            growth_rate=20.0,
            doubling_time=3.5,
            r_squared=0.95,
            is_exponential=True,
            acceleration=0.1,  # Accelerating
            confidence=0.9,
            data_points=30,
            time_window_hours=48.0
        )

    @pytest.fixture
    def low_velocity(self):
        """Create velocity result with low velocity."""
        return VelocityResult(
            score=15,
            growth_rate=2.0,
            doubling_time=35.0,
            r_squared=0.50,
            is_exponential=False,
            acceleration=-0.02,
            confidence=0.5,
            data_points=10,
            time_window_hours=12.0
        )

    @pytest.fixture
    def high_saturation(self):
        """Create saturation result with high saturation."""
        return SaturationResult(
            score=80,
            stage="mature",
            recommendation="Late stage - limited opportunity"
        )

    @pytest.fixture
    def very_high_saturation(self):
        """Create saturation result with very high saturation."""
        return SaturationResult(
            score=95,
            stage="decline",
            recommendation="Saturated - limited returns"
        )

    @pytest.fixture
    def low_saturation(self):
        """Create saturation result with low saturation."""
        return SaturationResult(
            score=20,
            stage="early",
            recommendation="Good opportunity - jump on this trend now"
        )

    @pytest.fixture
    def moderate_saturation(self):
        """Create saturation result with moderate saturation."""
        return SaturationResult(
            score=50,
            stage="growth",
            recommendation="Strong opportunity - still growing"
        )

    # =========================================================================
    # State Transition: EMERGING → PEAKING
    # =========================================================================

    def test_emerging_to_peaking_transition(self, manager, 
                                             high_velocity_decelerating,
                                             low_saturation):
        """
        Test transition from EMERGING to PEAKING.
        
        Conditions: velocity > 80 AND acceleration < 0
        """
        new_status = manager.determine_status(
            TrendStatus.EMERGING,
            high_velocity_decelerating,
            low_saturation
        )
        
        assert new_status == TrendStatus.PEAKING

    def test_emerging_stays_when_accelerating(self, manager,
                                               high_velocity_accelerating,
                                               low_saturation):
        """
        Test that trend stays EMERGING when still accelerating.
        
        Even with high velocity, if acceleration is positive, 
        trend is still in early growth phase.
        """
        new_status = manager.determine_status(
            TrendStatus.EMERGING,
            high_velocity_accelerating,
            low_saturation
        )
        
        assert new_status == TrendStatus.EMERGING

    def test_emerging_stays_with_moderate_velocity(self, manager,
                                                    low_saturation):
        """Test that trend stays EMERGING with moderate velocity."""
        velocity = VelocityResult(
            score=60,
            growth_rate=10.0,
            doubling_time=7.0,
            r_squared=0.85,
            is_exponential=True,
            acceleration=-0.02,
            confidence=0.8,
            data_points=20,
            time_window_hours=24.0
        )
        
        new_status = manager.determine_status(
            TrendStatus.EMERGING,
            velocity,
            low_saturation
        )
        
        assert new_status == TrendStatus.EMERGING

    # =========================================================================
    # State Transition: EMERGING → EXPIRED
    # =========================================================================

    def test_emerging_to_expired_high_saturation_no_growth(self, manager,
                                                            low_velocity,
                                                            very_high_saturation):
        """
        Test direct transition from EMERGING to EXPIRED.
        
        Conditions: saturation > 90 AND (not exponential OR velocity < 20)
        """
        new_status = manager.determine_status(
            TrendStatus.EMERGING,
            low_velocity,
            very_high_saturation
        )
        
        assert new_status == TrendStatus.EXPIRED

    def test_emerging_to_expired_low_velocity_no_exponential(self, manager,
                                                              low_velocity,
                                                              moderate_saturation):
        """
        Test EMERGING → EXPIRED due to low velocity without exponential growth.
        
        Conditions: velocity < 20 AND not exponential AND sufficient data
        """
        velocity = VelocityResult(
            score=15,
            growth_rate=2.0,
            doubling_time=35.0,
            r_squared=0.40,
            is_exponential=False,
            acceleration=-0.01,
            confidence=0.5,
            data_points=10,  # >= 5 data points
            time_window_hours=12.0
        )
        
        new_status = manager.determine_status(
            TrendStatus.EMERGING,
            velocity,
            moderate_saturation
        )
        
        assert new_status == TrendStatus.EXPIRED

    def test_emerging_stays_with_low_velocity_few_points(self, manager,
                                                          low_velocity,
                                                          moderate_saturation):
        """
        Test that trend stays EMERGING with low velocity but few data points.
        
        If data_points < 5, we wait for more data before expiring.
        """
        velocity = VelocityResult(
            score=15,
            growth_rate=2.0,
            doubling_time=35.0,
            r_squared=0.40,
            is_exponential=False,
            acceleration=-0.01,
            confidence=0.5,
            data_points=3,  # < 5 data points
            time_window_hours=6.0
        )
        
        new_status = manager.determine_status(
            TrendStatus.EMERGING,
            velocity,
            moderate_saturation
        )
        
        # Should stay EMERGING, not expired yet
        assert new_status == TrendStatus.EMERGING

    # =========================================================================
    # State Transition: PEAKING → SATURATED
    # =========================================================================

    def test_peaking_to_saturated_high_saturation(self, manager,
                                                   high_velocity_decelerating,
                                                   high_saturation):
        """
        Test transition from PEAKING to SATURATED due to high saturation.
        
        Conditions: saturation > 70
        """
        new_status = manager.determine_status(
            TrendStatus.PEAKING,
            high_velocity_decelerating,
            high_saturation
        )
        
        assert new_status == TrendStatus.SATURATED

    def test_peaking_to_saturated_strong_deceleration(self, manager,
                                                       high_velocity_decelerating,
                                                       moderate_saturation):
        """
        Test transition from PEAKING to SATURATED due to strong deceleration.
        
        Conditions: acceleration < -0.1
        """
        velocity = VelocityResult(
            score=75,
            growth_rate=15.0,
            doubling_time=4.67,
            r_squared=0.90,
            is_exponential=True,
            acceleration=-0.15,  # Strong deceleration
            confidence=0.85,
            data_points=40,
            time_window_hours=48.0
        )
        
        new_status = manager.determine_status(
            TrendStatus.PEAKING,
            velocity,
            moderate_saturation
        )
        
        assert new_status == TrendStatus.SATURATED

    def test_peaking_stays_without_transition_conditions(self, manager,
                                                          high_velocity_accelerating,
                                                          low_saturation):
        """Test that trend stays PEAKING without transition conditions."""
        new_status = manager.determine_status(
            TrendStatus.PEAKING,
            high_velocity_accelerating,
            low_saturation
        )
        
        assert new_status == TrendStatus.PEAKING

    # =========================================================================
    # State Transition: SATURATED → EXPIRED
    # =========================================================================

    def test_saturated_to_expired_low_velocity(self, manager,
                                                low_velocity,
                                                high_saturation):
        """
        Test transition from SATURATED to EXPIRED due to low velocity.
        
        Conditions: velocity < 20
        """
        new_status = manager.determine_status(
            TrendStatus.SATURATED,
            low_velocity,
            high_saturation
        )
        
        assert new_status == TrendStatus.EXPIRED

    def test_saturated_to_expired_very_high_saturation(self, manager,
                                                        high_velocity_decelerating,
                                                        very_high_saturation):
        """
        Test transition from SATURATED to EXPIRED due to very high saturation.
        
        Conditions: saturation > 90
        """
        new_status = manager.determine_status(
            TrendStatus.SATURATED,
            high_velocity_decelerating,
            very_high_saturation
        )
        
        assert new_status == TrendStatus.EXPIRED

    def test_saturated_stays_with_moderate_metrics(self, manager):
        """Test that trend stays SATURATED with moderate metrics."""
        velocity = VelocityResult(
            score=40,
            growth_rate=8.0,
            doubling_time=8.75,
            r_squared=0.70,
            is_exponential=False,
            acceleration=-0.02,
            confidence=0.7,
            data_points=50,
            time_window_hours=72.0
        )
        
        saturation = SaturationResult(
            score=75,
            stage="mature",
            recommendation="Late stage - limited opportunity"
        )
        
        new_status = manager.determine_status(
            TrendStatus.SATURATED,
            velocity,
            saturation
        )
        
        assert new_status == TrendStatus.SATURATED

    # =========================================================================
    # Expired State (Terminal)
    # =========================================================================

    def test_expired_stays_expired(self, manager, high_velocity_accelerating, low_saturation):
        """
        Test that EXPIRED is a terminal state.
        
        No transitions out of EXPIRED should be possible.
        """
        new_status = manager.determine_status(
            TrendStatus.EXPIRED,
            high_velocity_accelerating,
            low_saturation
        )
        
        assert new_status == TrendStatus.EXPIRED

    def test_expired_ignores_high_velocity(self, manager, high_velocity_decelerating, low_saturation):
        """Test that even high velocity doesn't revive EXPIRED trend."""
        new_status = manager.determine_status(
            TrendStatus.EXPIRED,
            high_velocity_decelerating,
            low_saturation
        )
        
        assert new_status == TrendStatus.EXPIRED

    # =========================================================================
    # Expected Transition Tests
    # =========================================================================

    def test_expected_transition_emerging_to_peaking(self, manager,
                                                      high_velocity_decelerating,
                                                      low_saturation):
        """Test expected transition hint for emerging → peaking."""
        expected = manager.get_expected_transition(
            TrendStatus.EMERGING,
            high_velocity_decelerating,
            low_saturation
        )
        
        assert expected == "peaking"

    def test_expected_transition_emerging_growing(self, manager,
                                                   high_velocity_accelerating,
                                                   low_saturation):
        """Test expected transition hint for still growing trend."""
        expected = manager.get_expected_transition(
            TrendStatus.EMERGING,
            high_velocity_accelerating,
            low_saturation
        )
        
        assert expected == "growing"

    def test_expected_transition_emerging_expiring(self, manager,
                                                    low_velocity,
                                                    high_saturation):
        """Test expected transition hint for expiring trend."""
        velocity = VelocityResult(
            score=30,
            growth_rate=5.0,
            doubling_time=14.0,
            r_squared=0.60,
            is_exponential=False,
            acceleration=-0.05,
            confidence=0.6,
            data_points=20,
            time_window_hours=24.0
        )
        
        expected = manager.get_expected_transition(
            TrendStatus.EMERGING,
            velocity,
            high_saturation
        )
        
        assert expected == "expiring"

    def test_expected_transition_peaking_saturating(self, manager,
                                                     high_velocity_decelerating,
                                                     moderate_saturation):
        """Test expected transition hint for peaking → saturating."""
        expected = manager.get_expected_transition(
            TrendStatus.PEAKING,
            high_velocity_decelerating,
            moderate_saturation
        )
        
        assert expected == "saturating"

    def test_expected_transition_saturated_expiring(self, manager,
                                                     low_velocity,
                                                     high_saturation):
        """Test expected transition hint for saturated → expiring."""
        expected = manager.get_expected_transition(
            TrendStatus.SATURATED,
            low_velocity,
            high_saturation
        )
        
        assert expected == "expiring"

    def test_expected_transition_expired_none(self, manager,
                                               low_velocity,
                                               very_high_saturation):
        """Test that EXPIRED has no expected transition."""
        expected = manager.get_expected_transition(
            TrendStatus.EXPIRED,
            low_velocity,
            very_high_saturation
        )
        
        assert expected is None

    # =========================================================================
    # Status Description Tests
    # =========================================================================

    def test_status_description_emerging(self, manager):
        """Test description for EMERGING status."""
        desc = manager.get_status_description(TrendStatus.EMERGING)
        assert "early growth" in desc.lower()
        assert "opportunity" in desc.lower()

    def test_status_description_peaking(self, manager):
        """Test description for PEAKING status."""
        desc = manager.get_status_description(TrendStatus.PEAKING)
        assert "peak velocity" in desc.lower()

    def test_status_description_saturated(self, manager):
        """Test description for SATURATED status."""
        desc = manager.get_status_description(TrendStatus.SATURATED)
        assert "mainstream adoption" in desc.lower()

    def test_status_description_expired(self, manager):
        """Test description for EXPIRED status."""
        desc = manager.get_status_description(TrendStatus.EXPIRED)
        assert "no longer relevant" in desc.lower()

    # =========================================================================
    # Peak Time Recording Tests
    # =========================================================================

    def test_should_record_peak_time_emerging_to_peaking(self, manager):
        """Test peak time recording for emerging → peaking transition."""
        should_record = manager.should_record_peak_time(
            TrendStatus.EMERGING,
            TrendStatus.PEAKING
        )
        
        assert should_record is True

    def test_should_not_record_peak_time_peaking_to_saturated(self, manager):
        """Test that peak time is NOT recorded for peaking → saturated."""
        should_record = manager.should_record_peak_time(
            TrendStatus.PEAKING,
            TrendStatus.SATURATED
        )
        
        assert should_record is False

    def test_should_not_record_peak_time_same_status(self, manager):
        """Test that peak time is NOT recorded when status unchanged."""
        should_record = manager.should_record_peak_time(
            TrendStatus.EMERGING,
            TrendStatus.EMERGING
        )
        
        assert should_record is False

    # =========================================================================
    # Transition Priority Tests
    # =========================================================================

    def test_transition_priority_to_peaking_high(self, manager):
        """Test that transition to PEAKING is high priority."""
        priority = manager.get_transition_priority(
            TrendStatus.EMERGING,
            TrendStatus.PEAKING
        )
        
        assert priority == "high"

    def test_transition_priority_peaking_to_saturated_medium(self, manager):
        """Test that peaking → saturated is medium priority."""
        priority = manager.get_transition_priority(
            TrendStatus.PEAKING,
            TrendStatus.SATURATED
        )
        
        assert priority == "medium"

    def test_transition_priority_emerging_to_expired_medium(self, manager):
        """Test that early expiration is medium priority."""
        priority = manager.get_transition_priority(
            TrendStatus.EMERGING,
            TrendStatus.EXPIRED
        )
        
        assert priority == "medium"

    def test_transition_priority_other_low(self, manager):
        """Test that other transitions are low priority."""
        priority = manager.get_transition_priority(
            TrendStatus.SATURATED,
            TrendStatus.EXPIRED
        )
        
        assert priority == "low"


class TestLifecycleTransition:
    """Test suite for LifecycleTransition dataclass."""

    def test_lifecycle_transition_creation(self):
        """Test creating a LifecycleTransition instance."""
        transition = LifecycleTransition(
            from_status=TrendStatus.EMERGING,
            to_status=TrendStatus.PEAKING,
            reason="High velocity with deceleration",
            velocity_at_transition=85,
            saturation_at_transition=30
        )
        
        assert transition.from_status == TrendStatus.EMERGING
        assert transition.to_status == TrendStatus.PEAKING
        assert "deceleration" in transition.reason
        assert transition.velocity_at_transition == 85


class TestThresholdConfiguration:
    """Test suite for lifecycle threshold configuration."""

    def test_default_thresholds(self):
        """Test default threshold values."""
        manager = LifecycleManager()
        
        assert manager.emerging_to_peaking_velocity == 80
        assert manager.peaking_to_saturated_saturation == 70
        assert manager.saturated_to_expired_velocity == 20
        assert manager.saturated_to_expired_saturation == 90
        assert manager.emerging_to_expired_saturation == 90

    def test_threshold_ranges(self):
        """Test that thresholds are within valid ranges."""
        manager = LifecycleManager()
        
        assert 0 <= manager.emerging_to_peaking_velocity <= 100
        assert 0 <= manager.peaking_to_saturated_saturation <= 100
        assert 0 <= manager.saturated_to_expired_velocity <= 100
        assert 0 <= manager.saturated_to_expired_saturation <= 100
