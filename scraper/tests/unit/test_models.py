"""
Unit tests for Pydantic data models.

Tests VideoData, VideoStats, VideoAuthor, VideoMusic and related models
for valid data creation, validation, serialization, and edge cases.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from scraper.models import (
    VideoStats,
    VideoAuthor,
    VideoMusic,
    VideoData,
    HealthStatus,
    CheckStatus,
    ComponentCheck,
    ScraperHealth,
    ScraperMetrics,
    TrendSignal,
)


class TestVideoStats:
    """Test VideoStats model."""

    def test_valid_creation(self):
        """Valid data should create VideoStats successfully."""
        stats = VideoStats(
            play_count=1000,
            digg_count=50,
            share_count=10,
            comment_count=5
        )
        
        assert stats.play_count == 1000
        assert stats.digg_count == 50
        assert stats.share_count == 10
        assert stats.comment_count == 5

    def test_creation_with_aliases(self):
        """VideoStats should accept aliased field names."""
        stats = VideoStats(
            playCount=1000,
            diggCount=50,
            shareCount=10,
            commentCount=5
        )
        
        assert stats.play_count == 1000
        assert stats.digg_count == 50

    def test_zero_values_allowed(self):
        """Zero values should be allowed."""
        stats = VideoStats(
            play_count=0,
            digg_count=0,
            share_count=0,
            comment_count=0
        )
        
        assert stats.play_count == 0

    def test_negative_values_rejected(self):
        """Negative values should be rejected."""
        with pytest.raises(ValidationError):
            VideoStats(
                play_count=-1,
                digg_count=0,
                share_count=0,
                comment_count=0
            )

    def test_very_large_numbers_allowed(self):
        """Very large numbers should be allowed."""
        stats = VideoStats(
            play_count=999999999,
            digg_count=999999999,
            share_count=999999999,
            comment_count=999999999
        )
        
        assert stats.play_count == 999999999

    def test_json_serialization_round_trip(self):
        """JSON serialization and deserialization should work."""
        original = VideoStats(
            play_count=1000,
            digg_count=50,
            share_count=10,
            comment_count=5
        )
        
        json_data = original.model_dump(by_alias=True)
        restored = VideoStats.model_validate(json_data)
        
        assert restored.play_count == original.play_count
        assert restored.digg_count == original.digg_count

    def test_missing_required_field_raises_error(self):
        """Missing required field should raise ValidationError."""
        with pytest.raises(ValidationError):
            VideoStats(
                play_count=1000,
                digg_count=50,
                share_count=10
                # missing comment_count
            )


class TestVideoAuthor:
    """Test VideoAuthor model."""

    def test_valid_creation(self):
        """Valid data should create VideoAuthor successfully."""
        author = VideoAuthor(
            unique_id="@testuser",
            nickname="Test User",
            follower_count=1000
        )
        
        assert author.unique_id == "@testuser"
        assert author.nickname == "Test User"
        assert author.follower_count == 1000

    def test_optional_nickname(self):
        """Nickname should be optional."""
        author = VideoAuthor(
            unique_id="@testuser",
            follower_count=1000
        )
        
        assert author.nickname is None

    def test_unique_id_required(self):
        """unique_id is required."""
        with pytest.raises(ValidationError):
            VideoAuthor(
                follower_count=1000
            )

    def test_empty_unique_id_rejected(self):
        """Empty unique_id should be rejected."""
        with pytest.raises(ValidationError):
            VideoAuthor(
                unique_id="",
                follower_count=1000
            )

    def test_unicode_strings_allowed(self):
        """Unicode strings should be allowed."""
        author = VideoAuthor(
            unique_id="@测试用户",
            nickname="测试用户 😊",
            follower_count=1000
        )
        
        assert author.unique_id == "@测试用户"
        assert author.nickname == "测试用户 😊"

    def test_long_unique_id_rejected(self):
        """unique_id exceeding max_length should be rejected."""
        with pytest.raises(ValidationError):
            VideoAuthor(
                unique_id="a" * 101,  # Exceeds 100 char limit
                follower_count=1000
            )

    def test_negative_follower_count_rejected(self):
        """Negative follower_count should be rejected."""
        with pytest.raises(ValidationError):
            VideoAuthor(
                unique_id="@test",
                follower_count=-1
            )


class TestVideoMusic:
    """Test VideoMusic model."""

    def test_valid_creation(self):
        """Valid data should create VideoMusic successfully."""
        music = VideoMusic(
            id="music123",
            title="Test Song",
            author_name="Artist Name"
        )
        
        assert music.id == "music123"
        assert music.title == "Test Song"
        assert music.author_name == "Artist Name"

    def test_all_fields_optional(self):
        """All fields should be optional."""
        music = VideoMusic()
        
        assert music.id is None
        assert music.title is None
        assert music.author_name is None

    def test_partial_data_allowed(self):
        """Partial data should be allowed."""
        music = VideoMusic(title="Test Song")
        
        assert music.title == "Test Song"
        assert music.id is None
        assert music.author_name is None

    def test_long_title_rejected(self):
        """Title exceeding max_length should be rejected."""
        with pytest.raises(ValidationError):
            VideoMusic(title="a" * 201)  # Exceeds 200 char limit

    def test_json_serialization(self):
        """JSON serialization should work with aliases."""
        music = VideoMusic(
            id="music123",
            title="Test Song",
            author_name="Artist"
        )
        
        json_data = music.model_dump(by_alias=True)
        
        assert json_data["authorName"] == "Artist"


class TestVideoData:
    """Test VideoData model."""

    @pytest.fixture
    def valid_video_data(self):
        """Fixture for valid video data."""
        return {
            "id": "video123",
            "desc": "Test video description",
            "create_time": 1609459200,
            "stats": {
                "play_count": 1000,
                "digg_count": 50,
                "share_count": 10,
                "comment_count": 5
            },
            "author": {
                "unique_id": "@testuser",
                "follower_count": 1000
            }
        }

    def test_valid_creation(self, valid_video_data):
        """Valid data should create VideoData successfully."""
        video = VideoData(**valid_video_data)
        
        assert video.id == "video123"
        assert video.desc == "Test video description"
        assert video.create_time == 1609459200

    def test_nested_models_created(self, valid_video_data):
        """Nested models should be created from dict."""
        video = VideoData(**valid_video_data)
        
        assert isinstance(video.stats, VideoStats)
        assert isinstance(video.author, VideoAuthor)
        assert video.stats.play_count == 1000
        assert video.author.unique_id == "@testuser"

    def test_default_scraped_at(self, valid_video_data):
        """scraped_at should default to current time."""
        before = datetime.utcnow()
        video = VideoData(**valid_video_data)
        after = datetime.utcnow()
        
        assert before <= video.scraped_at <= after

    def test_default_hashtags(self, valid_video_data):
        """hashtags should default to empty list."""
        video = VideoData(**valid_video_data)
        
        assert video.hashtags == []

    def test_optional_music(self, valid_video_data):
        """music should be optional."""
        video = VideoData(**valid_video_data)
        
        assert video.music is None

    def test_with_music(self, valid_video_data):
        """music can be provided."""
        valid_video_data["music"] = {
            "id": "music123",
            "title": "Test Song"
        }
        video = VideoData(**valid_video_data)
        
        assert isinstance(video.music, VideoMusic)
        assert video.music.id == "music123"

    def test_source_tracking_fields(self, valid_video_data):
        """Source tracking fields should be optional."""
        video = VideoData(**valid_video_data)
        
        assert video.source_type is None
        assert video.source_query is None

    def test_with_source_tracking(self, valid_video_data):
        """Source tracking can be provided."""
        valid_video_data["source_type"] = "trending"
        valid_video_data["source_query"] = "viral"
        
        video = VideoData(**valid_video_data)
        
        assert video.source_type == "trending"
        assert video.source_query == "viral"

    def test_empty_id_rejected(self, valid_video_data):
        """Empty id should be rejected."""
        valid_video_data["id"] = ""
        
        with pytest.raises(ValidationError):
            VideoData(**valid_video_data)

    def test_negative_create_time_rejected(self, valid_video_data):
        """Negative create_time should be rejected."""
        valid_video_data["create_time"] = -1
        
        with pytest.raises(ValidationError):
            VideoData(**valid_video_data)

    def test_long_description_allowed_within_limit(self, valid_video_data):
        """Description within limit should be allowed."""
        valid_video_data["desc"] = "a" * 5000
        
        video = VideoData(**valid_video_data)
        
        assert len(video.desc) == 5000

    def test_too_long_description_rejected(self, valid_video_data):
        """Description exceeding limit should be rejected."""
        valid_video_data["desc"] = "a" * 5001
        
        with pytest.raises(ValidationError):
            VideoData(**valid_video_data)

    def test_unicode_in_description(self, valid_video_data):
        """Unicode characters should be allowed in description."""
        valid_video_data["desc"] = "测试描述 🎉 #标签"
        
        video = VideoData(**valid_video_data)
        
        assert video.desc == "测试描述 🎉 #标签"

    def test_json_serialization_round_trip(self, valid_video_data):
        """JSON serialization and deserialization should work."""
        original = VideoData(**valid_video_data)
        
        json_data = original.model_dump(mode="json", by_alias=True)
        restored = VideoData.model_validate(json_data)
        
        assert restored.id == original.id
        assert restored.stats.play_count == original.stats.play_count

    def test_hashtags_list_validation(self, valid_video_data):
        """hashtags should accept list of strings."""
        valid_video_data["hashtags"] = ["viral", "trending", "fyp"]
        
        video = VideoData(**valid_video_data)
        
        assert video.hashtags == ["viral", "trending", "fyp"]

    def test_too_many_hashtags_rejected(self, valid_video_data):
        """More than 50 hashtags should be rejected."""
        valid_video_data["hashtags"] = [f"tag{i}" for i in range(51)]
        
        with pytest.raises(ValidationError):
            VideoData(**valid_video_data)


class TestHealthStatus:
    """Test HealthStatus enum."""

    def test_enum_values(self):
        """HealthStatus should have correct values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestCheckStatus:
    """Test CheckStatus enum."""

    def test_enum_values(self):
        """CheckStatus should have correct values."""
        assert CheckStatus.PASS.value == "pass"
        assert CheckStatus.WARN.value == "warn"
        assert CheckStatus.FAIL.value == "fail"


