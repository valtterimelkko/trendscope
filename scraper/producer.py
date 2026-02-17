"""
TikTok Data Producer

Implements the producer side of the producer-consumer pattern.
Fetches TikTok video metadata using TikTok-Api and pushes to Redis queue.

Architecture:
- Uses TikTok-Api library with Playwright for browser automation
- IPRoyal rotating residential proxies for IP rotation
- Rate limiting per endpoint type (trending, hashtag, user)
- Circuit breaker pattern for fault tolerance
- Redis queue with 72-hour TTL for hot cache

CRITICAL CONSTRAINTS:
- NEVER commit proxy credentials (use env vars)
- NEVER exceed rate limits (will trigger blocks)
- NEVER disable SSL verification
- ALWAYS use circuit breaker for external calls
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Optional
from datetime import datetime
from contextlib import asynccontextmanager

import redis.asyncio as redis
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from .config import settings
from .models import VideoData, VideoStats, VideoAuthor, VideoMusic
from .rate_limiter import get_rate_limiters, RateLimiter
from .circuit_breaker import CircuitBreaker, CircuitOpenError, get_circuit_breaker

logger = logging.getLogger(__name__)


# Custom exceptions for better error handling
class TikTokScrapeError(Exception):
    """Base TikTok scraping error."""
    pass


class RateLimitError(TikTokScrapeError):
    """Rate limit exceeded - 429 response or detected as bot."""
    pass


class BlockedError(TikTokScrapeError):
    """IP blocked by TikTok - 403 response."""
    pass


class EmptyResponseError(TikTokScrapeError):
    """Empty response from TikTok - no videos returned."""
    pass


class TikTokAPIError(TikTokScrapeError):
    """General TikTok API error."""
    pass


def create_retry_decorator():
    """Create retry decorator with configuration from settings."""
    return retry(
        stop=stop_after_attempt(settings.retry_max_attempts),
        wait=wait_exponential(
            multiplier=1,
            min=settings.retry_min_wait,
            max=settings.retry_max_wait
        ),
        retry=retry_if_exception_type((
            RateLimitError,
            EmptyResponseError,
            asyncio.TimeoutError,
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


class TikTokProducer:
    """Produces video data to Redis queue.

    This class handles:
    - TikTok-Api initialization with proxy configuration
    - Rate-limited data fetching for different endpoint types
    - Circuit breaker protection for external calls
    - Video metadata parsing and validation
    - Redis queue operations with TTL management

    Attributes:
        redis_client: Redis connection for queue operations
        proxy: Optional proxy URL for TikTok requests
        rate_limiters: Dict of rate limiters per endpoint type
        circuit_breaker: Circuit breaker for fault tolerance
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        proxy: Optional[str] = None,
    ):
        """Initialize TikTok producer.

        Args:
            redis_client: Redis connection for queue operations
            proxy: Optional proxy URL (from settings if not provided)
        """
        self.redis = redis_client
        self.proxy = proxy or settings.proxy_url
        self.rate_limiters = get_rate_limiters()
        self.circuit_breaker = get_circuit_breaker()

        # Metrics tracking
        self.videos_produced = 0
        self.errors_count = 0
        self.last_scrape_time: Optional[datetime] = None

        logger.info(
            "producer_initialized",
            extra={
                "has_proxy": self.proxy is not None,
                "rate_limits": {
                    k: f"{v.rate * 60:.1f}/min"
                    for k, v in self.rate_limiters.items()
                },
            }
        )

    @asynccontextmanager
    async def _tiktok_api_session(self):
        """Context manager for TikTok-Api sessions.

        Note: This is a placeholder for actual TikTok-Api integration.
        The actual implementation depends on TikTok-Api library usage.
        """
        # Placeholder for TikTok-Api initialization
        # In production, this would create a TikTokApi instance
        # with Playwright and proxy configuration
        api = None
        try:
            # api = TikTokApi(proxy=self.proxy)
            yield api
        finally:
            if api:
                pass  # await api.close()

    async def scrape_trending(
        self,
        count: int = 100,
    ) -> AsyncGenerator[VideoData, None]:
        """Fetch trending videos with rate limiting and circuit breaker.

        Args:
            count: Maximum number of videos to fetch

        Yields:
            VideoData objects for each video

        Raises:
            CircuitOpenError: If circuit breaker is open
            TikTokScrapeError: If scraping fails after retries
        """
        rate_limiter = self.rate_limiters["trending"]

        @create_retry_decorator()
        async def _fetch_batch():
            return await self._fetch_trending_batch(count)

        try:
            # Circuit breaker check
            if self.circuit_breaker.is_open():
                raise CircuitOpenError("Circuit breaker is OPEN - cannot scrape trending")

            async for video in _fetch_batch():
                await rate_limiter.acquire()
                yield video
                self.videos_produced += 1
        except CircuitOpenError:
            logger.error("circuit_breaker_open_trending")
            raise
        except Exception as e:
            self.errors_count += 1
            self._classify_and_raise_error(e)

    async def _fetch_trending_batch(
        self,
        count: int,
    ) -> AsyncGenerator[VideoData, None]:
        """Fetch batch of trending videos.

        Note: This is a placeholder for actual TikTok-Api integration.
        In production, this would use the TikTokApi library.
        """
        # Placeholder implementation
        # In production:
        # async with TikTokApi() as api:
        #     async for video in api.trending.videos(count=count):
        #         yield self._parse_video(video, source_type="trending")

        logger.info("fetching_trending", extra={"count": count})
        self.last_scrape_time = datetime.utcnow()

        # Yield empty generator for now (placeholder)
        return
        yield  # Makes this a generator

    async def scrape_hashtag(
        self,
        hashtag: str,
        count: int = 100,
    ) -> AsyncGenerator[VideoData, None]:
        """Fetch videos for specific hashtag with conservative rate limiting.

        Args:
            hashtag: Hashtag name (without #)
            count: Maximum number of videos to fetch

        Yields:
            VideoData objects for each video

        Raises:
            CircuitOpenError: If circuit breaker is open
            TikTokScrapeError: If scraping fails after retries
        """
        rate_limiter = self.rate_limiters["hashtag"]

        @create_retry_decorator()
        async def _fetch_batch():
            return await self._fetch_hashtag_batch(hashtag, count)

        try:
            async for video in _fetch_batch():
                await rate_limiter.acquire()
                yield video
                self.videos_produced += 1
        except CircuitOpenError:
            logger.error("circuit_breaker_open_hashtag", extra={"hashtag": hashtag})
            raise
        except Exception as e:
            self.errors_count += 1
            self._classify_and_raise_error(e)

    async def _fetch_hashtag_batch(
        self,
        hashtag: str,
        count: int,
    ) -> AsyncGenerator[VideoData, None]:
        """Fetch batch of hashtag videos.

        Note: This is a placeholder for actual TikTok-Api integration.
        """
        logger.info(
            "fetching_hashtag",
            extra={"hashtag": hashtag, "count": count}
        )
        self.last_scrape_time = datetime.utcnow()

        # Placeholder implementation
        return
        yield

    async def scrape_user(
        self,
        username: str,
        count: int = 50,
    ) -> AsyncGenerator[VideoData, None]:
        """Fetch user videos with most conservative rate limiting.

        Args:
            username: TikTok username (without @)
            count: Maximum number of videos to fetch

        Yields:
            VideoData objects for each video

        Raises:
            CircuitOpenError: If circuit breaker is open
            TikTokScrapeError: If scraping fails after retries
        """
        rate_limiter = self.rate_limiters["user"]

        @create_retry_decorator()
        async def _fetch_batch():
            return await self._fetch_user_batch(username, count)

        try:
            async for video in _fetch_batch():
                await rate_limiter.acquire()
                yield video
                self.videos_produced += 1
        except CircuitOpenError:
            logger.error("circuit_breaker_open_user", extra={"username": username})
            raise
        except Exception as e:
            self.errors_count += 1
            self._classify_and_raise_error(e)

    async def _fetch_user_batch(
        self,
        username: str,
        count: int,
    ) -> AsyncGenerator[VideoData, None]:
        """Fetch batch of user videos.

        Note: This is a placeholder for actual TikTok-Api integration.
        """
        logger.info(
            "fetching_user",
            extra={"username": username, "count": count}
        )
        self.last_scrape_time = datetime.utcnow()

        # Placeholder implementation
        return
        yield

    def _parse_video(
        self,
        video_data: dict,
        source_type: Optional[str] = None,
        source_query: Optional[str] = None,
    ) -> VideoData:
        """Parse raw video data into VideoData model.

        Args:
            video_data: Raw video dict from TikTok-Api
            source_type: 'trending', 'hashtag', or 'user'
            source_query: Original query (hashtag, username)

        Returns:
            Parsed VideoData model
        """
        try:
            # Extract stats
            stats = VideoStats(
                play_count=video_data.get("playCount", 0),
                digg_count=video_data.get("diggCount", 0),
                share_count=video_data.get("shareCount", 0),
                comment_count=video_data.get("commentCount", 0),
            )

            # Extract author
            author_data = video_data.get("author", {})
            author = VideoAuthor(
                unique_id=author_data.get("uniqueId", "unknown"),
                nickname=author_data.get("nickname"),
                follower_count=author_data.get("followerCount", 0),
            )

            # Extract music
            music_data = video_data.get("music", {})
            music = None
            if music_data:
                music = VideoMusic(
                    id=music_data.get("id"),
                    title=music_data.get("title"),
                    author_name=music_data.get("authorName"),
                )

            # Extract hashtags
            hashtags = [
                tag.get("name", "")
                for tag in video_data.get("hashtags", [])
                if tag.get("name")
            ]

            return VideoData(
                id=str(video_data.get("id", "")),
                desc=video_data.get("desc"),
                create_time=video_data.get("createTime", 0),
                stats=stats,
                author=author,
                music=music,
                hashtags=hashtags,
                source_type=source_type,
                source_query=source_query,
            )

        except Exception as e:
            logger.error(
                "parse_video_error",
                extra={
                    "video_id": video_data.get("id"),
                    "error": str(e),
                }
            )
            raise TikTokAPIError(f"Failed to parse video data: {e}")

    async def push_to_queue(
        self,
        video: VideoData,
        queue: Optional[str] = None,
    ) -> bool:
        """Push video metadata to Redis queue with TTL.

        Args:
            video: VideoData to push
            queue: Queue name (default from settings)

        Returns:
            True if successful

        Raises:
            redis.RedisError: If Redis operation fails
        """
        queue_name = queue or settings.redis_video_queue

        try:
            # Push to list (LPUSH adds to head)
            await self.redis.lpush(queue_name, video.model_dump_json())

            # Set/update TTL on the queue key
            await self.redis.expire(queue_name, settings.redis_video_ttl)

            logger.debug(
                "video_pushed_to_queue",
                extra={
                    "video_id": video.id,
                    "queue": queue_name,
                    "ttl_hours": settings.redis_video_ttl / 3600,
                }
            )

            return True

        except redis.RedisError as e:
            logger.error(
                "redis_push_error",
                extra={
                    "video_id": video.id,
                    "error": str(e),
                }
            )
            raise

    async def push_batch_to_queue(
        self,
        videos: list[VideoData],
        queue: Optional[str] = None,
    ) -> int:
        """Push multiple videos to queue efficiently.

        Args:
            videos: List of VideoData to push
            queue: Queue name (default from settings)

        Returns:
            Number of videos pushed
        """
        if not videos:
            return 0

        queue_name = queue or settings.redis_video_queue

        try:
            # Use pipeline for efficiency
            async with self.redis.pipeline() as pipe:
                for video in videos:
                    pipe.lpush(queue_name, video.model_dump_json())
                await pipe.execute()

            # Set TTL once for the queue
            await self.redis.expire(queue_name, settings.redis_video_ttl)

            logger.info(
                "batch_pushed_to_queue",
                extra={
                    "count": len(videos),
                    "queue": queue_name,
                }
            )

            return len(videos)

        except redis.RedisError as e:
            logger.error(
                "redis_batch_push_error",
                extra={
                    "video_count": len(videos),
                    "error": str(e),
                }
            )
            raise

    def _classify_and_raise_error(self, error: Exception) -> None:
        """Classify error and raise appropriate TikTokScrapeError.

        Args:
            error: Original exception

        Raises:
            Appropriate TikTokScrapeError subclass
        """
        error_msg = str(error).lower()

        if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
            raise RateLimitError(str(error))
        elif "block" in error_msg or "banned" in error_msg or "403" in error_msg:
            raise BlockedError(str(error))
        elif "empty" in error_msg or "no videos" in error_msg:
            raise EmptyResponseError(str(error))
        else:
            raise TikTokAPIError(str(error))

    async def run_continuous(
        self,
        interval: Optional[int] = None,
        hashtags: Optional[list[str]] = None,
    ) -> None:
        """Run scraper continuously with configurable interval.

        This is the main entry point for running the scraper as a service.

        Args:
            interval: Seconds between cycles (default from settings)
            hashtags: List of hashtags to scrape (default from settings)
        """
        interval = interval or settings.scrape_interval
        hashtags = hashtags or settings.hashtag_list

        logger.info(
            "starting_continuous_scraping",
            extra={
                "interval_seconds": interval,
                "hashtags": hashtags,
                "enable_trending": settings.enable_trending,
                "enable_hashtags": settings.enable_hashtags,
            }
        )

        while True:
            try:
                cycle_start = datetime.utcnow()

                # Scrape trending if enabled
                if settings.enable_trending:
                    trending_videos = []
                    async for video in self.scrape_trending(
                        count=settings.scrape_batch_size
                    ):
                        trending_videos.append(video)

                    if trending_videos:
                        await self.push_batch_to_queue(trending_videos)
                        logger.info(
                            "trending_cycle_complete",
                            extra={"videos_count": len(trending_videos)}
                        )

                # Scrape hashtags if enabled
                if settings.enable_hashtags:
                    for hashtag in hashtags:
                        hashtag_videos = []
                        async for video in self.scrape_hashtag(
                            hashtag=hashtag,
                            count=settings.scrape_batch_size
                        ):
                            hashtag_videos.append(video)

                        if hashtag_videos:
                            await self.push_batch_to_queue(hashtag_videos)
                            logger.info(
                                "hashtag_cycle_complete",
                                extra={
                                    "hashtag": hashtag,
                                    "videos_count": len(hashtag_videos)
                                }
                            )

                cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
                sleep_time = max(0, interval - cycle_duration)

                if sleep_time > 0:
                    logger.info(
                        "cycle_sleep",
                        extra={"sleep_seconds": sleep_time}
                    )
                    await asyncio.sleep(sleep_time)

            except CircuitOpenError as e:
                # Circuit is open, wait for recovery
                logger.warning(
                    "circuit_open_waiting",
                    extra={"error": str(e)}
                )
                await asyncio.sleep(settings.circuit_recovery_timeout)

            except Exception as e:
                logger.error(
                    "continuous_scrape_error",
                    extra={"error": str(e)},
                    exc_info=True
                )
                # Brief pause before retry
                await asyncio.sleep(60)
