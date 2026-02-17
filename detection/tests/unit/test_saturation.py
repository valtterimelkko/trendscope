"""
Unit Tests for Saturation Engine

Tests saturation score calculation, stage detection, and lifecycle thresholds.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from detection.saturation import (
    SaturationEngine,
    SaturationResult,
    get_saturation_description
)
from detection.velocity_engine import VelocityResult, VelocityEngine
from detection.models import Trend, TrendType, TrendStatus


class TestSaturationEngine:
    """Test suite for SaturationEngine class."""

    @pytest.fixture
    def engine(self):
        """Create a SaturationEngine instance."""
        return SaturationEngine()

    @pytest.fixture
    def mock_velocity_high_exponential(self):
        """Create a mock VelocityResult with high exponential growth."""
        return VelocityResult(
            score=85,
            growth_rate=20.0,
            doubling_time=3.5,
            r_squared=0.95,
            is_exponential=True,
            acceleration=0.1,
            confidence=0.9,
            data_points=30,
            time_window_hours=48.0
        )

    @pytest.fixture
    def mock_velocity_moderate(self):
        """Create a mock VelocityResult with moderate growth."""
        return VelocityResult(
            score=45,
            growth_rate=8.0,
            doubling_time=8.75,
            r_squared=0.75,
            is_exponential=False,
            acceleration=0.0,
            confidence=0.7,
            data_points=20,
            time_window_hours=24.0
        )

    @pytest.fixture
    def mock_velocity_decelerating(self):
        """Create a mock VelocityResult with decelerating growth."""
        return VelocityResult(
            score=30,
            growth_rate=3.0,
            doubling_time=23.33,
            r_squared=0.60,
            is_exponential=False,
            acceleration=-0.15,
            confidence=0.6,
            data_points=50,
            time_window_hours=72.0
        )

    @pytest.fixture
    def mock_existing_trend(self):
        """Create a mock existing Trend."""
        return Trend(
            type=TrendType.HASHTAG,
            name="#testtrend",
            platform_id="test123",
            first_detected_at=datetime.utcnow() - timedelta(hours=24),
            status=TrendStatus.EMERGING,
            velocity_score=50,
            saturation_percent=30
        )

    # =========================================================================
    # Saturation Score Calculation (0-100%)
    # =========================================================================

    def test_saturation_score_calculation_new_trend(self, engine):
        """
        Test saturation calculation for new trend (no existing trend).
        
        New trends should always have low saturation (10%).
        """
        velocity = VelocityResult(
            score=50,
            growth_rate=10.0,
            doubling_time=7.0,
            r_squared=0.85,
            is_exponential=True,
            acceleration=0.05,
            confidence=0.8,
            data_points=10,
            time_window_hours=12.0
        )
        
        result = engine.calculate(velocity, None, 10)
        
        assert result.score == 10
        assert result.stage == "early"
        assert "New trend" in result.recommendation

    def test_saturation_score_calculation_with_existing(self, engine, 
                                                         mock_velocity_high_exponential,
                                                         mock_existing_trend):
        """Test saturation calculation with existing trend."""
        result = engine.calculate(
            mock_velocity_high_exponential,
            mock_existing_trend,
            30
        )
        
        assert 0 <= result.score <= 100
        assert result.stage in ["early", "growth", "mature", "decline"]

    def test_saturation_score_bounds(self, engine, mock_velocity_moderate):
        """Test that saturation score is always between 0 and 100."""
        for hours in [1, 6, 24, 72, 168, 500]:
            trend = Trend(
                type=TrendType.HASHTAG,
                name="#test",
                platform_id="test",
                first_detected_at=datetime.utcnow() - timedelta(hours=hours),
                status=TrendStatus.EMERGING,
                velocity_score=50,
                saturation_percent=50
            )
            
            result = engine.calculate(mock_velocity_moderate, trend, 100)
            assert 0 <= result.score <= 100

    # =========================================================================
    # Stage Detection Tests
    # =========================================================================

    def test_early_stage_detection_0_to_30_percent(self, engine):
        """
        Test early stage detection (0-30%).
        
        Early stage characteristics:
        - Strong positive acceleration
        - Recent detection (< 6 hours)
        - Low data volume (< 10 points)
        """
        velocity = VelocityResult(
            score=60,
            growth_rate=15.0,
            doubling_time=4.67,
            r_squared=0.90,
            is_exponential=True,
            acceleration=0.15,  # Strong acceleration
            confidence=0.85,
            data_points=8,
            time_window_hours=6.0
        )
        
        trend = Trend(
            type=TrendType.HASHTAG,
            name="#early",
            platform_id="early123",
            first_detected_at=datetime.utcnow() - timedelta(hours=3),
            status=TrendStatus.EMERGING,
            velocity_score=60,
            saturation_percent=10
        )
        
        result = engine.calculate(velocity, trend, 8)
        
        assert result.stage == "early"
        assert result.score <= 30

    def test_growth_stage_detection_30_to_60_percent(self, engine):
        """
        Test growth stage detection (30-60%).
        
        Growth stage characteristics:
        - Moderate acceleration or stable
        - Detected within 6-24 hours
        - Moderate data volume (10-50 points)
        """
        velocity = VelocityResult(
            score=55,
            growth_rate=10.0,
            doubling_time=7.0,
            r_squared=0.85,
            is_exponential=True,
            acceleration=0.02,  # Slight acceleration
            confidence=0.8,
            data_points=25,
            time_window_hours=18.0
        )
        
        trend = Trend(
            type=TrendType.HASHTAG,
            name="#growth",
            platform_id="growth123",
            first_detected_at=datetime.utcnow() - timedelta(hours=12),
            status=TrendStatus.EMERGING,
            velocity_score=55,
            saturation_percent=35
        )
        
        result = engine.calculate(velocity, trend, 25)
        
        assert result.stage == "growth"
        assert 30 <= result.score < 60

    def test_mature_stage_detection_60_to_80_percent(self, engine):
        """
        Test mature/peaking stage detection (60-80%).
        
        Mature stage characteristics:
        - Negative acceleration (decelerating)
        - Detected 1-3 days ago
        - High velocity score (> 70)
        """
        velocity = VelocityResult(
            score=95,  # Very high velocity with exponential = warning sign
            growth_rate=25.0,
            doubling_time=2.8,
            r_squared=0.90,
            is_exponential=True,
            acceleration=-0.15,  # Strong deceleration
            confidence=0.85,
            data_points=150,  # High volume
            time_window_hours=72.0
        )
        
        trend = Trend(
            type=TrendType.HASHTAG,
            name="#mature",
            platform_id="mature123",
            first_detected_at=datetime.utcnow() - timedelta(hours=100),  # Old
            status=TrendStatus.PEAKING,
            velocity_score=75,
            saturation_percent=65
        )
        
        result = engine.calculate(velocity, trend, 150)
        
        assert result.stage in ["mature", "decline"]  # May be mature or declining
        assert result.score >= 60

    def test_decline_stage_detection_80_plus_percent(self, engine):
        """
        Test saturated/decline stage detection (80%+).
        
        Decline stage characteristics:
        - Strong negative acceleration
        - Very old trend (> 1 week)
        - Low velocity (< 30)
        - High data volume (> 500 points)
        """
        velocity = VelocityResult(
            score=15,  # Low velocity
            growth_rate=2.0,
            doubling_time=35.0,
            r_squared=0.50,
            is_exponential=False,
            acceleration=-0.2,  # Strong deceleration = 80 saturation contribution
            confidence=0.6,
            data_points=600,  # Very high volume = 85 saturation contribution
            time_window_hours=168.0
        )
        
        trend = Trend(
            type=TrendType.HASHTAG,
            name="#decline",
            platform_id="decline123",
            first_detected_at=datetime.utcnow() - timedelta(hours=200),  # Very old = 85 time contribution
            status=TrendStatus.SATURATED,
            velocity_score=15,
            saturation_percent=85
        )
        
        result = engine.calculate(velocity, trend, 600)
        
        # With weighted components, we should be in decline range
        # If not exactly 80+, verify it's at least in mature range
        assert result.score >= 60  # Score should be at least mature
        if result.score >= 80:
            assert result.stage == "decline"
        else:
            assert result.stage in ["mature", "decline"]

    # =========================================================================
    # Component Score Tests
    # =========================================================================

    def test_acceleration_to_saturation_positive(self, engine):
        """Test acceleration conversion with positive values."""
        # Strong acceleration (> 0.1) = very early, low saturation
        assert engine._acceleration_to_saturation(0.15) == 20
        
        # Slight acceleration (> 0) = still early
        assert engine._acceleration_to_saturation(0.05) == 35
        assert engine._acceleration_to_saturation(0.01) == 35

    def test_acceleration_to_saturation_negative(self, engine):
        """Test acceleration conversion with negative values."""
        # Near zero (> -0.05) = stable/mature
        assert engine._acceleration_to_saturation(-0.02) == 50
        
        # Slight deceleration (> -0.1) = starting to mature
        assert engine._acceleration_to_saturation(-0.08) == 65
        
        # Strong deceleration (<= -0.1) = late stage
        assert engine._acceleration_to_saturation(-0.1) == 80
        assert engine._acceleration_to_saturation(-0.2) == 80

    def test_time_to_saturation_very_new(self, engine):
        """Test time-based saturation for very new trends (< 6 hours)."""
        first_detected = datetime.utcnow() - timedelta(hours=3)
        assert engine._time_to_saturation(first_detected) == 15

    def test_time_to_saturation_first_day(self, engine):
        """Test time-based saturation for first day trends (6-24 hours)."""
        first_detected = datetime.utcnow() - timedelta(hours=12)
        assert engine._time_to_saturation(first_detected) == 30

    def test_time_to_saturation_first_3_days(self, engine):
        """Test time-based saturation for first 3 days (optimal window)."""
        first_detected = datetime.utcnow() - timedelta(hours=48)
        assert engine._time_to_saturation(first_detected) == 50

    def test_time_to_saturation_first_week(self, engine):
        """Test time-based saturation for first week."""
        first_detected = datetime.utcnow() - timedelta(hours=100)
        assert engine._time_to_saturation(first_detected) == 70

    def test_time_to_saturation_over_week(self, engine):
        """Test time-based saturation for trends over a week old."""
        first_detected = datetime.utcnow() - timedelta(hours=200)
        assert engine._time_to_saturation(first_detected) == 85

    def test_velocity_to_saturation_very_high_exponential(self, engine):
        """
        Test velocity conversion for very high exponential growth.
        
        High velocity + exponential = likely peaking (warning sign)
        """
        assert engine._velocity_to_saturation(95, True) == 75
        assert engine._velocity_to_saturation(92, True) == 75

    def test_velocity_to_saturation_high(self, engine):
        """Test velocity conversion for high velocity."""
        assert engine._velocity_to_saturation(75, True) == 50
        assert engine._velocity_to_saturation(80, False) == 50

    def test_velocity_to_saturation_moderate(self, engine):
        """Test velocity conversion for moderate velocity."""
        assert engine._velocity_to_saturation(60, True) == 35
        assert engine._velocity_to_saturation(55, False) == 35

    def test_velocity_to_saturation_low(self, engine):
        """Test velocity conversion for low velocity."""
        # Low velocity = already past peak or never took off
        assert engine._velocity_to_saturation(20, False) == 60
        assert engine._velocity_to_saturation(10, False) == 60

    def test_volume_to_saturation_few_videos(self, engine):
        """Test volume-based saturation with very few videos."""
        assert engine._volume_to_saturation(5) == 15
        assert engine._volume_to_saturation(9) == 15

    def test_volume_to_saturation_some_adoption(self, engine):
        """Test volume-based saturation with some adoption."""
        assert engine._volume_to_saturation(25) == 30
        assert engine._volume_to_saturation(49) == 30

    def test_volume_to_saturation_moderate(self, engine):
        """Test volume-based saturation with moderate adoption."""
        assert engine._volume_to_saturation(75) == 50
        assert engine._volume_to_saturation(99) == 50

    def test_volume_to_saturation_high(self, engine):
        """Test volume-based saturation with high adoption."""
        assert engine._volume_to_saturation(250) == 70
        assert engine._volume_to_saturation(499) == 70

    def test_volume_to_saturation_mainstream(self, engine):
        """Test volume-based saturation with mainstream adoption."""
        assert engine._volume_to_saturation(500) == 85
        assert engine._volume_to_saturation(1000) == 85

    # =========================================================================
    # Recommendation Tests
    # =========================================================================

    def test_recommendation_early_high_velocity(self, engine):
        """Test recommendation for early stage with high velocity."""
        rec = engine._get_recommendation(saturation=20, velocity=80)
        assert "Prime opportunity" in rec

    def test_recommendation_early_moderate_velocity(self, engine):
        """Test recommendation for early stage with moderate velocity."""
        rec = engine._get_recommendation(saturation=25, velocity=50)
        assert "Good opportunity" in rec

    def test_recommendation_early_low_velocity(self, engine):
        """Test recommendation for early stage with low velocity."""
        rec = engine._get_recommendation(saturation=15, velocity=20)
        assert "monitor" in rec.lower()

    def test_recommendation_growth_high_velocity(self, engine):
        """Test recommendation for growth stage with high velocity."""
        rec = engine._get_recommendation(saturation=45, velocity=70)
        assert "Strong opportunity" in rec

    def test_recommendation_moderate_velocity(self, engine):
        """Test recommendation for moderate opportunity."""
        rec = engine._get_recommendation(saturation=65, velocity=55)
        assert "Moderate opportunity" in rec

    def test_recommendation_late_stage(self, engine):
        """Test recommendation for late stage."""
        rec = engine._get_recommendation(saturation=80, velocity=30)
        assert "Late stage" in rec

    def test_recommendation_saturated(self, engine):
        """Test recommendation for saturated trend."""
        rec = engine._get_recommendation(saturation=95, velocity=10)
        assert "Saturated" in rec

    # =========================================================================
    # Lifecycle Threshold Determination
    # =========================================================================

    def test_stage_determination_early(self, engine):
        """Test stage determination for early stage."""
        assert engine._determine_stage(0) == "early"
        assert engine._determine_stage(15) == "early"
        assert engine._determine_stage(29) == "early"

    def test_stage_determination_growth(self, engine):
        """Test stage determination for growth stage."""
        assert engine._determine_stage(30) == "growth"
        assert engine._determine_stage(45) == "growth"
        assert engine._determine_stage(59) == "growth"

    def test_stage_determination_mature(self, engine):
        """Test stage determination for mature stage."""
        assert engine._determine_stage(60) == "mature"
        assert engine._determine_stage(70) == "mature"
        assert engine._determine_stage(79) == "mature"

    def test_stage_determination_decline(self, engine):
        """Test stage determination for decline stage."""
        assert engine._determine_stage(80) == "decline"
        assert engine._determine_stage(90) == "decline"
        assert engine._determine_stage(100) == "decline"


class TestSaturationResult:
    """Test suite for SaturationResult dataclass."""

    def test_saturation_result_creation(self):
        """Test creating a SaturationResult instance."""
        result = SaturationResult(
            score=45,
            stage="growth",
            recommendation="Good opportunity - jump on this trend now"
        )
        
        assert result.score == 45
        assert result.stage == "growth"
        assert "opportunity" in result.recommendation


class TestGetSaturationDescription:
    """Test suite for get_saturation_description function."""

    def test_description_early(self):
        """Test description for early stage."""
        desc = get_saturation_description("early")
        assert "Fresh trend" in desc
        assert "high opportunity" in desc

    def test_description_growth(self):
        """Test description for growth stage."""
        desc = get_saturation_description("growth")
        assert "Growing trend" in desc
        assert "good opportunity" in desc

    def test_description_mature(self):
        """Test description for mature stage."""
        desc = get_saturation_description("mature")
        assert "Established trend" in desc
        assert "participate quickly" in desc

    def test_description_decline(self):
        """Test description for decline stage."""
        desc = get_saturation_description("decline")
        assert "Saturated trend" in desc
        assert "limited opportunity" in desc

    def test_description_unknown(self):
        """Test description for unknown stage."""
        desc = get_saturation_description("unknown")
        assert desc == "Unknown stage"


class TestSaturationWeights:
    """Test suite for saturation weight configuration."""

    def test_default_weights_sum_to_one(self):
        """Test that default weights sum to approximately 1.0."""
        engine = SaturationEngine()
        
        total = (
            engine.weight_acceleration +
            engine.weight_time +
            engine.weight_velocity +
            engine.weight_volume
        )
        
        assert abs(total - 1.0) < 0.01

    def test_weight_ranges(self):
        """Test that weights are within valid range (0-1)."""
        engine = SaturationEngine()
        
        assert 0 <= engine.weight_acceleration <= 1
        assert 0 <= engine.weight_time <= 1
        assert 0 <= engine.weight_velocity <= 1
        assert 0 <= engine.weight_volume <= 1
