"""
Velocity Calculation Engine

Implements exponential growth detection for trend identification.
Based on TECH_FEASIBILITY.md Section 2 algorithms.

Core Algorithm:
1. Fit exponential curve to video count over time
2. Calculate R-squared to determine exponential fit quality
3. If R-squared > 0.85, growth is exponential
4. Calculate growth rate and doubling time (Rule of 70)

Uses numpy and scipy for numerical calculations.
"""

import numpy as np
from scipy import stats
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from detection.config import settings
from detection.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class VelocityResult:
    """Result of velocity calculation."""

    score: int                      # 0-100 velocity score
    growth_rate: float              # Percentage growth rate per hour
    doubling_time: float            # Hours to double (Rule of 70)
    r_squared: float                # Coefficient of determination
    is_exponential: bool            # True if R-squared > 0.85
    acceleration: float             # Second derivative (trend direction)
    confidence: float               # Confidence in the result (0-1)
    data_points: int                # Number of data points used
    time_window_hours: float        # Time span of data


class VelocityEngine:
    """
    Calculates trend velocity using exponential growth detection.

    Algorithm from TECH_FEASIBILITY.md Section 2:
    1. Fit exponential curve to video count over time
    2. Calculate R-squared to determine exponential fit quality
    3. If R-squared > 0.85, growth is exponential
    4. Calculate growth rate and doubling time (Rule of 70)

    The velocity score is a 0-100 scale representing how "hot" a trend is:
    - 0-30: Low velocity, may not be significant
    - 30-50: Moderate velocity, emerging trend
    - 50-80: High velocity, strong trend
    - 80-100: Viral velocity, immediate attention needed
    """

    # Configuration thresholds (from settings)
    R_SQUARED_THRESHOLD: float = 0.85      # Exponential growth threshold
    MIN_DATA_POINTS: int = 3               # Minimum points for calculation
    MAX_DATA_POINTS: int = 168             # 7 days of hourly data

    def __init__(self):
        """Initialize velocity engine with configuration."""
        self.r_squared_threshold = settings.velocity_r_squared_threshold
        self.min_data_points = settings.velocity_min_data_points
        self.max_data_points = settings.velocity_max_data_points
        self.adaptive_thresholds = AdaptiveThresholds()

    def calculate_velocity(
        self,
        data_points: List[Tuple[datetime, int]]
    ) -> VelocityResult:
        """
        Calculate velocity from time-series data.

        The core algorithm:
        1. Log-transform the data for linear regression
        2. Fit linear regression to log-transformed data
        3. Calculate R-squared (coefficient of determination)
        4. If R-squared > threshold, classify as exponential growth
        5. Calculate doubling time using Rule of 70

        Args:
            data_points: List of (timestamp, count) tuples
                        timestamp: when the observation was made
                        count: video count or play count at that time

        Returns:
            VelocityResult with all calculated metrics
        """
        if len(data_points) < self.min_data_points:
            return self._insufficient_data_result(len(data_points))

        # Sort by timestamp and extract arrays
        sorted_data = sorted(data_points, key=lambda x: x[0])
        timestamps, counts = zip(*sorted_data)

        # Convert timestamps to relative hours from first observation
        t0 = timestamps[0]
        times = np.array([(t - t0).total_seconds() / 3600 for t in timestamps])
        counts = np.array(counts, dtype=float)

        # Filter out zero/negative counts for log transformation
        valid_mask = counts > 0
        if np.sum(valid_mask) < self.min_data_points:
            return self._insufficient_data_result(len(data_points))

        times = times[valid_mask]
        counts = counts[valid_mask]

        # Log-transform for exponential fitting: ln(V) = ln(V0) + r*t
        log_counts = np.log(counts)

        # Linear regression on log-transformed data
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                times, log_counts
            )
        except Exception as e:
            logger.warning(
                "velocity_regression_failed",
                error=str(e),
                data_points=len(data_points)
            )
            return self._insufficient_data_result(len(data_points))

        r_squared = r_value ** 2
        growth_rate = slope * 100  # Convert to percentage per hour

        # Doubling time (Rule of 70)
        # T_double = 70 / growth_rate_percentage
        if growth_rate > 0:
            doubling_time = 70 / growth_rate
        else:
            doubling_time = float('inf')

        # Calculate acceleration (second derivative)
        acceleration = self._calculate_acceleration(times, counts)

        # Determine if exponential growth (R-squared > threshold)
        is_exponential = r_squared > self.r_squared_threshold

        # Calculate velocity score (0-100)
        velocity_score = self._calculate_score(
            growth_rate, r_squared, is_exponential
        )

        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(
            len(data_points),
            r_squared,
            times[-1] - times[0]  # time window
        )

        logger.debug(
            "velocity_calculated",
            score=velocity_score,
            growth_rate=round(growth_rate, 2),
            r_squared=round(r_squared, 3),
            is_exponential=is_exponential,
            data_points=len(data_points)
        )

        # Defensive: Check for NaN/inf values before rounding to avoid errors
        # NaN can occur with insufficient or invalid data points
        def safe_round(val, digits):
            if np.isnan(val) or np.isinf(val):
                return 0.0 if digits > 0 else 0
            return round(val, digits)
        
        return VelocityResult(
            score=safe_round(velocity_score, 0) if not np.isnan(velocity_score) else 0,
            growth_rate=safe_round(growth_rate, 2),
            doubling_time=safe_round(doubling_time, 2) if not np.isinf(doubling_time) else float('inf'),
            r_squared=safe_round(r_squared, 3),
            is_exponential=is_exponential,
            acceleration=safe_round(acceleration, 4),
            confidence=safe_round(confidence, 2),
            data_points=len(data_points),
            time_window_hours=safe_round(times[-1] - times[0], 2)
        )

    def _calculate_score(
        self,
        growth_rate: float,
        r_squared: float,
        is_exponential: bool
    ) -> int:
        """
        Calculate 0-100 velocity score.

        Scoring logic (from TECH_FEASIBILITY.md):
        - Exponential growth (R-squared > 0.85) with high rate:
          score = growth_rate, capped at 100
        - Linear/other growth: score = growth_rate * r_squared

        Additional considerations:
        - Minimum score of 0
        - Maximum score of 100
        """
        # Defensive: Check for NaN/inf values
        if np.isnan(growth_rate) or np.isinf(growth_rate):
            return 0
        if np.isnan(r_squared) or np.isinf(r_squared):
            r_squared = 0
        
        if is_exponential and growth_rate > 50:
            # Exponential growth with high rate = high score
            # Score directly reflects growth rate for viral content
            return min(100, max(0, int(growth_rate)))
        else:
            # Linear or weak growth = reduced score
            # Multiply by r_squared to penalize poor fits
            raw_score = growth_rate * r_squared
            if np.isnan(raw_score):
                return 0
            return min(100, max(0, int(raw_score)))

    def _calculate_acceleration(
        self,
        times: np.ndarray,
        counts: np.ndarray
    ) -> float:
        """
        Calculate acceleration (second derivative).

        Positive acceleration = growth is accelerating (early stage)
        Negative acceleration = growth is decelerating (late stage)
        Near zero = linear/stable growth

        This helps determine if a trend is in early or late phase.
        """
        if len(times) < 3:
            return 0.0

        try:
            # Calculate first derivative (velocity) at each point
            velocities = np.diff(counts) / np.diff(times)

            # Calculate second derivative (acceleration)
            if len(velocities) >= 2:
                accelerations = np.diff(velocities) / np.diff(times[:-1])
                return float(np.mean(accelerations))

            return 0.0
        except Exception:
            return 0.0

    def _calculate_confidence(
        self,
        data_points: int,
        r_squared: float,
        time_window: float
    ) -> float:
        """
        Calculate confidence in the velocity result.

        Factors:
        - More data points = higher confidence
        - Higher R-squared = higher confidence (better fit)
        - Longer time window = higher confidence (more data)

        Returns value between 0 and 1.
        """
        # Base confidence from data points (max at 24 points = 1 full day)
        points_factor = min(1.0, data_points / 24)

        # R-squared factor (direct mapping)
        r_factor = r_squared

        # Time window factor (prefer 6-72 hour windows)
        if 6 <= time_window <= 72:
            window_factor = 1.0
        elif time_window < 6:
            window_factor = time_window / 6
        else:
            # Diminishing confidence for very long windows
            window_factor = max(0.5, 1.0 - (time_window - 72) / 168)

        # Weighted combination
        confidence = (
            points_factor * 0.3 +
            r_factor * 0.4 +
            window_factor * 0.3
        )

        return min(1.0, max(0.0, confidence))

    def _insufficient_data_result(self, points: int) -> VelocityResult:
        """Return result for insufficient data."""
        return VelocityResult(
            score=0,
            growth_rate=0.0,
            doubling_time=float('inf'),
            r_squared=0.0,
            is_exponential=False,
            acceleration=0.0,
            confidence=0.0,
            data_points=points,
            time_window_hours=0.0
        )


