# Stage 04: Trend Detection Engine

**Status:** Planned
**Estimated Duration:** 8-10 hours
**Assigned Agent:** Unassigned
**Last Updated:** 2026-02-17

---

## 1. Overview

This stage implements the core trend detection engine that consumes video data from the Redis queue and identifies emerging trends using velocity calculation algorithms. The engine calculates exponential growth patterns, determines saturation levels, and manages the complete trend lifecycle (emerging -> peaking -> saturated -> expired). This is the "brain" of the Trendscope platform, transforming raw video data into actionable trend intelligence.

**Delivers:**
- Consumer service that processes video data from Redis queue
- Velocity calculation engine with exponential growth detection (R-squared > 0.85)
- Doubling time analysis using the Rule of 70
- Adaptive percentile thresholds for dynamic alert levels
- Trend persistence logic to PostgreSQL database
- Saturation scoring algorithm (0-100%)
- Trend lifecycle state machine management
- Velocity history tracking for time-series analysis
- Internal API interfaces for trend queries

**Success Criteria:**
- [ ] Trends detected within 5 minutes of velocity threshold being crossed
- [ ] Velocity scores accurate (validated against sample data with known growth patterns)
- [ ] Exponential growth detection correctly identifies R-squared > 0.85 patterns
- [ ] Doubling time calculations accurate to within 10% of theoretical values
- [ ] Saturation calculation correctly reflects trend lifecycle stages
- [ ] Trend lifecycle transitions occur at appropriate thresholds
- [ ] Velocity history recorded at hourly intervals
- [ ] Consumer processes batches of 50+ videos efficiently
- [ ] No duplicate trend records for same platform_id + type combination

---

## 2. Dependencies

### Must Complete First
| Stage | Status | What We Need |
|-------|--------|--------------|
| Stage 03 | Planned | Redis queue with video metadata, consumer skeleton |
| Stage 01 | Planned | Database service layer, trends table schema |
| Redis | Required | Running instance with video data queue |
| PostgreSQL | Required | `trends` and `trend_velocity_history` tables created |

### Can Run In Parallel
- Stage 05 (Alert Pipeline): Can design alert schema while detection is built
- Stage 06 (Monitoring): Can define metrics schema in parallel

### Blocks These Stages
- Stage 05 (Alert Pipeline): Requires detected trends from this stage to trigger alerts
- Stage 06 (Monitoring): Needs trend metrics for observability dashboards

---

## 3. Technical Components

### 3.1 Trend Detection Architecture

```
+------------------+       +-------------------+       +------------------+
|    Redis Queue   |       |  Trend Detection  |       |   PostgreSQL     |
|  tiktok:videos   |------>|     Engine        |------>|     Database     |
|   72hr TTL       |       |   (Consumer)      |       |                  |
+------------------+       +-------------------+       +------------------+
        |                          |                          |
        v                          v                          v
+------------------+       +-------------------+       +------------------+
|   Video Data     |       |  Velocity Engine  |       |   trends table   |
|  (per video)     |       |  (Calculator)     |       |   + history      |
+------------------+       +-------------------+       +------------------+
                                   |
                                   v
                          +-------------------+
                          |  Lifecycle Mgr    |
                          |  (State Machine)  |
                          +-------------------+
                                   |
                                   v
                          +-------------------+
                          | Saturation Engine |
                          |   (Scoring)       |
                          +-------------------+
```

### 3.2 Directory Structure

```
/detection/
+-- __init__.py
+-- main.py                    # Entry point, orchestrates consumer
+-- config.py                  # Detection configuration loader
+-- consumer.py                # Redis consumer implementation
+-- velocity_engine.py         # Velocity calculation algorithms
+-- trend_detector.py          # Trend identification logic
+-- saturation_engine.py       # Saturation scoring
+-- lifecycle_manager.py       # Trend lifecycle state machine
+-- models.py                  # Pydantic models for trend data
+-- repository.py              # Database repository layer
+-- tests/
|   +-- __init__.py
|   +-- test_velocity_engine.py
|   +-- test_trend_detector.py
|   +-- test_saturation_engine.py
|   +-- test_lifecycle_manager.py
|   +-- test_consumer.py
|   +-- fixtures/
|       +-- sample_video_data.json
|       +-- sample_trend_data.json
+-- requirements.txt           # Python dependencies (numpy, scipy)
```

### 3.3 Consumer Implementation (consumer.py)

Consumes video data from Redis and dispatches to trend detector.