class TestComponentCheck:
    """Test ComponentCheck model."""

    def test_valid_creation(self):
        """Valid data should create ComponentCheck."""
        check = ComponentCheck(
            status=CheckStatus.PASS,
            latency_ms=50,
            error=None,
            state="closed",
            failure_count=0,
            last_scrape="2024-01-01T00:00:00",
            videos_scraped=100
        )
        
        assert check.status == CheckStatus.PASS
        assert check.latency_ms == 50
        assert check.videos_scraped == 100

    def test_only_status_required(self):
        """Only status field is required."""
        check = ComponentCheck(status=CheckStatus.PASS)
        
        assert check.status == CheckStatus.PASS
        assert check.latency_ms is None
        assert check.error is None

    def test_negative_latency_rejected(self):
        """Negative latency should be rejected."""
        with pytest.raises(ValidationError):
            ComponentCheck(
                status=CheckStatus.PASS,
                latency_ms=-1
            )

    def test_negative_failure_count_rejected(self):
        """Negative failure_count should be rejected."""
        with pytest.raises(ValidationError):
            ComponentCheck(
                status=CheckStatus.PASS,
                failure_count=-1
            )

    def test_negative_videos_scraped_rejected(self):
        """Negative videos_scraped should be rejected."""
        with pytest.raises(ValidationError):
            ComponentCheck(
                status=CheckStatus.PASS,
                videos_scraped=-1
            )


