"""
Trend Detector

Core trend detection logic that processes video data and identifies trends.
Coordinates between velocity engine, saturation engine, and lifecycle manager.

Flow:
1. Extract potential trends (sound/hashtag) from video
2. Aggregate data points for each trend
3. Calculate velocity for each trend
4. Persist significant trends to database
5. Record velocity history
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

from detection.velocity_engine import VelocityEngine, VelocityResult
from detection.saturation import SaturationEngine, SaturationResult
from detection.lifecycle_manager import LifecycleManager
from detection.persistence import TrendRepository
from detection.models import (
    VideoData,
    Trend,
    TrendType,
    TrendStatus,
    ExtractedTrend
)
from detection.config import settings
from detection.logging_config import get_logger

logger = get_logger(__name__)


class TrendDetector:
    """
    Processes video data and detects/updates trends.

    This is the main coordinator for trend detection, bringing together:
    - VelocityEngine: Calculates growth metrics
    - SaturationEngine: Calculates saturation scores
    - LifecycleManager: Manages trend lifecycle states
    - TrendRepository: Persists trends to database

    The detector maintains an in-memory cache of data points for
    each trend to enable velocity calculation. This cache is bounded
    to prevent memory issues.
    """

    def __init__(
        self,
        repository: TrendRepository,
        velocity_engine: Optional[VelocityEngine] = None,
        saturation_engine: Optional[SaturationEngine] = None,
        lifecycle_manager: Optional[LifecycleManager] = None
    ):
        """
        Initialize trend detector.

        Args:
            repository: Database repository for persistence
            velocity_engine: Optional custom velocity engine
            saturation_engine: Optional custom saturation engine
            lifecycle_manager: Optional custom lifecycle manager
        """
        self.repository = repository
        self.velocity_engine = velocity_engine or VelocityEngine()
        self.saturation_engine = saturation_engine or SaturationEngine()
        self.lifecycle_manager = lifecycle_manager or LifecycleManager()

        # In-memory aggregation cache
        # Key: f"{type}:{platform_id}"
        # Value: List of (timestamp, play_count) tuples
        self.trend_cache: Dict[str, List[Tuple[datetime, int]]] = {}

        # Maximum data points per trend (configurable)
        self.max_cache_points = settings.velocity_max_data_points

    async def process_video(self, video: VideoData) -> List[Trend]:
        """
        Process a single video and update related trends.

        This is the main entry point for video processing.

        Args:
            video: Video data from scraper (via Redis queue)

        Returns:
            List of trends that were created or updated
        """
        # Extract trends from video
        extracted_trends = self._extract_trends(video)

        updated_trends = []

        for extracted in extracted_trends:
            try:
                trend = await self._process_trend(extracted)
                if trend:
                    updated_trends.append(trend)
            except Exception as e:
                logger.error(
                    "trend_processing_error",
                    trend_type=extracted.type.value,
                    platform_id=extracted.platform_id,
                    error=str(e)
                )

        return updated_trends

    def _extract_trends(self, video: VideoData) -> List[ExtractedTrend]:
        """
        Extract potential trends from video data.

        Extracts:
        - Sound/music trend (if music.id exists)
        - Hashtag trends (for each hashtag)

        Args:
            video: Video data to extract from

        Returns:
            List of extracted trends
        """
        trends = []

        # Extract sound/music trend
        if video.music and video.music.id:
            name = video.music.title or f"Sound {video.music.id}"
            if video.music.author_name:
                name = f"{name} - {video.music.author_name}"

            trends.append(ExtractedTrend(
                type=TrendType.SOUND,
                platform_id=video.music.id,
                name=name[:200],  # Truncate to max length
                video=video
            ))

        # Extract hashtag trends
        for hashtag in video.hashtags:
            if hashtag:  # Skip empty strings
                trends.append(ExtractedTrend(
                    type=TrendType.HASHTAG,
                    platform_id=hashtag.lower(),  # Normalize to lowercase
                    name=f"#{hashtag}",
                    video=video
                ))

        return trends

    async def _process_trend(self, extracted: ExtractedTrend) -> Optional[Trend]:
        """
        Process a single trend: aggregate data, calculate velocity, persist.

        This method:
        1. Adds current data point to cache
        2. Retrieves existing trend from database
        3. Calculates velocity from cached data
        4. Calculates saturation score
        5. Determines lifecycle status
        6. Creates or updates the trend record
        7. Records velocity history

        Args:
            extracted: Extracted trend from video

        Returns:
            Created or updated trend, or None if velocity too low
        """
        cache_key = f"{extracted.type.value}:{extracted.platform_id}"

        # Add current data point to cache
        data_point = (extracted.video.scraped_at, extracted.video.stats.play_count)

        if cache_key not in self.trend_cache:
            self.trend_cache[cache_key] = []

        self.trend_cache[cache_key].append(data_point)

        # Keep only the most recent data points
        if len(self.trend_cache[cache_key]) > self.max_cache_points:
            self.trend_cache[cache_key] = self.trend_cache[cache_key][-self.max_cache_points:]

        # Get existing trend from database
        existing_trend = await self.repository.get_by_platform_id(
            extracted.type,
            extracted.platform_id
        )

        # Calculate velocity
        velocity = self.velocity_engine.calculate_velocity(
            self.trend_cache[cache_key]
        )

        # Only persist if velocity is significant
        if velocity.score < settings.trend_min_velocity_score:
            logger.debug(
                "trend_velocity_below_threshold",
                cache_key=cache_key,
                velocity_score=velocity.score,
                threshold=settings.trend_min_velocity_score
            )
            return None

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
                extracted,
                velocity,
                saturation,
                status
            )
        else:
            status = TrendStatus.EMERGING
            trend_record = await self._create_trend(
                extracted,
                velocity,
                saturation,
                status
            )

        # Record velocity history
        await self.repository.record_velocity_history(
            trend_id=trend_record.id,
            timestamp=datetime.utcnow(),
            video_count=extracted.video.stats.play_count,
            velocity_score=velocity.score,
            growth_rate=velocity.growth_rate,
            saturation_percent=saturation.score
        )

        logger.info(
            "trend_processed",
            trend_id=str(trend_record.id),
            trend_name=trend_record.name,
            velocity_score=velocity.score,
            saturation_score=saturation.score,
            status=status.value,
            is_exponential=velocity.is_exponential
        )

        return trend_record

    async def _create_trend(
        self,
        extracted: ExtractedTrend,
        velocity: VelocityResult,
        saturation: SaturationResult,
        status: TrendStatus
    ) -> Trend:
        """
        Create new trend record in database.

        Args:
            extracted: Extracted trend data
            velocity: Calculated velocity result
            saturation: Calculated saturation result
            status: Initial status (always EMERGING for new trends)

        Returns:
            Created trend record
        """
        now = datetime.utcnow()

        trend = Trend(
            type=extracted.type,
            name=extracted.name,
            platform_id=extracted.platform_id,
            niche_id=None,  # Assigned by clustering (future enhancement)
            first_detected_at=now,
            peak_detected_at=None,
            status=status,
            velocity_score=velocity.score,
            saturation_percent=saturation.score,
            video_count_start=1,
            video_count_current=1,
            growth_rate=velocity.growth_rate,
            metadata={
                "initial_velocity": {
                    "score": velocity.score,
                    "growth_rate": velocity.growth_rate,
                    "r_squared": velocity.r_squared,
                    "is_exponential": velocity.is_exponential
                },
                "example_videos": [extracted.video.id],
                "example_creators": [{
                    "username": extracted.video.author.unique_id,
                    "follower_count": extracted.video.author.follower_count
                }]
            },
            created_at=now,
            updated_at=now
        )

        return await self.repository.create(trend)

    async def _update_trend(
        self,
        existing: Trend,
        extracted: ExtractedTrend,
        velocity: VelocityResult,
        saturation: SaturationResult,
        status: TrendStatus
    ) -> Trend:
        """
        Update existing trend record.

        Args:
            existing: Existing trend record
            extracted: Extracted trend data (for metadata update)
            velocity: Calculated velocity result
            saturation: Calculated saturation result
            status: New status

        Returns:
            Updated trend record
        """
        updates = {
            "velocity_score": velocity.score,
            "saturation_percent": saturation.score,
            "video_count_current": existing.video_count_current + 1,
            "growth_rate": velocity.growth_rate,
            "status": status,
        }

        # Update peak time if transitioning to peaking
        if self.lifecycle_manager.should_record_peak_time(existing.status, status):
            updates["peak_detected_at"] = datetime.utcnow()

        # Update metadata with example videos (keep up to 10)
        metadata = existing.metadata.copy()
        example_videos = metadata.get("example_videos", [])
        if extracted.video.id not in example_videos:
            example_videos.append(extracted.video.id)
            if len(example_videos) > 10:
                example_videos = example_videos[-10:]
            metadata["example_videos"] = example_videos
        updates["metadata"] = metadata

        return await self.repository.update(existing.id, updates)

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about the trend cache.

        Returns:
            Dict with cache statistics
        """
        total_points = sum(len(points) for points in self.trend_cache.values())

        return {
            "total_trends": len(self.trend_cache),
            "total_data_points": total_points,
            "avg_points_per_trend": total_points / len(self.trend_cache) if self.trend_cache else 0
        }

    def clear_stale_cache_entries(self, max_age_hours: int = 72) -> int:
        """
        Clear stale entries from the trend cache.

        Removes trends that haven't had new data in the specified time.

        Args:
            max_age_hours: Maximum age in hours (default 72)

        Returns:
            Number of entries removed
        """
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        removed = 0

        for cache_key in list(self.trend_cache.keys()):
            points = self.trend_cache[cache_key]
            if points:
                latest = max(point[0] for point in points)
                if latest < cutoff:
                    del self.trend_cache[cache_key]
                    removed += 1

        if removed > 0:
            logger.info(
                "cache_cleanup",
                removed_entries=removed,
                remaining_entries=len(self.trend_cache)
            )

        return removed

    async def get_trend_with_history(
        self,
        trend_id: str,
        history_hours: int = 24
    ) -> Optional[Dict]:
        """
        Get a trend with its velocity history.

        Convenience method for API responses.

        Args:
            trend_id: Trend UUID as string
            history_hours: Hours of history to include

        Returns:
            Dict with trend and velocity_history, or None if not found
        """
        try:
            trend_uuid = uuid.UUID(trend_id)
        except ValueError:
            return None

        trend = await self.repository.get_by_id(trend_uuid)
        if not trend:
            return None

        history = await self.repository.get_velocity_history(trend_uuid, history_hours)

        return {
            "trend": trend.model_dump(),
            "velocity_history": [h.model_dump() for h in history]
        }


# Import uuid for the get_trend_with_history method
import uuid