```python
import asyncio
import json
from typing import List
import redis.asyncio as redis
import asyncpg

from detection.config import settings
from detection.trend_detector import TrendDetector
from detection.models import VideoData
from detection.logging_config import get_logger

logger = get_logger(__name__)

class TrendConsumer:
    """Consumes video data from Redis and detects trends."""

    def __init__(
        self,
        redis_client: redis.Redis,
        db_pool: asyncpg.Pool,
        trend_detector: TrendDetector
    ):
        self.redis = redis_client
        self.db_pool = db_pool
        self.trend_detector = trend_detector
        self.running = False
        self.batch_size = settings.consumer_batch_size

    async def consume(self) -> None:
        """Main consumption loop - processes batches from Redis queue."""
        self.running = True
        logger.info("trend_consumer_started", batch_size=self.batch_size)

        while self.running:
            try:
                # Fetch batch from queue (non-blocking)
                batch = await self._fetch_batch()

                if not batch:
                    await asyncio.sleep(settings.consumer_idle_wait)
                    continue

                # Process each video in batch
                for video_json in batch:
                    try:
                        video = VideoData.model_validate_json(video_json)
                        await self.trend_detector.process_video(video)
                    except Exception as e:
                        logger.error("video_processing_error",
                                    video_id=video_json.get("id", "unknown"),
                                    error=str(e))

                # Remove processed items from queue
                await self.redis.ltrim(
                    "tiktok:videos",
                    len(batch),
                    -1
                )

                logger.info("batch_processed", count=len(batch))

            except Exception as e:
                logger.error("consumer_error", error=str(e))
                await asyncio.sleep(settings.consumer_error_wait)

    async def _fetch_batch(self) -> List[str]:
        """Fetch a batch of video data from Redis queue."""
        items = await self.redis.lrange("tiktok:videos", 0, self.batch_size - 1)
        return [item.decode("utf-8") for item in items]

    async def stop(self) -> None:
        """Gracefully stop the consumer."""
        self.running = False
        logger.info("trend_consumer_stopped")
```

### 3.4 Velocity Engine Implementation (velocity_engine.py)

Core velocity calculation using exponential growth detection.

```python
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
    4. Calculate growth rate and doubling time
    """

    # Configuration thresholds
    R_SQUARED_THRESHOLD = 0.85      # Exponential growth threshold
    MIN_DATA_POINTS = 3             # Minimum points for calculation
    MAX_DATA_POINTS = 168           # 7 days of hourly data

    def __init__(self):
        self.adaptive_thresholds = AdaptiveThresholds()

    def calculate_velocity(
        self,
        data_points: List[Tuple[datetime, int]]
    ) -> VelocityResult:
        """
        Calculate velocity from time-series data.

        Args:
            data_points: List of (timestamp, count) tuples

        Returns:
            VelocityResult with all calculated metrics
        """
        if len(data_points) < self.MIN_DATA_POINTS:
            return self._insufficient_data_result(len(data_points))

        # Sort by timestamp and extract arrays
        sorted_data = sorted(data_points, key=lambda x: x[0])
        timestamps, counts = zip(*sorted_data)

        # Convert timestamps to relative hours
        t0 = timestamps[0]
        times = np.array([(t - t0).total_seconds() / 3600 for t in timestamps])
        counts = np.array(counts, dtype=float)

        # Filter out zero/negative counts for log transformation
        valid_mask = counts > 0
        if np.sum(valid_mask) < self.MIN_DATA_POINTS:
            return self._insufficient_data_result(len(data_points))

        times = times[valid_mask]
        counts = counts[valid_mask]

        # Log-transform for exponential fitting: ln(V) = ln(V0) + r*t
        log_counts = np.log(counts)

        # Linear regression on log-transformed data
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            times, log_counts
        )

        r_squared = r_value ** 2
        growth_rate = slope * 100  # Convert to percentage per hour

        # Doubling time (Rule of 70)
        doubling_time = 70 / growth_rate if growth_rate > 0 else float('inf')

        # Calculate acceleration (second derivative)
        acceleration = self._calculate_acceleration(times, counts)

        # Determine if exponential growth
        is_exponential = r_squared > self.R_SQUARED_THRESHOLD

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

        return VelocityResult(
            score=velocity_score,
            growth_rate=round(growth_rate, 2),
            doubling_time=round(doubling_time, 2),
            r_squared=round(r_squared, 3),
            is_exponential=is_exponential,
            acceleration=round(acceleration, 4),
            confidence=round(confidence, 2),
            data_points=len(data_points),
            time_window_hours=round(times[-1] - times[0], 2)
        )

    def _calculate_score(
        self,
        growth_rate: float,
        r_squared: float,
        is_exponential: bool
    ) -> int:
        """
        Calculate 0-100 velocity score.

        Scoring logic:
        - Exponential growth (R-squared > 0.85): score = growth_rate, capped at 100
        - Linear/other growth: score = growth_rate * r_squared
        """
        if is_exponential and growth_rate > 50:
            # Exponential growth with high rate = high score
            return min(100, int(growth_rate))
        else:
            # Linear or weak growth = reduced score
            return min(100, int(growth_rate * r_squared))

    def _calculate_acceleration(
        self,
        times: np.ndarray,
        counts: np.ndarray
    ) -> float:
        """
        Calculate acceleration (second derivative).

        Positive acceleration = growth is accelerating
        Negative acceleration = growth is decelerating
        """
        if len(times) < 3:
            return 0.0

        # Calculate first derivative (velocity) at each point
        velocities = np.diff(counts) / np.diff(times)

        # Calculate second derivative (acceleration)
        if len(velocities) >= 2:
            accelerations = np.diff(velocities) / np.diff(times[:-1])
            return float(np.mean(accelerations))

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
        - Higher R-squared = higher confidence
        - Longer time window = higher confidence
        """
        # Base confidence from data points
        points_factor = min(1.0, data_points / 24)  # Max at 24 points

        # R-squared factor
        r_factor = r_squared

        # Time window factor (prefer 6-72 hour windows)
        if 6 <= time_window <= 72:
            window_factor = 1.0
        elif time_window < 6:
            window_factor = time_window / 6
        else:
            window_factor = max(0.5, 1.0 - (time_window - 72) / 168)

        return (points_factor * 0.3 + r_factor * 0.4 + window_factor * 0.3)

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

    Implements BERTrend-style self-adjusting thresholds.
    """

    def __init__(self, window_days: int = 7):
        self.window_days = window_days
        self.percentile_cache: Dict[str, Dict] = {}

    def calculate_percentiles(
        self,
        historical_scores: List[float]
    ) -> Dict[str, float]:
        """
        Calculate adaptive thresholds over rolling window.

        Returns:
            Dict with P10, P50, P90, P99 percentiles
        """
        if len(historical_scores) < 10:
            # Insufficient data, use defaults
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

        Returns:
            'noise' | 'weak' | 'moderate' | 'strong' | 'viral'
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
```

