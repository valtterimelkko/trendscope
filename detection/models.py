"""
Pydantic Data Models for Trend Detection Engine

Type-safe models for video metadata, trends, velocity history,
and related data structures.

These models align with:
- Stage 03 VideoData format (from scraper)
- Database schema in Project-Technical-Architecture.md
- API contracts for trend endpoints
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class TrendType(str, Enum):
    """Type of trend being tracked."""

    SOUND = "sound"
    HASHTAG = "hashtag"
    FORMAT = "format"


class TrendStatus(str, Enum):
    """Trend lifecycle status.

    Lifecycle flow:
    EMERGING -> PEAKING -> SATURATED -> EXPIRED

    A trend can also go directly from EMERGING to EXPIRED
    if it never gains sufficient momentum.
    """

    EMERGING = "emerging"    # Just detected, early growth phase
    PEAKING = "peaking"      # Maximum velocity reached
    SATURATED = "saturated"  # Growth slowing, mainstream adoption
    EXPIRED = "expired"      # No longer relevant


class VideoStats(BaseModel):
    """Video engagement statistics from TikTok.

    Matches Stage 03 VideoStats for compatibility.
    """

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


class VideoMusic(BaseModel):
    """Music/sound information associated with the video.

    This is the primary source for SOUND trend detection.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(
        default=None,
        description="TikTok sound/music ID (primary key for sound trends)"
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


class VideoAuthor(BaseModel):
    """Video author/creator information.

    Used for micro-influencer tracking (<10k followers).
    """

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


class VideoData(BaseModel):
    """Complete video metadata structure from Redis queue.

    This model matches the Stage 03 VideoData format for seamless
    consumption from the Redis queue.

    The primary fields used for trend detection:
    - music.id -> SOUND trends
    - hashtags -> HASHTAG trends
    - stats.play_count -> velocity calculation
    - scraped_at -> timestamp for time-series analysis
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

    # Music/sound data (key for sound trends)
    music: Optional[VideoMusic] = Field(
        default=None,
        description="Associated music/sound (source of SOUND trends)"
    )

    # Hashtags (key for hashtag trends)
    hashtags: List[str] = Field(
        default_factory=list,
        max_length=50,
        description="List of hashtags used in video (source of HASHTAG trends)"
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


class Trend(BaseModel):
    """Detected trend record.

    Represents a trend (sound or hashtag) that has been identified
    and is being tracked through its lifecycle.

    Maps to the 'trends' table in PostgreSQL.
    """

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique trend identifier (UUID)"
    )
    type: TrendType = Field(
        ...,
        description="Type of trend: sound, hashtag, or format"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display name of the trend"
    )
    platform_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="TikTok's internal ID for this trend"
    )
    niche_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Assigned niche (from clustering, future enhancement)"
    )

    # Lifecycle timestamps
    first_detected_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this trend was first detected"
    )
    peak_detected_at: Optional[datetime] = Field(
        default=None,
        description="When this trend peaked (transitioned to PEAKING status)"
    )

    # Current state
    status: TrendStatus = Field(
        default=TrendStatus.EMERGING,
        description="Current lifecycle status"
    )

    # Metrics
    velocity_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Current velocity score (0-100)"
    )
    saturation_percent: int = Field(
        ...,
        ge=0,
        le=100,
        description="Current saturation percentage (0-100%)"
    )

    # Video tracking
    video_count_start: int = Field(
        default=1,
        ge=1,
        description="Video count when first detected"
    )
    video_count_current: int = Field(
        default=1,
        ge=1,
        description="Current video count using this trend"
    )

    # Growth metrics
    growth_rate: float = Field(
        default=0.0,
        ge=0.0,
        description="Percentage growth rate per hour"
    )

    # Additional data
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional trend metadata (example videos, etc.)"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Record creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Record last update timestamp"
    )


class TrendVelocityHistory(BaseModel):
    """Velocity history record for time-series analysis.

    Stores snapshots of trend metrics at regular intervals
    for historical analysis and graphing.

    Maps to 'trend_velocity_history' table in PostgreSQL.
    """

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique history record identifier"
    )
    trend_id: uuid.UUID = Field(
        ...,
        description="Foreign key to parent trend"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this snapshot was recorded"
    )

    # Snapshot metrics
    video_count: int = Field(
        ...,
        ge=0,
        description="Video count at this point in time"
    )
    velocity_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Velocity score at this point"
    )
    growth_rate: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Growth rate at this point"
    )
    saturation_percent: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Saturation percentage at this point"
    )


class TrendWithHistory(BaseModel):
    """Trend with velocity history for API responses.

    Used when returning trend details with historical data
    for graphing and analysis.
    """

    trend: Trend = Field(
        ...,
        description="The trend record"
    )
    velocity_history: List[TrendVelocityHistory] = Field(
        default_factory=list,
        description="Historical velocity snapshots"
    )


class ExtractedTrend(BaseModel):
    """Trend extracted from video data during processing.

    Internal model used by TrendDetector to represent
    a potential trend found in a video.
    """

    type: TrendType = Field(
        ...,
        description="Type of extracted trend"
    )
    platform_id: str = Field(
        ...,
        description="TikTok's ID for this trend"
    )
    name: str = Field(
        ...,
        description="Display name"
    )
    video: VideoData = Field(
        ...,
        description="Source video data"
    )


class VelocityResult(BaseModel):
    """Result of velocity calculation from VelocityEngine.

    Contains all metrics from the exponential growth analysis.
    """

    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Velocity score (0-100)"
    )
    growth_rate: float = Field(
        ...,
        ge=0.0,
        description="Percentage growth rate per hour"
    )
    doubling_time: float = Field(
        ...,
        ge=0.0,
        description="Hours to double (Rule of 70)"
    )
    r_squared: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Coefficient of determination (fit quality)"
    )
    is_exponential: bool = Field(
        ...,
        description="True if R-squared > 0.85 (exponential growth)"
    )
    acceleration: float = Field(
        ...,
        description="Second derivative (trend direction)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the result (0-1)"
    )
    data_points: int = Field(
        ...,
        ge=0,
        description="Number of data points used in calculation"
    )
    time_window_hours: float = Field(
        ...,
        ge=0.0,
        description="Time span of data in hours"
    )


class SaturationResult(BaseModel):
    """Result of saturation calculation from SaturationEngine.

    Contains saturation score and related metadata.
    """

    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Saturation percentage (0-100%)"
    )
    stage: str = Field(
        ...,
        description="Trend stage: 'early', 'growth', 'mature', or 'decline'"
    )
    recommendation: str = Field(
        ...,
        description="Action recommendation for user"
    )
