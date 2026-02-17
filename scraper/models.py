"""
Pydantic Data Models for Scraper Service

Type-safe models for video metadata, health checks, and internal data structures.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum


class VideoStats(BaseModel):
    """Video engagement statistics from TikTok."""

    model_config = ConfigDict(populate_by_name=True)

    play_count: int = Field(
        ...,
        alias="playCount",
        ge=0,
        description="Number of video views/plays"
    )
    digg_count: int = Field(
        ...,
        alias="diggCount",
        ge=0,
        description="Number of likes (digg is TikTok's internal term)"
    )
    share_count: int = Field(
        ...,
        alias="shareCount",
        ge=0,
        description="Number of times video was shared"
    )
    comment_count: int = Field(
        ...,
        alias="commentCount",
        ge=0,
        description="Number of comments on the video"
    )


class VideoAuthor(BaseModel):
    """Video author/creator information."""

    model_config = ConfigDict(populate_by_name=True)

    unique_id: str = Field(
        ...,
        alias="uniqueId",
        min_length=1,
        max_length=100,
        description="TikTok username (e.g., @username)"
    )
    nickname: Optional[str] = Field(
        default=None,
        alias="nickname",
        max_length=100,
        description="Display name of the creator"
    )
    follower_count: int = Field(
        ...,
        alias="followerCount",
        ge=0,
        description="Number of followers the creator has"
    )


class VideoMusic(BaseModel):
    """Music/sound information associated with the video."""

    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(
        default=None,
        description="TikTok sound/music ID"
    )
    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Title of the sound/music"
    )
    author_name: Optional[str] = Field(
        default=None,
        alias="authorName",
        max_length=100,
        description="Author/artist name"
    )


class VideoData(BaseModel):
    """Complete video metadata structure for queue messages.

    This is the primary data structure pushed to Redis queue
    for consumption by the trend detection engine.
    """

    model_config = ConfigDict(populate_by_name=True)

    # Core identifiers
    id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="TikTok video ID"
    )
    desc: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Video caption/description"
    )
    create_time: int = Field(
        ...,
        alias="createTime",
        ge=0,
        description="Unix timestamp of video creation"
    )

    # Engagement data
    stats: VideoStats = Field(
        ...,
        description="Video engagement statistics"
    )

    # Creator data
    author: VideoAuthor = Field(
        ...,
        description="Video creator information"
    )

    # Music/sound data
    music: Optional[VideoMusic] = Field(
        default=None,
        description="Associated music/sound"
    )

    # Hashtags
    hashtags: List[str] = Field(
        default_factory=list,
        max_length=50,
        description="List of hashtags used in video"
    )

    # Scraping metadata
    scraped_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when video was scraped"
    )

    # Source tracking
    source_type: Optional[str] = Field(
        default=None,
        description="Source of video: 'trending', 'hashtag', or 'user'"
    )
    source_query: Optional[str] = Field(
        default=None,
        description="Original query (hashtag name, username, etc.)"
    )


class HealthStatus(str, Enum):
    """Health check status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class CheckStatus(str, Enum):
    """Individual check status."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class ComponentCheck(BaseModel):
    """Health check result for a single component."""

    status: CheckStatus = Field(
        ...,
        description="Check result status"
    )
    latency_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="Check latency in milliseconds"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if check failed"
    )
    state: Optional[str] = Field(
        default=None,
        description="Current state (e.g., circuit breaker state)"
    )
    failure_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of failures for this component"
    )
    last_scrape: Optional[str] = Field(
        default=None,
        description="ISO timestamp of last successful scrape"
    )
    videos_scraped: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total videos scraped"
    )


class ScraperHealth(BaseModel):
    """Complete health check response structure."""

    status: HealthStatus = Field(
        ...,
        description="Overall health status"
    )
    version: str = Field(
        default="1.0.0",
        description="Scraper service version"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )
    checks: dict[str, ComponentCheck] = Field(
        default_factory=dict,
        description="Individual component checks"
    )
    metrics: dict[str, int | float] = Field(
        default_factory=dict,
        description="Scraper metrics"
    )


class ScraperMetrics(BaseModel):
    """Scraper performance metrics."""

    videos_scraped_total: int = Field(
        default=0,
        ge=0,
        description="Total videos scraped since startup"
    )
    videos_scraped_current_cycle: int = Field(
        default=0,
        ge=0,
        description="Videos scraped in current cycle"
    )
    errors_total: int = Field(
        default=0,
        ge=0,
        description="Total errors since startup"
    )
    rate_limit_hits: int = Field(
        default=0,
        ge=0,
        description="Number of rate limit hits"
    )
    circuit_opens: int = Field(
        default=0,
        ge=0,
        description="Number of times circuit breaker opened"
    )
    last_scrape_timestamp: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last successful scrape"
    )
    uptime_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Service uptime in seconds"
    )
    scrape_cycles_completed: int = Field(
        default=0,
        ge=0,
        description="Number of completed scrape cycles"
    )


class TrendSignal(BaseModel):
    """Detected trend signal from video data."""

    signal_type: str = Field(
        ...,
        description="Type: 'sound', 'hashtag', or 'format'"
    )
    platform_id: str = Field(
        ...,
        description="TikTok's internal ID for this trend"
    )
    name: str = Field(
        ...,
        description="Display name of the trend"
    )
    video_count: int = Field(
        default=1,
        ge=1,
        description="Number of videos with this trend"
    )
    first_seen_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this trend was first detected"
    )
    last_seen_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Most recent video with this trend"
    )
    sample_video_ids: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Sample video IDs for this trend"
    )
