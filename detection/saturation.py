"""
Saturation Engine

Calculates saturation score (0-100%) based on trend lifecycle.
Saturation indicates how "used up" a trend is.

Saturation Stages:
- 0-30%: Early stage, high opportunity window
- 30-60%: Growth stage, still good opportunity
- 60-80%: Mature stage, decreasing returns
- 80-100%: Saturated/decline, limited opportunity

Factors considered:
- Acceleration (positive = early, negative = late)
- Time since detection (longer = more saturated)
- Velocity score (very high = might be peaking)
- Data point count (more data = more mature)
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from detection.velocity_engine import VelocityResult
from detection.models import Trend
from detection.config import settings
from detection.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SaturationResult:
    """Saturation calculation result."""

    score: int                      # 0-100 saturation percentage
    stage: str                      # 'early' | 'growth' | 'mature' | 'decline'
    recommendation: str             # Action recommendation for user


class SaturationEngine:
    """
    Calculates trend saturation using multiple signals.

    Saturation indicates how "used up" a trend is and helps users
    understand the opportunity window.

    The scoring combines multiple factors with configurable weights:
    - Acceleration (30%): Is growth accelerating or decelerating?
    - Time since detection (25%): How long has the trend existed?
    - Velocity score (25%): How hot is the trend right now?
    - Data volume (20%): How much data has accumulated?

    Stage Classification:
    - early (0-30%): Prime opportunity - jump on this trend now
    - growth (30-60%): Good opportunity - still room to grow
    - mature (60-80%): Moderate opportunity - act quickly
    - decline (80-100%): Late stage - limited returns
    """

    # Saturation stage thresholds
    EARLY_THRESHOLD = 30
    GROWTH_THRESHOLD = 60
    MATURE_THRESHOLD = 80

    def __init__(self):
        """Initialize saturation engine with configuration weights."""
        self.weight_acceleration = settings.saturation_weight_acceleration
        self.weight_time = settings.saturation_weight_time
        self.weight_velocity = settings.saturation_weight_velocity
        self.weight_volume = settings.saturation_weight_volume

    def calculate(
        self,
        velocity: VelocityResult,
        existing_trend: Optional[Trend],
        data_points: int
    ) -> SaturationResult:
        """
        Calculate saturation score for a trend.

        Args:
            velocity: Current velocity calculation result
            existing_trend: Existing trend record (None if new trend)
            data_points: Number of data points accumulated

        Returns:
            SaturationResult with score, stage, and recommendation
        """
        if existing_trend is None:
            return self._new_trend_saturation()

        # Calculate component scores
        acceleration_score = self._acceleration_to_saturation(
            velocity.acceleration
        )
        time_score = self._time_to_saturation(
            existing_trend.first_detected_at
        )
        velocity_score = self._velocity_to_saturation(
            velocity.score,
            velocity.is_exponential
        )
        volume_score = self._volume_to_saturation(data_points)

        # Weighted combination
        saturation = (
            acceleration_score * self.weight_acceleration +
            time_score * self.weight_time +
            velocity_score * self.weight_velocity +
            volume_score * self.weight_volume
        )

        score = int(min(100, max(0, saturation)))
        stage = self._determine_stage(score)
        recommendation = self._get_recommendation(score, velocity.score)

        logger.debug(
            "saturation_calculated",
            score=score,
            stage=stage,
            acceleration_score=acceleration_score,
            time_score=time_score,
            velocity_score=velocity_score,
            volume_score=volume_score
        )

        return SaturationResult(
            score=score,
            stage=stage,
            recommendation=recommendation
        )

    def _new_trend_saturation(self) -> SaturationResult:
        """Saturation for newly detected trend.

        New trends always start with low saturation (high opportunity).
        """
        return SaturationResult(
            score=10,
            stage="early",
            recommendation="New trend - prime opportunity window"
        )

    def _acceleration_to_saturation(self, acceleration: float) -> float:
        """
        Convert acceleration to saturation component.

        Positive acceleration = early stage = low saturation
        Negative acceleration = late stage = high saturation

        Args:
            acceleration: Second derivative of growth

        Returns:
            Saturation contribution (0-100 scale)
        """
        if acceleration > 0.1:
            # Strong acceleration = very early, low saturation
            return 20
        elif acceleration > 0:
            # Slight acceleration = still early
            return 35
        elif acceleration > -0.05:
            # Near zero = stable/mature
            return 50
        elif acceleration > -0.1:
            # Slight deceleration = starting to mature
            return 65
        else:
            # Strong deceleration = late stage, high saturation
            return 80

    def _time_to_saturation(self, first_detected: datetime) -> float:
        """
        Convert time since detection to saturation.

        Longer existence = higher saturation (more people have used it).

        Args:
            first_detected: When the trend was first detected

        Returns:
            Saturation contribution (0-100 scale)
        """
        hours_since = (datetime.utcnow() - first_detected).total_seconds() / 3600

        if hours_since < 6:
            # Very new (< 6 hours)
            return 15
        elif hours_since < 24:
            # First day
            return 30
        elif hours_since < 72:
            # First 3 days (optimal window)
            return 50
        elif hours_since < 168:
            # First week
            return 70
        else:
            # Over a week old
            return 85

    def _velocity_to_saturation(
        self,
        velocity_score: int,
        is_exponential: bool
    ) -> float:
        """
        Convert velocity score to saturation.

        Very high velocity might indicate peaking (about to decline).
        Low velocity indicates the trend has already peaked or never took off.

        Args:
            velocity_score: Current velocity score (0-100)
            is_exponential: Whether growth is exponential

        Returns:
            Saturation contribution (0-100 scale)
        """
        if velocity_score > 90 and is_exponential:
            # Very high velocity + exponential = likely at/near peak
            # This is actually a warning sign
            return 75
        elif velocity_score > 70:
            # High velocity = still growing but might be peaking
            return 50
        elif velocity_score > 50:
            # Moderate velocity = stable growth
            return 35
        elif velocity_score > 30:
            # Low-moderate velocity = could be declining
            return 45
        else:
            # Low velocity = already past peak or never took off
            return 60

    def _volume_to_saturation(self, data_points: int) -> float:
        """
        Convert data point volume to saturation.

        More data points = more videos using the trend = more saturated.

        Args:
            data_points: Number of data points accumulated

        Returns:
            Saturation contribution (0-100 scale)
        """
        if data_points < 10:
            # Very few videos
            return 15
        elif data_points < 50:
            # Some adoption
            return 30
        elif data_points < 100:
            # Moderate adoption
            return 50
        elif data_points < 500:
            # High adoption
            return 70
        else:
            # Very high adoption = mainstream
            return 85

    def _determine_stage(self, score: int) -> str:
        """
        Determine trend stage from saturation score.

        Args:
            score: Saturation score (0-100)

        Returns:
            Stage name: 'early' | 'growth' | 'mature' | 'decline'
        """
        if score < self.EARLY_THRESHOLD:
            return "early"
        elif score < self.GROWTH_THRESHOLD:
            return "growth"
        elif score < self.MATURE_THRESHOLD:
            return "mature"
        else:
            return "decline"

    def _get_recommendation(self, saturation: int, velocity: int) -> str:
        """
        Generate action recommendation for the user.

        Combines saturation and velocity to provide actionable guidance.

        Args:
            saturation: Saturation score (0-100)
            velocity: Velocity score (0-100)

        Returns:
            Human-readable recommendation string
        """
        # High velocity + low saturation = best opportunity
        if saturation < 30:
            if velocity > 70:
                return "Prime opportunity - hot trend with room to grow"
            elif velocity > 40:
                return "Good opportunity - jump on this trend now"
            else:
                return "Early stage - monitor for growth before acting"
        elif saturation < 50:
            if velocity > 60:
                return "Strong opportunity - still growing, act quickly"
            else:
                return "Good opportunity - still room to grow"
        elif saturation < 70:
            if velocity > 50:
                return "Moderate opportunity - act quickly while relevant"
            else:
                return "Limited window - consider if unique angle available"
        elif saturation < 85:
            return "Late stage - only pursue if unique angle available"
        else:
            return "Saturated - may not yield significant returns"


def get_saturation_description(stage: str) -> str:
    """
    Get human-readable description for saturation stage.

    Args:
        stage: Stage name ('early', 'growth', 'mature', 'decline')

    Returns:
        Description string
    """
    descriptions = {
        "early": "Fresh trend with high opportunity - creators can be early adopters",
        "growth": "Growing trend with good opportunity - still room to participate",
        "mature": "Established trend - participate quickly before decline",
        "decline": "Saturated trend - limited opportunity, consider alternatives"
    }
    return descriptions.get(stage, "Unknown stage")