class TestScraperHealth:
    """Test ScraperHealth model."""

    def test_valid_creation(self):
        """Valid data should create ScraperHealth."""
        health = ScraperHealth(
            status=HealthStatus.HEALTHY,
            version="1.0.0",
            checks={
                "redis": ComponentCheck(status=CheckStatus.PASS),
                "circuit_breaker": ComponentCheck(status=CheckStatus.PASS)
            },
            metrics={"videos_scraped": 100}
        )
        
        assert health.status == HealthStatus.HEALTHY
        assert health.version == "1.0.0"

    def test_status_required(self):
        """status field is required."""
        with pytest.raises(ValidationError):
            ScraperHealth()

    def test_default_version(self):
        """version should default to 1.0.0."""
        health = ScraperHealth(status=HealthStatus.HEALTHY)
        
        assert health.version == "1.0.0"

    def test_default_timestamp(self):
        """timestamp should default to current time."""
        before = datetime.utcnow()
        health = ScraperHealth(status=HealthStatus.HEALTHY)
        after = datetime.utcnow()
        
        assert before <= health.timestamp <= after

    def test_default_empty_checks(self):
        """checks should default to empty dict."""
        health = ScraperHealth(status=HealthStatus.HEALTHY)
        
        assert health.checks == {}

    def test_default_empty_metrics(self):
        """metrics should default to empty dict."""
        health = ScraperHealth(status=HealthStatus.HEALTHY)
        
        assert health.metrics == {}

    def test_json_serialization(self):
        """JSON serialization should work with datetime."""
        health = ScraperHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        json_data = health.model_dump(mode="json")
        
        assert json_data["status"] == "healthy"
        assert "timestamp" in json_data