### 3.5 Trend Detector Implementation (trend_detector.py)

Identifies and persists trends from video data.

```python
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dataclasses import dataclass
import json

from detection.velocity_engine import VelocityEngine, VelocityResult
from detection.saturation_engine import SaturationEngine
from detection.lifecycle_manager import LifecycleManager, TrendStatus
from detection.models import VideoData, Trend, TrendType
from detection.repository import TrendRepository
from detection.logging_config import get_logger
from detection.config import settings

logger = get_logger(__name__)

@dataclass
class ExtractedTrend:
    """Trend extracted from video data."""
    type: TrendType
    platform_id: str
    name: str
    video: VideoData

class TrendDetector:
    """
    Processes video data and detects/updates trends.

    Flow:
    1. Extract potential trends (sound/hashtag) from video
    2. Aggregate data points for each trend
    3. Calculate velocity for each trend
    4. Persist significant trends to database
    5. Record velocity history
    """

    def __init__(
        self,
        repository: TrendRepository,
        velocity_engine: VelocityEngine,
        saturation_engine: SaturationEngine,
        lifecycle_manager: LifecycleManager
    ):
        self.repository = repository
        self.velocity_engine = velocity_engine
        self.saturation_engine = saturation_engine
        self.lifecycle_manager = lifecycle_manager
        self.trend_cache: Dict[str, List[tuple]] = {}  # In-memory aggregation

    async def process_video(self, video: VideoData) -> None:
        """
        Process a single video and update related trends.

        Args:
            video: Video data from scraper
        """
        # Extract trends from video
        trends = self._extract_trends(video)

        for trend in trends:
            await self._process_trend(trend)

    def _extract_trends(self, video: VideoData) -> List[ExtractedTrend]:
        """
        Extract potential trends from video data.

        Returns:
            List of extracted trends (sound + hashtags)
        """
        trends = []

        # Extract sound/music trend
        if video.music and video.music.id:
            trends.append(ExtractedTrend(
                type=TrendType.SOUND,
                platform_id=video.music.id,
                name=video.music.title or f"Sound {video.music.id}",
                video=video
            ))

        # Extract hashtag trends
        for hashtag in video.hashtags:
            trends.append(ExtractedTrend(
                type=TrendType.HASHTAG,
                platform_id=hashtag.lower(),
                name=f"#{hashtag}",
                video=video
            ))

        return trends

    async def _process_trend(self, trend: ExtractedTrend) -> None:
        """
        Process a single trend: aggregate data, calculate velocity, persist.
        """
        cache_key = f"{trend.type.value}:{trend.platform_id}"

        # Add current data point to cache
        data_point = (trend.video.scraped_at, trend.video.stats.play_count)

        if cache_key not in self.trend_cache:
            self.trend_cache[cache_key] = []

        self.trend_cache[cache_key].append(data_point)

        # Keep only last 168 data points (7 days of hourly data)
        if len(self.trend_cache[cache_key]) > 168:
            self.trend_cache[cache_key] = self.trend_cache[cache_key][-168:]

        # Get existing trend from database
        existing_trend = await self.repository.get_by_platform_id(
            trend.type,
            trend.platform_id
        )

        # Calculate velocity
        velocity = self.velocity_engine.calculate_velocity(
            self.trend_cache[cache_key]
        )

        # Only persist if velocity is significant
        if velocity.score < settings.trend_min_velocity_score:
            return

        # Calculate saturation
        saturation = self.saturation_engine.calculate(
            velocity,
            existing_trend,
            len(self.trend_cache[cache_key])
        )

        # Determine trend status
        if existing_trend:
            status = self.lifecycle_manager.determine_status(
                existing_trend.status,
                velocity,
                saturation
            )
            trend_record = await self._update_trend(
                existing_trend,
                velocity,
                saturation,
                status
            )
        else:
            status = TrendStatus.EMERGING
            trend_record = await self._create_trend(
                trend,
                velocity,
                saturation,
                status
            )

        # Record velocity history
        await self.repository.record_velocity_history(
            trend_id=trend_record.id,
            timestamp=datetime.utcnow(),
            video_count=self.trend_cache[cache_key][-1][1],
            velocity_score=velocity.score,
            growth_rate=velocity.growth_rate,
            saturation_percent=saturation.score
        )

        logger.info(
            "trend_processed",
            trend_id=str(trend_record.id),
            trend_name=trend_record.name,
            velocity_score=velocity.score,
            status=status.value
        )

    async def _create_trend(
        self,
        extracted: ExtractedTrend,
        velocity: VelocityResult,
        saturation,
        status: TrendStatus
    ) -> Trend:
        """Create new trend record in database."""
        trend = Trend(
            type=extracted.type,
            name=extracted.name,
            platform_id=extracted.platform_id,
            niche_id=None,  # Assigned by clustering (future enhancement)
            first_detected_at=datetime.utcnow(),
            peak_detected_at=None,
            status=status,
            velocity_score=velocity.score,
            saturation_percent=saturation.score,
            video_count_start=1,
            video_count_current=1,
            growth_rate=velocity.growth_rate,
            metadata={
                "initial_velocity": velocity.__dict__,
                "example_videos": [extracted.video.id]
            }
        )

        return await self.repository.create(trend)

    async def _update_trend(
        self,
        existing: Trend,
        velocity: VelocityResult,
        saturation,
        status: TrendStatus
    ) -> Trend:
        """Update existing trend record."""
        updates = {
            "velocity_score": velocity.score,
            "saturation_percent": saturation.score,
            "video_count_current": existing.video_count_current + 1,
            "growth_rate": velocity.growth_rate,
            "status": status,
            "updated_at": datetime.utcnow()
        }

        # Update peak time if transitioning to peaking
        if status == TrendStatus.PEAKING and existing.status != TrendStatus.PEAKING:
            updates["peak_detected_at"] = datetime.utcnow()

        return await self.repository.update(existing.id, updates)
```

