"""
Lifecycle Manager

Manages trend lifecycle state transitions.

State Machine:
    +----------+     velocity>80,      +---------+
    | emerging |---------------------->| peaking |
    +----------+     accel<0           +---------+
         |                                  |
         | velocity<threshold               | saturation>70
         | OR saturation>90                 | OR accel<-0.1
         v                                  v
    +----------+                     +----------+
    | expired  |<--------------------| saturated|
    +----------+     velocity<20     +----------+
                     OR saturation>90

Transition Rules:
- emerging -> peaking: velocity > 80 AND acceleration < 0 (passed peak growth)
- peaking -> saturated: saturation > 70 OR acceleration < -0.1
- saturated -> expired: velocity < 20 OR saturation > 90
- emerging -> expired: velocity drops below threshold before peaking
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass

from detection.velocity_engine import VelocityResult
from detection.saturation import SaturationResult
from detection.models import TrendStatus
from detection.config import settings
from detection.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class LifecycleTransition:
    """Record of a status transition."""

    from_status: TrendStatus
    to_status: TrendStatus
    reason: str
    velocity_at_transition: int
    saturation_at_transition: int


class LifecycleManager:
    """
    Manages trend lifecycle state machine.

    The lifecycle follows a predictable pattern:
    1. EMERGING: Trend just detected, growing
    2. PEAKING: Maximum velocity reached, starting to decelerate
    3. SATURATED: Growth slowing, mainstream adoption
    4. EXPIRED: No longer relevant

    The state machine ensures consistent transitions and provides
    visibility into expected next states for UI display.
    """

    # Transition thresholds from settings
    EMERGING_TO_PEAKING_VELOCITY: int = 80
    PEAKING_TO_SATURATED_SATURATION: int = 70
    SATURATED_TO_EXPIRED_VELOCITY: int = 20
    SATURATED_TO_EXPIRED_SATURATION: int = 90
    EMERGING_TO_EXPIRED_SATURATION: int = 90

    def __init__(self):
        """Initialize lifecycle manager with configuration thresholds."""
        self.emerging_to_peaking_velocity = settings.emerging_to_peaking_velocity
        self.peaking_to_saturated_saturation = settings.peaking_to_saturated_saturation
        self.saturated_to_expired_velocity = settings.saturated_to_expired_velocity
        self.saturated_to_expired_saturation = settings.saturated_to_expired_saturation
        self.emerging_to_expired_saturation = settings.emerging_to_expired_saturation

    def determine_status(
        self,
        current_status: TrendStatus,
        velocity: VelocityResult,
        saturation: SaturationResult
    ) -> TrendStatus:
        """
        Determine new status based on current state and metrics.

        This is the main entry point for status evaluation. It delegates
        to state-specific evaluation methods.

        Args:
            current_status: Current trend status
            velocity: Current velocity calculation result
            saturation: Current saturation calculation result

        Returns:
            New (or unchanged) status
        """
        if current_status == TrendStatus.EMERGING:
            return self._evaluate_emerging(velocity, saturation)
        elif current_status == TrendStatus.PEAKING:
            return self._evaluate_peaking(velocity, saturation)
        elif current_status == TrendStatus.SATURATED:
            return self._evaluate_saturated(velocity, saturation)
        else:
            # EXPIRED is terminal state - no transitions out
            return TrendStatus.EXPIRED

    def _evaluate_emerging(
        self,
        velocity: VelocityResult,
        saturation: SaturationResult
    ) -> TrendStatus:
        """
        Evaluate transition from EMERGING state.

        Possible transitions:
        - EMERGING -> PEAKING: High velocity with deceleration
        - EMERGING -> EXPIRED: Low velocity or high saturation without growth

        Args:
            velocity: Current velocity calculation
            saturation: Current saturation calculation

        Returns:
            New status (PEAKING, EXPIRED, or stay EMERGING)
        """
        # Check for direct expiration (trend never took off)
        # This happens if saturation is very high without exponential growth
        if saturation.score > self.emerging_to_expired_saturation:
            if not velocity.is_exponential or velocity.score < 20:
                logger.info(
                    "lifecycle_transition",
                    from_status="emerging",
                    to_status="expired",
                    reason="High saturation without exponential growth"
                )
                return TrendStatus.EXPIRED

        # Check for low velocity without exponential growth
        if velocity.score < 20 and not velocity.is_exponential:
            # Only expire if we've had enough time to evaluate
            if velocity.data_points >= 5:
                logger.info(
                    "lifecycle_transition",
                    from_status="emerging",
                    to_status="expired",
                    reason="Low velocity without exponential growth after sufficient data"
                )
                return TrendStatus.EXPIRED

        # Check for transition to peaking
        # Need high velocity AND deceleration (passed peak growth rate)
        if velocity.score > self.emerging_to_peaking_velocity:
            if velocity.acceleration < 0:
                logger.info(
                    "lifecycle_transition",
                    from_status="emerging",
                    to_status="peaking",
                    reason="High velocity with deceleration",
                    velocity_score=velocity.score,
                    acceleration=velocity.acceleration
                )
                return TrendStatus.PEAKING

        # Stay in emerging state
        return TrendStatus.EMERGING

    def _evaluate_peaking(
        self,
        velocity: VelocityResult,
        saturation: SaturationResult
    ) -> TrendStatus:
        """
        Evaluate transition from PEAKING state.

        Possible transitions:
        - PEAKING -> SATURATED: High saturation or significant deceleration

        Once a trend is peaking, it typically transitions to saturated
        relatively quickly (within hours to a day).

        Args:
            velocity: Current velocity calculation
            saturation: Current saturation calculation

        Returns:
            New status (SATURATED or stay PEAKING)
        """
        # Check for transition to saturated
        # Triggered by high saturation or significant deceleration
        if saturation.score > self.peaking_to_saturated_saturation:
            logger.info(
                "lifecycle_transition",
                from_status="peaking",
                to_status="saturated",
                reason="High saturation",
                saturation_score=saturation.score
            )
            return TrendStatus.SATURATED

        # Significant deceleration indicates the trend is maturing
        if velocity.acceleration < -0.1:
            logger.info(
                "lifecycle_transition",
                from_status="peaking",
                to_status="saturated",
                reason="Significant deceleration",
                acceleration=velocity.acceleration
            )
            return TrendStatus.SATURATED

        # Stay in peaking state
        return TrendStatus.PEAKING

    def _evaluate_saturated(
        self,
        velocity: VelocityResult,
        saturation: SaturationResult
    ) -> TrendStatus:
        """
        Evaluate transition from SATURATED state.

        Possible transitions:
        - SATURATED -> EXPIRED: Very low velocity or very high saturation

        A saturated trend eventually expires when interest wanes.

        Args:
            velocity: Current velocity calculation
            saturation: Current saturation calculation

        Returns:
            New status (EXPIRED or stay SATURATED)
        """
        # Check for transition to expired
        # Triggered by very low velocity or very high saturation
        if velocity.score < self.saturated_to_expired_velocity:
            logger.info(
                "lifecycle_transition",
                from_status="saturated",
                to_status="expired",
                reason="Low velocity",
                velocity_score=velocity.score
            )
            return TrendStatus.EXPIRED

        if saturation.score > self.saturated_to_expired_saturation:
            logger.info(
                "lifecycle_transition",
                from_status="saturated",
                to_status="expired",
                reason="Very high saturation",
                saturation_score=saturation.score
            )
            return TrendStatus.EXPIRED

        # Stay in saturated state
        return TrendStatus.SATURATED

    def get_expected_transition(
        self,
        status: TrendStatus,
        velocity: VelocityResult,
        saturation: SaturationResult
    ) -> Optional[str]:
        """
        Get hint about expected next transition.

        Useful for UI to show "trending towards X" indicators.
        This doesn't guarantee a transition, just indicates the
        likely direction based on current metrics.

        Args:
            status: Current trend status
            velocity: Current velocity calculation
            saturation: Current saturation calculation

        Returns:
            Expected next state name or None if terminal/expired
        """
        if status == TrendStatus.EMERGING:
            # Check if trending towards peaking
            if velocity.score > 60 and velocity.acceleration < 0:
                return "peaking"
            # Check if at risk of expiring
            if saturation.score > 70 and not velocity.is_exponential:
                return "expiring"
            return "growing"

        elif status == TrendStatus.PEAKING:
            # Peaking trends move towards saturation
            return "saturating"

        elif status == TrendStatus.SATURATED:
            # Saturated trends move towards expiry
            return "expiring"

        else:
            # EXPIRED is terminal
            return None

    def get_status_description(self, status: TrendStatus) -> str:
        """
        Get human-readable description for status.

        Args:
            status: Trend status

        Returns:
            Description string
        """
        descriptions = {
            TrendStatus.EMERGING: (
                "Trend is in early growth phase. "
                "High opportunity window for creators to participate."
            ),
            TrendStatus.PEAKING: (
                "Trend has reached peak velocity. "
                "Still good opportunity but window is closing."
            ),
            TrendStatus.SATURATED: (
                "Trend has reached mainstream adoption. "
                "Limited opportunity, consider unique angles."
            ),
            TrendStatus.EXPIRED: (
                "Trend is no longer relevant. "
                "Focus on newer emerging trends."
            )
        }
        return descriptions.get(status, "Unknown status")

    def should_record_peak_time(
        self,
        current_status: TrendStatus,
        new_status: TrendStatus
    ) -> bool:
        """
        Check if peak detection time should be recorded.

        Peak time is recorded when transitioning from EMERGING to PEAKING.

        Args:
            current_status: Current status before transition
            new_status: New status after evaluation

        Returns:
            True if peak time should be recorded
        """
        return (
            current_status == TrendStatus.EMERGING and
            new_status == TrendStatus.PEAKING
        )

    def get_transition_priority(
        self,
        from_status: TrendStatus,
        to_status: TrendStatus
    ) -> str:
        """
        Get priority level for a status transition.

        Useful for alert prioritization.

        Args:
            from_status: Status before transition
            to_status: Status after transition

        Returns:
            Priority: 'high' | 'medium' | 'low'
        """
        # Transition to peaking is high priority
        if to_status == TrendStatus.PEAKING:
            return "high"

        # Transition from peaking to saturated is medium
        if from_status == TrendStatus.PEAKING and to_status == TrendStatus.SATURATED:
            return "medium"

        # Early expiration is notable
        if from_status == TrendStatus.EMERGING and to_status == TrendStatus.EXPIRED:
            return "medium"

        # Other transitions are low priority
        return "low"