class TestScraperMetrics:
    """Test ScraperMetrics model."""

    def test_valid_creation(self):
        """Valid data should create ScraperMetrics."""
        metrics = ScraperMetrics(
            videos_scraped_total=1000,
            videos_scraped_current_cycle=50,
            errors_total=5,
            rate_limit_hits=2,
            circuit_opens=1,
            last_scrape_timestamp=datetime.utcnow(),
            uptime_seconds=3600.0,
            scrape_cycles_completed=10
        )
        
        assert metrics.videos_scraped_total == 1000
        assert metrics.errors_total == 5

    def test_all_fields_have_defaults(self):
        """All fields should have default values."""
        metrics = ScraperMetrics()
        
        assert metrics.videos_scraped_total == 0
        assert metrics.videos_scraped_current_cycle == 0
        assert metrics.errors_total == 0
        assert metrics.rate_limit_hits == 0
        assert metrics.circuit_opens == 0
        assert metrics.last_scrape_timestamp is None
        assert metrics.uptime_seconds == 0.0
        assert metrics.scrape_cycles_completed == 0

    def test_negative_values_rejected(self):
        """Negative values should be rejected."""
        with pytest.raises(ValidationError):
            ScraperMetrics(videos_scraped_total=-1)

    def test_negative_uptime_rejected(self):
        """Negative uptime should be rejected."""
        with pytest.raises(ValidationError):
            ScraperMetrics(uptime_seconds=-1.0)


class TestTrendSignal:
    """Test TrendSignal model."""

    def test_valid_creation(self):
        """Valid data should create TrendSignal."""
        signal = TrendSignal(
            signal_type="hashtag",
            platform_id="hashtag123",
            name="viral",
            video_count=50,
            sample_video_ids=["vid1", "vid2", "vid3"]
        )
        
        assert signal.signal_type == "hashtag"
        assert signal.platform_id == "hashtag123"
        assert signal.name == "viral"
        assert signal.video_count == 50

    def test_required_fields(self):
        """signal_type, platform_id, name are required."""
        with pytest.raises(ValidationError):
            TrendSignal(signal_type="hashtag")

    def test_defaults(self):
        """Optional fields should have defaults."""
        signal = TrendSignal(
            signal_type="sound",
            platform_id="sound123",
            name="trending_sound"
        )
        
        assert signal.video_count == 1
        assert signal.sample_video_ids == []

    def test_negative_video_count_rejected(self):
        """Negative video_count should be rejected."""
        with pytest.raises(ValidationError):
            TrendSignal(
                signal_type="hashtag",
                platform_id="id",
                name="test",
                video_count=0  # Must be >= 1
            )

    def test_too_many_sample_video_ids_rejected(self):
        """More than 10 sample_video_ids should be rejected."""
        with pytest.raises(ValidationError):
            TrendSignal(
                signal_type="hashtag",
                platform_id="id",
                name="test",
                sample_video_ids=[f"vid{i}" for i in range(11)]
            )

    def test_default_timestamps(self):
        """first_seen_at and last_seen_at should default to now."""
        before = datetime.utcnow()
        signal = TrendSignal(
            signal_type="hashtag",
            platform_id="id",
            name="test"
        )
        after = datetime.utcnow()
        
        assert before <= signal.first_seen_at <= after
        assert before <= signal.last_seen_at <= after


class TestModelEdgeCases:
    """Test edge cases across all models."""

    def test_very_large_follower_count(self):
        """Very large follower counts should be allowed."""
        author = VideoAuthor(
            unique_id="@celebrity",
            follower_count=999999999999
        )
        
        assert author.follower_count == 999999999999

    def test_empty_hashtags_list(self):
        """Empty hashtags list should be valid."""
        stats = VideoStats(
            play_count=1,
            digg_count=0,
            share_count=0,
            comment_count=0
        )
        author = VideoAuthor(
            unique_id="@test",
            follower_count=0
        )
        video = VideoData(
            id="vid1",
            create_time=1,
            stats=stats,
            author=author,
            hashtags=[]
        )
        
        assert video.hashtags == []

    def test_special_characters_in_strings(self):
        """Special characters should be allowed in strings."""
        author = VideoAuthor(
            unique_id="@user_name-123",
            nickname="Test <User> & Friends",
            follower_count=100
        )
        
        assert author.unique_id == "@user_name-123"
        assert author.nickname == "Test <User> & Friends"

    def test_zero_play_count(self):
        """Zero play_count should be valid."""
        stats = VideoStats(
            play_count=0,
            digg_count=0,
            share_count=0,
            comment_count=0
        )
        
        assert stats.play_count == 0

    def test_datetime_precision(self):
        """Datetime fields should handle microsecond precision."""
        now = datetime.utcnow()
        metrics = ScraperMetrics(last_scrape_timestamp=now)
        
        assert metrics.last_scrape_timestamp == now