### 3.6 Saturation Engine Implementation (saturation_engine.py)

Calculates saturation score (0-100%) based on trend lifecycle.

```python
from dataclasses import dataclass
from typing import Optional

from detection.velocity_engine import VelocityResult
from detection.lifecycle_manager import TrendStatus
from detection.models import Trend
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

    Saturation indicates how "used up" a trend is:
    - 0-30%: Early stage, high opportunity
    - 30-60%: Growth stage, still good opportunity
    - 60-80%: Mature stage, decreasing returns
    - 80-100%: Saturated, declining returns
    """

    # Saturation thresholds
    EARLY_THRESHOLD = 30
    GROWTH_THRESHOLD = 60
    MATURE_THRESHOLD = 80

    def calculate(
        self,
        velocity: VelocityResult,
        existing_trend: Optional[Trend],
        data_points: int
    ) -> SaturationResult:
        """
        Calculate saturation score for a trend.

        Factors:
        - Acceleration (positive = early, negative = late)
        - Time since detection (longer = more saturated)
        - Velocity score (very high = might be peaking)
        - Data point count (more data = more mature)
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
            acceleration_score * 0.30 +
            time_score * 0.25 +
            velocity_score * 0.25 +
            volume_score * 0.20
        )

        score = int(min(100, max(0, saturation)))
        stage = self._determine_stage(score)
        recommendation = self._get_recommendation(score, velocity.score)

        return SaturationResult(
            score=score,
            stage=stage,
            recommendation=recommendation
        )

    def _new_trend_saturation(self) -> SaturationResult:
        """Saturation for newly detected trend."""
        return SaturationResult(
            score=10,
            stage="early",
            recommendation="New trend - high opportunity window"
        )

    def _acceleration_to_saturation(self, acceleration: float) -> float:
        """
        Convert acceleration to saturation component.

        Positive acceleration = early stage = low saturation
        Negative acceleration = late stage = high saturation
        """
        if acceleration > 0.1:
            return 20  # Accelerating growth = early
        elif acceleration > 0:
            return 40  # Slight acceleration
        elif acceleration > -0.1:
            return 60  # Slight deceleration
        else:
            return 80  # Decelerating = late

    def _time_to_saturation(self, first_detected) -> float:
        """
        Convert time since detection to saturation.

        Longer existence = higher saturation
        """
        from datetime import datetime

        hours_since = (datetime.utcnow() - first_detected).total_seconds() / 3600

        if hours_since < 6:
            return 15
        elif hours_since < 24:
            return 30
        elif hours_since < 72:
            return 50
        elif hours_since < 168:
            return 70
        else:
            return 85

    def _velocity_to_saturation(
        self,
        velocity_score: int,
        is_exponential: bool
    ) -> float:
        """
        Convert velocity score to saturation.

        Very high velocity might indicate peaking
        """
        if velocity_score > 90 and is_exponential:
            return 75  # High velocity + exponential = might be peaking
        elif velocity_score > 70:
            return 50
        elif velocity_score > 50:
            return 35
        else:
            return 25

    def _volume_to_saturation(self, data_points: int) -> float:
        """
        Convert data point volume to saturation.

        More data points = more people using = more saturated
        """
        if data_points < 10:
            return 15
        elif data_points < 50:
            return 30
        elif data_points < 100:
            return 50
        elif data_points < 500:
            return 70
        else:
            return 85

    def _determine_stage(self, score: int) -> str:
        """Determine trend stage from saturation score."""
        if score < self.EARLY_THRESHOLD:
            return "early"
        elif score < self.GROWTH_THRESHOLD:
            return "growth"
        elif score < self.MATURE_THRESHOLD:
            return "mature"
        else:
            return "decline"

    def _get_recommendation(self, saturation: int, velocity: int) -> str:
        """Generate action recommendation."""
        if saturation < 30:
            return "Prime opportunity - jump on this trend now"
        elif saturation < 50:
            return "Good opportunity - still room to grow"
        elif saturation < 70:
            return "Moderate opportunity - act quickly"
        elif saturation < 85:
            return "Late stage - consider if unique angle available"
        else:
            return "Saturated - may not yield significant returns"
```

