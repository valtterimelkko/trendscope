"""
Trend Consumer - Redis Queue Consumer

Consumes video data from Redis queue and dispatches to trend detector.
Implements the consumer side of the producer-consumer pattern.

The consumer:
1. Fetches batches from Redis queue
2. Parses JSON to VideoData models
3. Sends to TrendDetector for processing
4. Removes processed items from queue
5. Handles errors gracefully
"""

import asyncio
import json
from typing import List, Optional
from datetime import datetime

import redis.asyncio as redis
import asyncpg

from detection.config import settings
from detection.trend_detector import TrendDetector
from detection.persistence import TrendRepository
from detection.velocity_engine import VelocityEngine
from detection.saturation import SaturationEngine
from detection.lifecycle_manager import LifecycleManager
from detection.models import VideoData, Trend
from detection.logging_config import get_logger

logger = get_logger(__name__)


class TrendConsumer:
    """
    Consumes video data from Redis and detects trends.

    The consumer runs a continuous loop that:
    1. Fetches a batch of videos from the Redis queue
    2. Parses each video from JSON to VideoData model
    3. Processes each video through the TrendDetector
    4. Removes processed items from the queue
    5. Waits if queue is empty

    Error handling:
    - Individual video errors are logged and skipped
    - Batch errors trigger a wait period
    - Connection errors trigger reconnection attempts
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        db_pool: asyncpg.Pool,
        trend_detector: Optional[TrendDetector] = None
    ):
        """
        Initialize trend consumer.

        Args:
            redis_client: Redis connection for queue operations
            db_pool: Database connection pool
            trend_detector: Optional custom trend detector
        """
        self.redis = redis_client
        self.db_pool = db_pool

        # Initialize trend detector if not provided
        if trend_detector:
            self.trend_detector = trend_detector
        else:
            repository = TrendRepository(db_pool)
            self.trend_detector = TrendDetector(
                repository=repository,
                velocity_engine=VelocityEngine(),
                saturation_engine=SaturationEngine(),
                lifecycle_manager=LifecycleManager()
            )

        self.running = False
        self.batch_size = settings.consumer_batch_size
        self.queue_name = settings.redis_video_queue

        # Metrics
        self.videos_processed = 0
        self.trends_detected = 0
        self.errors_count = 0
        self.last_batch_time: Optional[datetime] = None

    async def consume(self) -> None:
        """
        Main consumption loop - processes batches from Redis queue.

        This method runs indefinitely until stop() is called.
        It handles errors gracefully and reconnects if needed.
        """
        self.running = True
        logger.info(
            "consumer_started",
            queue=self.queue_name,
            batch_size=self.batch_size,
            idle_wait=settings.consumer_idle_wait
        )

        while self.running:
            try:
                # Fetch batch from queue
                batch = await self._fetch_batch()

                if not batch:
                    # Queue is empty, wait before next attempt
                    await asyncio.sleep(settings.consumer_idle_wait)
                    continue

                self.last_batch_time = datetime.utcnow()

                # Process each video in batch
                batch_trends = 0
                batch_errors = 0

                for video_json in batch:
                    try:
                        # Parse JSON to VideoData
                        video = VideoData.model_validate_json(video_json)

                        # Process through trend detector
                        trends = await self.trend_detector.process_video(video)

                        batch_trends += len(trends)
                        self.videos_processed += 1

                    except Exception as e:
                        batch_errors += 1
                        self.errors_count += 1
                        logger.error(
                            "video_processing_error",
                            error=str(e),
                            video_data_preview=video_json[:200] if video_json else None
                        )

                # Remove processed items from queue
                await self._remove_processed(len(batch))

                self.trends_detected += batch_trends

                logger.info(
                    "batch_processed",
                    videos_count=len(batch),
                    trends_detected=batch_trends,
                    errors=batch_errors,
                    total_videos=self.videos_processed,
                    total_trends=self.trends_detected
                )

            except redis.RedisError as e:
                logger.error(
                    "consumer_redis_error",
                    error=str(e)
                )
                self.errors_count += 1
                await asyncio.sleep(settings.consumer_error_wait)

            except asyncpg.PostgresError as e:
                logger.error(
                    "consumer_database_error",
                    error=str(e)
                )
                self.errors_count += 1
                await asyncio.sleep(settings.consumer_error_wait)

            except Exception as e:
                logger.error(
                    "consumer_error",
                    error=str(e),
                    exc_info=True
                )
                self.errors_count += 1
                await asyncio.sleep(settings.consumer_error_wait)

        logger.info(
            "consumer_stopped",
            total_videos_processed=self.videos_processed,
            total_trends_detected=self.trends_detected,
            total_errors=self.errors_count
        )

    async def _fetch_batch(self) -> List[str]:
        """
        Fetch a batch of video data from Redis queue.

        Uses LRANGE to get items without removing them.
        Items are removed after successful processing.

        Returns:
            List of JSON strings (video data)
        """
        items = await self.redis.lrange(self.queue_name, 0, self.batch_size - 1)
        return [item.decode("utf-8") for item in items]

    async def _remove_processed(self, count: int) -> None:
        """
        Remove processed items from queue.

        Uses LTRIM to keep only items beyond the processed count.

        Args:
            count: Number of items to remove from front of queue
        """
        if count <= 0:
            return

        # LTRIM keeps elements from start to end (inclusive)
        # We want to remove the first 'count' elements
        # So we keep from 'count' to -1 (end)
        await self.redis.ltrim(self.queue_name, count, -1)

    async def stop(self) -> None:
        """
        Gracefully stop the consumer.

        Sets running flag to False, allowing current batch
        to complete before exiting.
        """
        logger.info("consumer_stop_requested")
        self.running = False

    def get_metrics(self) -> dict:
        """
        Get consumer metrics.

        Returns:
            Dict with current metrics
        """
        return {
            "running": self.running,
            "videos_processed": self.videos_processed,
            "trends_detected": self.trends_detected,
            "errors_count": self.errors_count,
            "last_batch_time": self.last_batch_time.isoformat() if self.last_batch_time else None,
            "batch_size": self.batch_size,
            "queue_name": self.queue_name
        }

    async def get_queue_size(self) -> int:
        """
        Get current queue size.

        Returns:
            Number of items in queue
        """
        return await self.redis.llen(self.queue_name)


async def create_consumer(
    redis_url: Optional[str] = None,
    database_url: Optional[str] = None
) -> TrendConsumer:
    """
    Factory function to create a fully initialized consumer.

    Creates Redis and database connections and initializes
    all required components.

    Args:
        redis_url: Redis connection URL (default from settings)
        database_url: Database connection URL (default from settings)

    Returns:
        Initialized TrendConsumer instance
    """
    redis_url = redis_url or settings.redis_url
    database_url = database_url or settings.database_url

    # Create Redis connection
    redis_client = redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=False
    )

    # Create database pool
    db_pool = await asyncpg.create_pool(
        database_url,
        min_size=2,
        max_size=settings.database_pool_size
    )

    # Create repository
    repository = TrendRepository(db_pool)

    # Create trend detector with all components
    trend_detector = TrendDetector(
        repository=repository,
        velocity_engine=VelocityEngine(),
        saturation_engine=SaturationEngine(),
        lifecycle_manager=LifecycleManager()
    )

    return TrendConsumer(
        redis_client=redis_client,
        db_pool=db_pool,
        trend_detector=trend_detector
    )
