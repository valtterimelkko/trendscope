"""
Trend Detection Engine

Core trend detection system that consumes video data from Redis queue
and identifies emerging trends using velocity calculation algorithms.

Components:
- Consumer: Processes video data from Redis queue
- VelocityEngine: Calculates exponential growth detection (R-squared > 0.85)
- TrendDetector: Identifies and manages trend records
- SaturationEngine: Calculates saturation scores (0-100%)
- LifecycleManager: Manages trend lifecycle states
- Repository: PostgreSQL persistence layer
"""

from detection.config import settings
from detection.models import (
    TrendType,
    TrendStatus,
    VideoData,
    VideoStats,
    VideoMusic,
    Trend,
    TrendVelocityHistory,
    TrendWithHistory,
)
from detection.velocity_engine import VelocityEngine, VelocityResult, AdaptiveThresholds
from detection.saturation import SaturationEngine, SaturationResult
from detection.lifecycle_manager import LifecycleManager
from detection.persistence import TrendRepository
from detection.trend_detector import TrendDetector
from detection.consumer import TrendConsumer

__all__ = [
    # Configuration
    "settings",
    # Models
    "TrendType",
    "TrendStatus",
    "VideoData",
    "VideoStats",
    "VideoMusic",
    "Trend",
    "TrendVelocityHistory",
    "TrendWithHistory",
    # Velocity
    "VelocityEngine",
    "VelocityResult",
    "AdaptiveThresholds",
    # Saturation
    "SaturationEngine",
    "SaturationResult",
    # Lifecycle
    "LifecycleManager",
    # Persistence
    "TrendRepository",
    # Detection
    "TrendDetector",
    # Consumer
    "TrendConsumer",
]