### 3.7 Lifecycle Manager Implementation (lifecycle_manager.py)

Manages trend lifecycle state transitions.

```python
from enum import Enum
from typing import Optional
from dataclasses import dataclass

from detection.velocity_engine import VelocityResult
from detection.saturation_engine import SaturationResult
from detection.logging_config import get_logger

logger = get_logger(__name__)

class TrendStatus(Enum):
    """Trend lifecycle states."""
    EMERGING = "emerging"      # Just detected, early growth
    PEAKING = "peaking"        # Maximum velocity
    SATURATED = "saturated"    # Growth slowing, mainstream
    EXPIRED = "expired"        # No longer relevant

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

    State Transitions:
    emerging -> peaking: velocity > 80 AND acceleration < 0
    peaking -> saturated: saturation > 70 OR acceleration < -0.1
    saturated -> expired: velocity < 20 OR saturation > 90
    emerging -> expired: velocity drops below threshold before peaking

    State Machine Diagram:

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
    """

    # Transition thresholds
    EMERGING_TO_PEAKING_VELOCITY = 80
    PEAKING_TO_SATURATED_SATURATION = 70
    SATURATED_TO_EXPIRED_VELOCITY = 20
    SATURATED_TO_EXPIRED_SATURATION = 90
    EMERGING_TO_EXPIRED_SATURATION = 90

    def determine_status(
        self,
        current_status: TrendStatus,
        velocity: VelocityResult,
        saturation: SaturationResult
    ) -> TrendStatus:
        """
        Determine new status based on current state and metrics.

        Args:
            current_status: Current trend status
            velocity: Current velocity calculation
            saturation: Current saturation calculation

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
            # Expired is terminal state
            return TrendStatus.EXPIRED

    def _evaluate_emerging(
        self,
        velocity: VelocityResult,
        saturation: SaturationResult
    ) -> TrendStatus:
        """Evaluate transition from EMERGING state."""
        # Check for direct expiration (never took off)
        if (saturation.score > self.EMERGING_TO_EXPIRED_SATURATION or
            (velocity.score < 20 and not velocity.is_exponential)):
            logger.info(
                "lifecycle_transition",
                from_status="emerging",
                to_status="expired",
                reason="Low velocity or high saturation without growth"
            )
            return TrendStatus.EXPIRED

        # Check for transition to peaking
        if (velocity.score > self.EMERGING_TO_PEAKING_VELOCITY and
            velocity.acceleration < 0):  # Decelerating = passed peak growth
            logger.info(
                "lifecycle_transition",
                from_status="emerging",
                to_status="peaking",
                reason="High velocity with deceleration"
            )
            return TrendStatus.PEAKING

        return TrendStatus.EMERGING

    def _evaluate_peaking(
        self,
        velocity: VelocityResult,
        saturation: SaturationResult
    ) -> TrendStatus:
        """Evaluate transition from PEAKING state."""
        # Check for transition to saturated
        if (saturation.score > self.PEAKING_TO_SATURATED_SATURATION or
            velocity.acceleration < -0.1):
            logger.info(
                "lifecycle_transition",
                from_status="peaking",
                to_status="saturated",
                reason="High saturation or significant deceleration"
            )
            return TrendStatus.SATURATED

        return TrendStatus.PEAKING

    def _evaluate_saturated(
        self,
        velocity: VelocityResult,
        saturation: SaturationResult
    ) -> TrendStatus:
        """Evaluate transition from SATURATED state."""
        # Check for transition to expired
        if (velocity.score < self.SATURATED_TO_EXPIRED_VELOCITY or
            saturation.score > self.SATURATED_TO_EXPIRED_SATURATION):
            logger.info(
                "lifecycle_transition",
                from_status="saturated",
                to_status="expired",
                reason="Low velocity or very high saturation"
            )
            return TrendStatus.EXPIRED

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
        """
        if status == TrendStatus.EMERGING:
            if velocity.acceleration < 0:
                return "peaking"
            return "growing"
        elif status == TrendStatus.PEAKING:
            return "saturating"
        elif status == TrendStatus.SATURATED:
            return "expiring"
        else:
            return None
```

### 3.8 Data Models (models.py)

Pydantic models for trend data structures.

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid

class TrendType(str, Enum):
    """Type of trend."""
    SOUND = "sound"
    HASHTAG = "hashtag"
    FORMAT = "format"

class TrendStatus(str, Enum):
    """Trend lifecycle status."""
    EMERGING = "emerging"
    PEAKING = "peaking"
    SATURATED = "saturated"
    EXPIRED = "expired"

class VideoStats(BaseModel):
    """Video engagement statistics."""
    play_count: int = Field(..., alias="playCount")
    digg_count: int = Field(..., alias="diggCount")
    share_count: int = Field(..., alias="shareCount")
    comment_count: int = Field(..., alias="commentCount")

class VideoMusic(BaseModel):
    """Music/sound information."""
    id: Optional[str] = None
    title: Optional[str] = None
    author_name: Optional[str] = None