class AdaptiveThresholds:
    """
    Adaptive percentile thresholds for dynamic alert levels.

    Implements BERTrend-style self-adjusting thresholds that
    adapt to the distribution of velocity scores over time.

    This helps prevent alert fatigue during high-activity periods
    and ensures alerts are meaningful relative to current baseline.
    """

    def __init__(self, window_days: int = 7):
        """
        Initialize adaptive thresholds.

        Args:
            window_days: Rolling window for threshold calculation
        """
        self.window_days = window_days
        self.percentile_cache: Dict[str, Dict] = {}

    def calculate_percentiles(
        self,
        historical_scores: List[float]
    ) -> Dict[str, float]:
        """
        Calculate adaptive thresholds over rolling window.

        Uses numpy percentile calculation for efficiency.

        Args:
            historical_scores: List of historical velocity scores

        Returns:
            Dict with P10, P50, P90, P99 percentiles
        """
        min_samples = settings.adaptive_threshold_min_samples

        if len(historical_scores) < min_samples:
            # Insufficient data, use sensible defaults
            return {
                "P10": 10.0,
                "P50": 50.0,
                "P90": 75.0,
                "P99": 90.0
            }

        scores = np.array(historical_scores)

        return {
            "P10": float(np.percentile(scores, 10)),
            "P50": float(np.percentile(scores, 50)),
            "P90": float(np.percentile(scores, 90)),
            "P99": float(np.percentile(scores, 99))
        }

    def classify_score(
        self,
        score: float,
        percentiles: Dict[str, float]
    ) -> str:
        """
        Classify velocity score into alert level.

        Args:
            score: Velocity score to classify
            percentiles: Calculated percentile thresholds

        Returns:
            Alert level: 'noise' | 'weak' | 'moderate' | 'strong' | 'viral'
        """
        if score < percentiles["P10"]:
            return "noise"
        elif score < percentiles["P50"]:
            return "weak"
        elif score < percentiles["P90"]:
            return "moderate"
        elif score < percentiles["P99"]:
            return "strong"
        else:
            return "viral"

    def get_threshold_description(self, percentiles: Dict[str, float]) -> Dict[str, str]:
        """
        Get human-readable threshold descriptions.

        Useful for dashboard display and user education.
        """
        return {
            "noise": f"Below {percentiles['P10']:.0f} - Ignored",
            "weak": f"{percentiles['P10']:.0f}-{percentiles['P50']:.0f} - Log only",
            "moderate": f"{percentiles['P50']:.0f}-{percentiles['P90']:.0f} - Trending list",
            "strong": f"{percentiles['P90']:.0f}-{percentiles['P99']:.0f} - Alert eligible",
            "viral": f"Above {percentiles['P99']:.0f} - Immediate alert"
        }


def calculate_doubling_time(growth_rate: float) -> float:
    """
    Calculate doubling time using Rule of 70.

    This is a simple utility function for quick calculations.

    Args:
        growth_rate: Percentage growth rate (e.g., 50 for 50%)

    Returns:
        Hours to double, or infinity if growth rate is <= 0
    """
    if growth_rate <= 0:
        return float('inf')
    return 70 / growth_rate


def classify_growth_rate(growth_rate: float) -> str:
    """
    Classify growth rate into descriptive category.

    Based on TECH_FEASIBILITY.md thresholds.

    Args:
        growth_rate: Percentage growth rate per hour

    Returns:
        Classification: 'slow' | 'moderate' | 'fast' | 'explosive'
    """
    if growth_rate < 0.5:
        return "slow"
    elif growth_rate < 1.0:
        return "moderate"
    elif growth_rate < 2.0:
        return "fast"
    else:
        return "explosive"