class VideoData(BaseModel):
    """Video metadata from scraper."""
    id: str
    desc: Optional[str] = None
    create_time: int = Field(..., alias="createTime")
    stats: VideoStats
    author: Dict[str, Any]
    music: Optional[VideoMusic] = None
    hashtags: List[str] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class Trend(BaseModel):
    """Detected trend record."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    type: TrendType
    name: str
    platform_id: str
    niche_id: Optional[uuid.UUID] = None
    first_detected_at: datetime
    peak_detected_at: Optional[datetime] = None
    status: TrendStatus = TrendStatus.EMERGING
    velocity_score: int = Field(..., ge=0, le=100)
    saturation_percent: int = Field(..., ge=0, le=100)
    video_count_start: int
    video_count_current: int
    growth_rate: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TrendVelocityHistory(BaseModel):
    """Velocity history record for time-series analysis."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    trend_id: uuid.UUID
    timestamp: datetime
    video_count: int
    velocity_score: Optional[int] = None
    growth_rate: Optional[float] = None
    saturation_percent: Optional[int] = None

class TrendWithHistory(BaseModel):
    """Trend with velocity history for API responses."""
    trend: Trend
    velocity_history: List[TrendVelocityHistory] = Field(default_factory=list)
```

### 3.9 Repository Implementation (repository.py)

Database access layer for trends.

```python
import asyncpg
from typing import Optional, List
from datetime import datetime
import uuid
import json

from detection.models import Trend, TrendType, TrendStatus, TrendVelocityHistory
from detection.logging_config import get_logger

logger = get_logger(__name__)

class TrendRepository:
    """Database repository for trend operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_by_platform_id(
        self,
        trend_type: TrendType,
        platform_id: str
    ) -> Optional[Trend]:
        """Get trend by type and platform ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM trends
                WHERE type = $1 AND platform_id = $2
                """,
                trend_type.value,
                platform_id
            )

            if row:
                return self._row_to_trend(row)
            return None

    async def get_by_id(self, trend_id: uuid.UUID) -> Optional[Trend]:
        """Get trend by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM trends WHERE id = $1",
                trend_id
            )

            if row:
                return self._row_to_trend(row)
            return None

    async def create(self, trend: Trend) -> Trend:
        """Create new trend record."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO trends (
                    id, type, name, platform_id, niche_id,
                    first_detected_at, peak_detected_at, status,
                    velocity_score, saturation_percent,
                    video_count_start, video_count_current,
                    growth_rate, metadata, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                ON CONFLICT (type, platform_id) DO NOTHING
                RETURNING *
                """,
                trend.id,
                trend.type.value,
                trend.name,
                trend.platform_id,
                trend.niche_id,
                trend.first_detected_at,
                trend.peak_detected_at,
                trend.status.value,
                trend.velocity_score,
                trend.saturation_percent,
                trend.video_count_start,
                trend.video_count_current,
                trend.growth_rate,
                json.dumps(trend.metadata),
                trend.created_at,
                trend.updated_at
            )

            if row:
                logger.info("trend_created", trend_id=str(trend.id), name=trend.name)
                return self._row_to_trend(row)

            # If conflict, return existing
            return await self.get_by_platform_id(trend.type, trend.platform_id)

    async def update(
        self,
        trend_id: uuid.UUID,
        updates: dict
    ) -> Trend:
        """Update trend record."""
        async with self.pool.acquire() as conn:
            # Build dynamic update query
            set_clauses = []
            values = [trend_id]
            param_idx = 2

            for key, value in updates.items():
                if key == "status" and isinstance(value, TrendStatus):
                    value = value.value
                set_clauses.append(f"{key} = ${param_idx}")
                values.append(value)
                param_idx += 1

            query = f"""
                UPDATE trends
                SET {', '.join(set_clauses)}
                WHERE id = $1
                RETURNING *
            """

            row = await conn.fetchrow(query, *values)
            return self._row_to_trend(row)

    async def record_velocity_history(
        self,
        trend_id: uuid.UUID,
        timestamp: datetime,
        video_count: int,
        velocity_score: int,
        growth_rate: float,
        saturation_percent: int
    ) -> None:
        """Record velocity history for time-series analysis."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO trend_velocity_history (
                    trend_id, timestamp, video_count,
                    velocity_score, growth_rate, saturation_percent
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                trend_id,
                timestamp,
                video_count,
                velocity_score,
                growth_rate,
                saturation_percent
            )

    async def get_velocity_history(
        self,
        trend_id: uuid.UUID,
        hours: int = 24
    ) -> List[TrendVelocityHistory]:
        """Get velocity history for a trend."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM trend_velocity_history
                WHERE trend_id = $1
                AND timestamp > NOW() - INTERVAL '1 hour' * $2
                ORDER BY timestamp ASC
                """,
                trend_id,
                hours
            )

            return [
                TrendVelocityHistory(
                    id=row["id"],
                    trend_id=row["trend_id"],
                    timestamp=row["timestamp"],
                    video_count=row["video_count"],
                    velocity_score=row["velocity_score"],
                    growth_rate=row["growth_rate"],
                    saturation_percent=row["saturation_percent"]
                )
                for row in rows
            ]

    def _row_to_trend(self, row: asyncpg.Record) -> Trend:
        """Convert database row to Trend model."""
        return Trend(
            id=row["id"],
            type=TrendType(row["type"]),
            name=row["name"],
            platform_id=row["platform_id"],
            niche_id=row["niche_id"],
            first_detected_at=row["first_detected_at"],
            peak_detected_at=row["peak_detected_at"],
            status=TrendStatus(row["status"]),
            velocity_score=row["velocity_score"],
            saturation_percent=row["saturation_percent"],
            video_count_start=row["video_count_start"],
            video_count_current=row["video_count_current"],
            growth_rate=float(row["growth_rate"]),
            metadata=row["metadata"] or {},
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
```

### 3.10 Configuration (config.py)

Environment-based configuration for detection service.

```python
from pydantic_settings import BaseSettings
from typing import Optional

class DetectionSettings(BaseSettings):
    """Detection engine configuration."""

    # Database
    database_url: str = "postgresql://localhost/trendscope"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Consumer
    consumer_batch_size: int = 50
    consumer_idle_wait: float = 5.0  # seconds
    consumer_error_wait: float = 30.0  # seconds

    # Velocity thresholds
    trend_min_velocity_score: int = 30  # Minimum to persist
    velocity_r_squared_threshold: float = 0.85
    velocity_min_data_points: int = 3

    # Lifecycle thresholds
    emerging_to_peaking_velocity: int = 80
    peaking_to_saturated_saturation: int = 70
    saturated_to_expired_velocity: int = 20
    saturated_to_expired_saturation: int = 90

    # History
    velocity_history_retention_hours: int = 168  # 7 days

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = DetectionSettings()
```

---

## 4. API Contracts

### Internal Service Interfaces

These are internal Python interfaces used by other stages, not HTTP endpoints.

#### TrendRepository Interface

```python
# Used by Stage 05 (Alert Pipeline) and Stage 01 (API Core)

async def get_by_platform_id(trend_type: TrendType, platform_id: str) -> Optional[Trend]:
    """Get trend by type and platform ID."""

async def get_by_id(trend_id: uuid.UUID) -> Optional[Trend]:
    """Get trend by ID."""

async def get_velocity_history(trend_id: uuid.UUID, hours: int = 24) -> List[TrendVelocityHistory]:
    """Get velocity history for time-series display."""
```

#### VelocityEngine Interface

```python
# Used for trend detection and can be queried for analysis

def calculate_velocity(data_points: List[Tuple[datetime, int]]) -> VelocityResult:
    """
    Calculate velocity from time-series data.

    Returns: VelocityResult with score, growth_rate, doubling_time, r_squared, etc.
    """
```

#### LifecycleManager Interface

```python
# Used to determine and display trend status

def determine_status(
    current_status: TrendStatus,
    velocity: VelocityResult,
    saturation: SaturationResult
) -> TrendStatus:
    """Determine new status based on metrics."""

def get_expected_transition(
    status: TrendStatus,
    velocity: VelocityResult,
    saturation: SaturationResult
) -> Optional[str]:
    """Get hint about expected next transition."""
```

---

## 5. Database Schema Changes

This stage populates existing tables defined in the initial schema but may add indexes for performance.

### Tables Populated

| Table | Purpose | Records Created By |
|-------|---------|-------------------|
| `trends` | Detected trends | TrendDetector._create_trend() |
| `trend_velocity_history` | Velocity snapshots | TrendRepository.record_velocity_history() |

### Recommended Indexes

```sql
-- Optimize velocity history queries
CREATE INDEX IF NOT EXISTS idx_trend_velocity_history_trend_time
ON public.trend_velocity_history(trend_id, timestamp DESC);

-- Optimize trend lookups by status
CREATE INDEX IF NOT EXISTS idx_trends_status_detected
ON public.trends(status, first_detected_at DESC);

-- Optimize trend lookups by velocity
CREATE INDEX IF NOT EXISTS idx_trends_velocity_status
ON public.trends(velocity_score DESC, status)
WHERE status IN ('emerging', 'peaking');
```

### Redis Keys Used

| Key Pattern | Type | TTL | Purpose |
|-------------|------|-----|---------|
| `tiktok:videos` | List | 72h | Source queue (Stage 03) |
| `detection:trend:{type}:{platform_id}` | String | 72h | Trend aggregation cache |

---

## 6. Testing Requirements

### Unit Tests

| Test | What It Validates |
|------|------------------|
| `test_velocity_calculation_exponential` | Correctly calculates R-squared for exponential growth |
| `test_velocity_calculation_linear` | Correctly handles linear (non-exponential) growth |
| `test_velocity_calculation_insufficient_data` | Returns zero score for insufficient data |
| `test_doubling_time_calculation` | Rule of 70 doubling time accurate |
| `test_acceleration_calculation` | Second derivative correctly calculated |
| `test_saturation_early_stage` | New trends have low saturation |
| `test_saturation_late_stage` | Mature trends have high saturation |
| `test_saturation_recommendation` | Recommendations appropriate to stage |
| `test_lifecycle_emerging_to_peaking` | Correct transition at velocity threshold |
| `test_lifecycle_peaking_to_saturated` | Correct transition at saturation threshold |
| `test_lifecycle_saturated_to_expired` | Correct transition at low velocity |
| `test_trend_extraction_sound` | Sound correctly extracted from video |
| `test_trend_extraction_hashtag` | Hashtags correctly extracted from video |
| `test_deduplication` | Same trend not created twice |

### Integration Tests

| Test | What It Validates |
|------|------------------|
| `test_consumer_batch_processing` | Consumer processes batch correctly |
| `test_trend_persistence` | Trend correctly persisted to database |
| `test_velocity_history_recording` | History correctly recorded |
| `test_full_detection_pipeline` | End-to-end: video -> trend -> history |
| `test_redis_connection` | Consumer connects to Redis |
| `test_database_connection` | Repository connects to PostgreSQL |

### Manual Verification

- [ ] Run consumer for 1 hour with sample video data
- [ ] Verify trends created in database with correct velocity scores
- [ ] Verify velocity history recorded at expected intervals
- [ ] Check saturation scores increase over time for same trend
- [ ] Verify lifecycle transitions occur at thresholds
- [ ] Validate R-squared calculation against known exponential data

---

## 7. Critical Constraints

**DO NOT:**
- Create duplicate trend records (use unique constraint on type + platform_id)
- Persist trends with velocity score below threshold (wastes storage)
- Run velocity calculation with fewer than 3 data points
- Store raw video data in PostgreSQL (only in Redis with TTL)
- Block consumer on slow database operations (use async)
- Skip velocity history recording (needed for time-series charts)

**MUST:**
- Use exponential growth detection with R-squared > 0.85 threshold
- Calculate doubling time using Rule of 70
- Update trend status via LifecycleManager only
- Record velocity history at each trend update
- Handle database connection errors gracefully
- Use structured logging with correlation IDs
- Validate video data before processing

**ALGORITHM CONSTRAINTS:**
- R-squared threshold: 0.85 for exponential classification
- Minimum data points: 3 for velocity calculation
- Maximum data points: 168 (7 days of hourly data)
- Velocity score range: 0-100 (integer)
- Saturation range: 0-100 (integer)

---

## 8. Progress Log

*Updated by implementing agent during work.*

### [Date] - [Time]
- **Completed:** [What was done]
- **Next:** [What's planned]
- **Blockers:** [Issues or "None"]

---

## 9. Issues & Blockers

*Document any escalations here.*

### [Issue Title] - [Status: Open/Resolved]

**Date:** [When discovered]
**Severity:** Blocker | Warning

**Description:**
[Clear description of the issue]

**Attempts Made:**
1. [Attempt 1]: [Result]
2. [Attempt 2]: [Result]
3. [Attempt 3]: [Result]

**Error Logs:**
```
[Relevant error output]
```

**Resolution:**
[How it was resolved, or "Escalated to Co-CEO"]

---

## 10. Completion Checklist

- [ ] All components built per Section 3
  - [ ] consumer.py - Redis consumer implementation
  - [ ] velocity_engine.py - Velocity calculation algorithms
  - [ ] trend_detector.py - Trend identification logic
  - [ ] saturation_engine.py - Saturation scoring
  - [ ] lifecycle_manager.py - Trend state machine
  - [ ] models.py - Pydantic data models
  - [ ] repository.py - Database repository layer
  - [ ] config.py - Configuration loader
  - [ ] main.py - Entry point
- [ ] Internal API contracts implemented per Section 4
  - [ ] TrendRepository interface
  - [ ] VelocityEngine interface
  - [ ] LifecycleManager interface
- [ ] Database changes applied per Section 5
  - [ ] Trends populated correctly
  - [ ] Velocity history recorded
  - [ ] Indexes created for performance
- [ ] All tests passing per Section 6
  - [ ] Unit tests pass
  - [ ] Integration tests pass
- [ ] All constraints followed per Section 7
- [ ] Progress log updated per Section 8
- [ ] Success criteria met (Section 1)
  - [ ] Detection within 5 minutes
  - [ ] Velocity scores accurate
  - [ ] Exponential detection works
  - [ ] Doubling time accurate
  - [ ] Saturation reflects lifecycle
  - [ ] Lifecycle transitions correct
- [ ] Verified using `verification-before-completion` skill

**Stage Completed:** [Date] | **Final Status:** [Complete/Blocked]

---

## 11. Reference Documents

| Document | Path | Purpose |
|----------|------|---------|
| Technical PRD | `docs/Project-Technical-Architecture.md` | System architecture |
| Technical Feasibility | `background_files/TECH_FEASIBILITY.md` | Algorithm reference (Section 2) |
| Stage 03 Architecture | `docs/stages/stage-03-scraper-integration.md` | Scraper/Redis integration |
| Progress Tracker | `PROGRESS.md` | Current project state |

---

## 12. Velocity Calculation Algorithm Reference

From `background_files/TECH_FEASIBILITY.md` Section 2:

### Exponential Growth Detection

```
Formula: V(t) = V0 * e^(rt)

Where:
- V(t) = volume at time t
- V0 = initial volume
- r = growth rate
- t = time

Implementation:
1. Take log of volume measurements: ln(V(t))
2. Fit linear regression to log-transformed data
3. Calculate R-squared (coefficient of determination)
4. If R-squared > 0.85, growth is exponential
5. Extract growth rate r from slope

Thresholds:
- r > 0.5 (50% growth rate) = Early warning
- r > 1.0 (100% growth rate) = High priority alert
- r > 2.0 (200% growth rate) = Critical alert
```

### Doubling Time (Rule of 70)

```
Formula: T_double = 70 / growth_rate_percentage

Interpretation:
- Doubling time < 1 hour = Viral momentum
- Doubling time < 30 minutes = Explosive growth
- Doubling time > 6 hours = Slow burn trend
```

### Adaptive Percentile Thresholds

```
Percentile | Alert Level | Action
-----------|-------------|--------
< P10      | Noise       | Ignore
P10-P50    | Weak Signal | Log only
P50-P90    | Moderate    | Trending list
P90-P99    | Strong      | Alert eligible
> P99      | Viral       | Immediate alert
```

---

*Document Version: 1.0*
*Last Updated: 2026-02-17*
