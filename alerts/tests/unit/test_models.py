"""
Unit tests for Alert models.

Tests Pydantic models including:
- Alert model creation and validation
- AlertStatus state transitions
- Tier enum validation
- AlertChannel validation
- BatchType validation
- UUID and timestamp auto-generation
- JSON serialization
- Edge cases
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any

import pytest
from pydantic import ValidationError

from alerts.models import (
    Alert,
    AlertResult,
    AlertChannel,
    AlertStatus,
    Tier,
    BatchType,
    UserAlertConfig,
    RoutingDecision,
    TrendForAlert,
    DigestEntry,
    EngagementEvent,
    EngagementStats,
    SlackMessage,
    EmailContent,
)


# =============================================================================
# Alert Model Tests
# =============================================================================

class TestAlertModel:
    """Tests for the core Alert model."""

    def test_alert_creation_with_all_fields(self):
        """Test creating an alert with all required fields."""
        user_id = uuid.uuid4()
        trend_id = uuid.uuid4()
        
        alert = Alert(
            user_id=user_id,
            trend_id=trend_id,
            channel=AlertChannel.EMAIL
        )
        
        assert alert.user_id == user_id
        assert alert.trend_id == trend_id
        assert alert.channel == AlertChannel.EMAIL
        assert alert.status == AlertStatus.PENDING
        assert isinstance(alert.id, uuid.UUID)
        assert isinstance(alert.created_at, datetime)

    def test_alert_creation_with_optional_fields(self):
        """Test creating an alert with optional fields specified."""
        user_id = uuid.uuid4()
        trend_id = uuid.uuid4()
        alert_id = uuid.uuid4()
        now = datetime.utcnow()
        
        alert = Alert(
            id=alert_id,
            user_id=user_id,
            trend_id=trend_id,
            channel=AlertChannel.SLACK,
            status=AlertStatus.SENT,
            sent_at=now,
            opened_at=now,
            clicked_at=now,
            dismissed=True,
            confidence_score=0.85
        )
        
        assert alert.id == alert_id
        assert alert.status == AlertStatus.SENT
        assert alert.sent_at == now
        assert alert.opened_at == now
        assert alert.clicked_at == now
        assert alert.dismissed is True
        assert alert.confidence_score == 0.85

    def test_alert_uuid_auto_generation(self):
        """Test that UUID is auto-generated when not provided."""
        alert1 = Alert(
            user_id=uuid.uuid4(),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.EMAIL
        )
        alert2 = Alert(
            user_id=uuid.uuid4(),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.EMAIL
        )
        
        assert isinstance(alert1.id, uuid.UUID)
        assert isinstance(alert2.id, uuid.UUID)
        assert alert1.id != alert2.id

    def test_alert_timestamp_auto_generation(self):
        """Test that created_at timestamp is auto-generated."""
        before = datetime.utcnow()
        alert = Alert(
            user_id=uuid.uuid4(),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.EMAIL
        )
        after = datetime.utcnow()
        
        assert isinstance(alert.created_at, datetime)
        assert before <= alert.created_at <= after

    def test_alert_default_status_pending(self):
        """Test that default status is PENDING."""
        alert = Alert(
            user_id=uuid.uuid4(),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.EMAIL
        )
        
        assert alert.status == AlertStatus.PENDING

    def test_alert_status_transition_success_path(self):
        """Test successful status transitions: PENDING → SENT → DELIVERED."""
        alert = Alert(
            user_id=uuid.uuid4(),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.SLACK
        )
        
        assert alert.status == AlertStatus.PENDING
        
        alert.status = AlertStatus.SENT
        assert alert.status == AlertStatus.SENT
        
        alert.status = AlertStatus.DELIVERED
        assert alert.status == AlertStatus.DELIVERED

    def test_alert_status_failure_path(self):
        """Test failure status transition: PENDING → SENT → FAILED."""
        alert = Alert(
            user_id=uuid.uuid4(),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.WEBHOOK
        )
        
        assert alert.status == AlertStatus.PENDING
        
        alert.status = AlertStatus.SENT
        assert alert.status == AlertStatus.SENT
        
        alert.status = AlertStatus.FAILED
        assert alert.status == AlertStatus.FAILED

    def test_alert_status_direct_to_failed(self):
        """Test transition from PENDING directly to FAILED."""
        alert = Alert(
            user_id=uuid.uuid4(),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.EMAIL
        )
        
        alert.status = AlertStatus.FAILED
        assert alert.status == AlertStatus.FAILED

    def test_alert_confidence_score_validation(self):
        """Test confidence score validation (0.0 to 1.0)."""
        # Valid values
        alert = Alert(
            user_id=uuid.uuid4(),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.EMAIL,
            confidence_score=0.5
        )
        assert alert.confidence_score == 0.5
        
        # Boundary values
        alert.confidence_score = 0.0
        assert alert.confidence_score == 0.0
        
        alert.confidence_score = 1.0
        assert alert.confidence_score == 1.0

    def test_alert_confidence_score_invalid_too_high(self):
        """Test that confidence score > 1.0 raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Alert(
                user_id=uuid.uuid4(),
                trend_id=uuid.uuid4(),
                channel=AlertChannel.EMAIL,
                confidence_score=1.5
            )
        
        assert "confidence_score" in str(exc_info.value)

    def test_alert_confidence_score_invalid_too_low(self):
        """Test that confidence score < 0.0 raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Alert(
                user_id=uuid.uuid4(),
                trend_id=uuid.uuid4(),
                channel=AlertChannel.EMAIL,
                confidence_score=-0.1
            )
        
        assert "confidence_score" in str(exc_info.value)

    def test_alert_missing_required_field_user_id(self):
        """Test that missing user_id raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Alert(
                trend_id=uuid.uuid4(),
                channel=AlertChannel.EMAIL
            )
        
        assert "user_id" in str(exc_info.value)

    def test_alert_missing_required_field_trend_id(self):
        """Test that missing trend_id raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Alert(
                user_id=uuid.uuid4(),
                channel=AlertChannel.EMAIL
            )
        
        assert "trend_id" in str(exc_info.value)

    def test_alert_missing_required_field_channel(self):
        """Test that missing channel raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Alert(
                user_id=uuid.uuid4(),
                trend_id=uuid.uuid4()
            )
        
        assert "channel" in str(exc_info.value)

    def test_alert_json_serialization(self):
        """Test JSON serialization with UUID and datetime fields."""
        user_id = uuid.uuid4()
        trend_id = uuid.uuid4()
        alert_id = uuid.uuid4()
        
        alert = Alert(
            id=alert_id,
            user_id=user_id,
            trend_id=trend_id,
            channel=AlertChannel.EMAIL,
            status=AlertStatus.SENT
        )
        
        # Serialize to dict (Pydantic model_dump)
        data = alert.model_dump()
        
        assert isinstance(data["id"], uuid.UUID)
        assert isinstance(data["user_id"], uuid.UUID)
        assert isinstance(data["trend_id"], uuid.UUID)
        assert isinstance(data["created_at"], datetime)
        assert data["channel"] == "email"
        assert data["status"] == "sent"

    def test_alert_json_serialization_mode_json(self):
        """Test JSON serialization mode that converts UUIDs to strings."""
        alert = Alert(
            user_id=uuid.uuid4(),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.SLACK
        )
        
        # Serialize to JSON-compatible dict
        data = alert.model_dump(mode="json")
        
        assert isinstance(data["id"], str)
        assert isinstance(data["user_id"], str)
        assert isinstance(data["trend_id"], str)
        assert isinstance(data["created_at"], str)

    def test_alert_model_dump_json(self):
        """Test model_dump_json method."""
        alert = Alert(
            user_id=uuid.uuid4(),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.WEBHOOK
        )
        
        json_str = alert.model_dump_json()
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert "id" in parsed
        assert "user_id" in parsed
        assert "trend_id" in parsed
        assert parsed["channel"] == "webhook"

    def test_alert_from_dict(self):
        """Test creating Alert from dictionary."""
        user_id = uuid.uuid4()
        trend_id = uuid.uuid4()
        
        data = {
            "user_id": user_id,
            "trend_id": trend_id,
            "channel": "email",
            "status": "pending"
        }
        
        alert = Alert(**data)
        
        assert alert.user_id == user_id
        assert alert.trend_id == trend_id
        assert alert.channel == AlertChannel.EMAIL
        assert alert.status == AlertStatus.PENDING

    def test_alert_optional_fields_none(self):
        """Test that optional fields can be None."""
        alert = Alert(
            user_id=uuid.uuid4(),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.EMAIL,
            sent_at=None,
            opened_at=None,
            clicked_at=None
        )
        
        assert alert.sent_at is None
        assert alert.opened_at is None
        assert alert.clicked_at is None

    def test_alert_future_timestamp(self):
        """Test that future timestamps are accepted."""
        future = datetime.utcnow() + timedelta(days=1)
        
        alert = Alert(
            user_id=uuid.uuid4(),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.EMAIL,
            sent_at=future
        )
        
        assert alert.sent_at == future

    def test_alert_very_long_content_in_model(self):
        """Test that model handles edge cases - Alert model doesn't have content field."""
        # This test documents that Alert model uses references (trend_id) 
        # rather than storing content directly
        alert = Alert(
            user_id=uuid.uuid4(),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.EMAIL
        )
        
        assert alert is not None


# =============================================================================
# AlertStatus Enum Tests
# =============================================================================

class TestAlertStatus:
    """Tests for AlertStatus enum."""

    def test_alert_status_values(self):
        """Test AlertStatus enum values."""
        assert AlertStatus.PENDING.value == "pending"
        assert AlertStatus.SENT.value == "sent"
        assert AlertStatus.DELIVERED.value == "delivered"
        assert AlertStatus.FAILED.value == "failed"

    def test_alert_status_from_string_valid(self):
        """Test creating AlertStatus from valid strings."""
        assert AlertStatus("pending") == AlertStatus.PENDING
        assert AlertStatus("sent") == AlertStatus.SENT
        assert AlertStatus("delivered") == AlertStatus.DELIVERED
        assert AlertStatus("failed") == AlertStatus.FAILED

    def test_alert_status_from_string_invalid(self):
        """Test that invalid status string raises ValueError."""
        with pytest.raises(ValueError):
            AlertStatus("invalid_status")

    def test_alert_status_comparison(self):
        """Test AlertStatus comparison operations."""
        status = AlertStatus.PENDING
        
        assert status == AlertStatus.PENDING
        assert status != AlertStatus.SENT
        assert status != "pending"  # Enum comparison, not string


# =============================================================================
# Tier Enum Tests
# =============================================================================

class TestTier:
    """Tests for Tier enum."""

    def test_tier_values(self):
        """Test Tier enum values."""
        assert Tier.FREE.value == "free"
        assert Tier.SOLO.value == "solo"
        assert Tier.AGENCY.value == "agency"
        assert Tier.ENTERPRISE.value == "enterprise"

    def test_tier_from_string_valid(self):
        """Test creating Tier from valid strings."""
        assert Tier("free") == Tier.FREE
        assert Tier("solo") == Tier.SOLO
        assert Tier("agency") == Tier.AGENCY
        assert Tier("enterprise") == Tier.ENTERPRISE

    def test_tier_from_string_invalid(self):
        """Test that invalid tier string raises ValueError."""
        with pytest.raises(ValueError):
            Tier("premium")

    def test_tier_case_sensitive(self):
        """Test that tier is case-sensitive."""
        with pytest.raises(ValueError):
            Tier("FREE")
        
        with pytest.raises(ValueError):
            Tier("Free")

    def test_tier_all_values(self):
        """Test that all expected tiers exist."""
        tiers = list(Tier)
        
        assert Tier.FREE in tiers
        assert Tier.SOLO in tiers
        assert Tier.AGENCY in tiers
        assert Tier.ENTERPRISE in tiers
        assert len(tiers) == 4


# =============================================================================
# AlertChannel Enum Tests
# =============================================================================

class TestAlertChannel:
    """Tests for AlertChannel enum."""

    def test_alert_channel_values(self):
        """Test AlertChannel enum values."""
        assert AlertChannel.EMAIL.value == "email"
        assert AlertChannel.SLACK.value == "slack"
        assert AlertChannel.WEBHOOK.value == "webhook"

    def test_alert_channel_from_string_valid(self):
        """Test creating AlertChannel from valid strings."""
        assert AlertChannel("email") == AlertChannel.EMAIL
        assert AlertChannel("slack") == AlertChannel.SLACK
        assert AlertChannel("webhook") == AlertChannel.WEBHOOK

    def test_alert_channel_from_string_invalid(self):
        """Test that invalid channel string raises ValueError."""
        with pytest.raises(ValueError):
            AlertChannel("sms")

    def test_alert_channel_all_values(self):
        """Test that all expected channels exist."""
        channels = list(AlertChannel)
        
        assert AlertChannel.EMAIL in channels
        assert AlertChannel.SLACK in channels
        assert AlertChannel.WEBHOOK in channels
        assert len(channels) == 3


# =============================================================================
# BatchType Enum Tests
# =============================================================================

class TestBatchType:
    """Tests for BatchType enum."""

    def test_batch_type_values(self):
        """Test BatchType enum values."""
        assert BatchType.REALTIME.value == "realtime"
        assert BatchType.HOURLY.value == "hourly"
        assert BatchType.DAILY.value == "daily"
        assert BatchType.WEEKLY.value == "weekly"

    def test_batch_type_from_string_valid(self):
        """Test creating BatchType from valid strings."""
        assert BatchType("realtime") == BatchType.REALTIME
        assert BatchType("hourly") == BatchType.HOURLY
        assert BatchType("daily") == BatchType.DAILY
        assert BatchType("weekly") == BatchType.WEEKLY

    def test_batch_type_from_string_invalid(self):
        """Test that invalid batch type string raises ValueError."""
        with pytest.raises(ValueError):
            BatchType("monthly")

    def test_batch_type_all_values(self):
        """Test that all expected batch types exist."""
        batch_types = list(BatchType)
        
        assert BatchType.REALTIME in batch_types
        assert BatchType.HOURLY in batch_types
        assert BatchType.DAILY in batch_types
        assert BatchType.WEEKLY in batch_types
        assert len(batch_types) == 4


# =============================================================================
# AlertResult Model Tests
# =============================================================================

class TestAlertResult:
    """Tests for AlertResult model."""

    def test_alert_result_default_values(self):
        """Test AlertResult with default values."""
        result = AlertResult()
        
        assert result.alert_id is None
        assert result.queued is False
        assert result.sent is False
        assert result.skipped is False
        assert result.skip_reason is None
        assert result.error is None

    def test_alert_result_success(self):
        """Test AlertResult for successful alert."""
        alert_id = uuid.uuid4()
        
        result = AlertResult(
            alert_id=alert_id,
            queued=True,
            sent=True,
            skipped=False
        )
        
        assert result.alert_id == alert_id
        assert result.queued is True
        assert result.sent is True
        assert result.skipped is False

    def test_alert_result_skipped(self):
        """Test AlertResult for skipped alert."""
        result = AlertResult(
            skipped=True,
            skip_reason="duplicate"
        )
        
        assert result.skipped is True
        assert result.skip_reason == "duplicate"

    def test_alert_result_error(self):
        """Test AlertResult for failed alert."""
        result = AlertResult(
            error="Connection timeout"
        )
        
        assert result.error == "Connection timeout"


# =============================================================================
# UserAlertConfig Model Tests
# =============================================================================

class TestUserAlertConfig:
    """Tests for UserAlertConfig model."""

    def test_user_alert_config_required_fields(self):
        """Test UserAlertConfig with required fields."""
        user_id = uuid.uuid4()
        niche_id = uuid.uuid4()
        
        config = UserAlertConfig(
            user_id=user_id,
            email="user@example.com",
            niche_id=niche_id
        )
        
        assert config.user_id == user_id
        assert config.email == "user@example.com"
        assert config.niche_id == niche_id

    def test_user_alert_config_defaults(self):
        """Test UserAlertConfig default values."""
        config = UserAlertConfig(
            user_id=uuid.uuid4(),
            email="user@example.com",
            niche_id=uuid.uuid4()
        )
        
        assert config.tier == Tier.FREE
        assert config.email_notifications is True
        assert config.alert_enabled is True
        assert config.velocity_threshold == 50
        assert config.integration_id is None
        assert config.integration_type is None
        assert config.integration_config is None

    def test_user_alert_config_velocity_threshold_validation(self):
        """Test velocity_threshold validation (0-100)."""
        # Valid values
        config = UserAlertConfig(
            user_id=uuid.uuid4(),
            email="user@example.com",
            niche_id=uuid.uuid4(),
            velocity_threshold=0
        )
        assert config.velocity_threshold == 0
        
        config.velocity_threshold = 100
        assert config.velocity_threshold == 100

    def test_user_alert_config_velocity_threshold_too_high(self):
        """Test that velocity_threshold > 100 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            UserAlertConfig(
                user_id=uuid.uuid4(),
                email="user@example.com",
                niche_id=uuid.uuid4(),
                velocity_threshold=101
            )
        
        assert "velocity_threshold" in str(exc_info.value)

    def test_user_alert_config_velocity_threshold_negative(self):
        """Test that negative velocity_threshold raises error."""
        with pytest.raises(ValidationError) as exc_info:
            UserAlertConfig(
                user_id=uuid.uuid4(),
                email="user@example.com",
                niche_id=uuid.uuid4(),
                velocity_threshold=-1
            )
        
        assert "velocity_threshold" in str(exc_info.value)

    def test_user_alert_config_with_integration(self):
        """Test UserAlertConfig with integration settings."""
        integration_id = uuid.uuid4()
        
        config = UserAlertConfig(
            user_id=uuid.uuid4(),
            email="user@example.com",
            niche_id=uuid.uuid4(),
            integration_id=integration_id,
            integration_type="slack",
            integration_config={
                "webhook_url": "https://hooks.slack.com/test",
                "channel": "#alerts"
            }
        )
        
        assert config.integration_id == integration_id
        assert config.integration_type == "slack"
        assert config.integration_config["webhook_url"] == "https://hooks.slack.com/test"


# =============================================================================
# RoutingDecision Model Tests
# =============================================================================

class TestRoutingDecision:
    """Tests for RoutingDecision model."""

    def test_routing_decision_creation(self):
        """Test RoutingDecision creation."""
        decision = RoutingDecision(
            is_immediate=True,
            delay_seconds=0,
            batch_type=BatchType.REALTIME,
            max_alerts_per_batch=0
        )
        
        assert decision.is_immediate is True
        assert decision.delay_seconds == 0
        assert decision.batch_type == BatchType.REALTIME
        assert decision.max_alerts_per_batch == 0

    def test_routing_decision_daily_batch(self):
        """Test RoutingDecision for daily batch."""
        decision = RoutingDecision(
            is_immediate=False,
            delay_seconds=24 * 3600,
            batch_type=BatchType.DAILY,
            max_alerts_per_batch=10
        )
        
        assert decision.is_immediate is False
        assert decision.delay_seconds == 86400
        assert decision.batch_type == BatchType.DAILY
        assert decision.max_alerts_per_batch == 10

    def test_routing_decision_delay_seconds_validation(self):
        """Test that negative delay_seconds raises error."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingDecision(
                is_immediate=False,
                delay_seconds=-1,
                batch_type=BatchType.DAILY,
                max_alerts_per_batch=10
            )
        
        assert "delay_seconds" in str(exc_info.value)

    def test_routing_decision_max_alerts_validation(self):
        """Test that negative max_alerts_per_batch raises error."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingDecision(
                is_immediate=False,
                delay_seconds=3600,
                batch_type=BatchType.HOURLY,
                max_alerts_per_batch=-1
            )
        
        assert "max_alerts_per_batch" in str(exc_info.value)


# =============================================================================
# TrendForAlert Model Tests
# =============================================================================

class TestTrendForAlert:
    """Tests for TrendForAlert model."""

    def test_trend_for_alert_creation(self):
        """Test TrendForAlert creation."""
        trend_id = uuid.uuid4()
        
        trend = TrendForAlert(
            id=trend_id,
            type="hashtag",
            name="#testtrend",
            velocity_score=85,
            saturation_percent=45,
            video_count_current=5000,
            growth_rate=12.5
        )
        
        assert trend.id == trend_id
        assert trend.type == "hashtag"
        assert trend.name == "#testtrend"
        assert trend.velocity_score == 85
        assert trend.saturation_percent == 45
        assert trend.video_count_current == 5000
        assert trend.growth_rate == 12.5

    def test_trend_for_alert_velocity_score_validation(self):
        """Test velocity_score validation (0-100)."""
        # Valid boundaries
        trend = TrendForAlert(
            id=uuid.uuid4(),
            type="sound",
            name="test sound",
            velocity_score=0,
            saturation_percent=50,
            video_count_current=100,
            growth_rate=5.0
        )
        assert trend.velocity_score == 0
        
        trend.velocity_score = 100
        assert trend.velocity_score == 100

    def test_trend_for_alert_velocity_score_too_high(self):
        """Test that velocity_score > 100 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            TrendForAlert(
                id=uuid.uuid4(),
                type="hashtag",
                name="#test",
                velocity_score=101,
                saturation_percent=50,
                video_count_current=100,
                growth_rate=5.0
            )
        
        assert "velocity_score" in str(exc_info.value)

    def test_trend_for_alert_saturation_validation(self):
        """Test saturation_percent validation (0-100)."""
        with pytest.raises(ValidationError) as exc_info:
            TrendForAlert(
                id=uuid.uuid4(),
                type="hashtag",
                name="#test",
                velocity_score=50,
                saturation_percent=101,
                video_count_current=100,
                growth_rate=5.0
            )
        
        assert "saturation_percent" in str(exc_info.value)

    def test_trend_for_alert_video_count_validation(self):
        """Test video_count_current validation (non-negative)."""
        with pytest.raises(ValidationError) as exc_info:
            TrendForAlert(
                id=uuid.uuid4(),
                type="hashtag",
                name="#test",
                velocity_score=50,
                saturation_percent=50,
                video_count_current=-1,
                growth_rate=5.0
            )
        
        assert "video_count_current" in str(exc_info.value)

    def test_trend_for_alert_growth_rate_validation(self):
        """Test growth_rate validation (non-negative)."""
        with pytest.raises(ValidationError) as exc_info:
            TrendForAlert(
                id=uuid.uuid4(),
                type="hashtag",
                name="#test",
                velocity_score=50,
                saturation_percent=50,
                video_count_current=100,
                growth_rate=-1.0
            )
        
        assert "growth_rate" in str(exc_info.value)

    def test_trend_for_alert_defaults(self):
        """Test TrendForAlert default values."""
        trend = TrendForAlert(
            id=uuid.uuid4(),
            type="format",
            name="test format",
            velocity_score=75,
            saturation_percent=30,
            video_count_current=2000,
            growth_rate=8.5
        )
        
        assert trend.niche_name is None
        assert trend.status == "emerging"
        assert trend.window_hours == "6-8"
        assert isinstance(trend.first_detected_at, datetime)


# =============================================================================
# DigestEntry Model Tests
# =============================================================================

class TestDigestEntry:
    """Tests for DigestEntry model."""

    def test_digest_entry_creation(self):
        """Test DigestEntry creation."""
        entry = DigestEntry(
            trend_id=str(uuid.uuid4()),
            trend_name="#testtrend",
            velocity_score=80,
            saturation_percent=40,
            growth_rate=15.0
        )
        
        assert entry.trend_name == "#testtrend"
        assert entry.velocity_score == 80
        assert entry.saturation_percent == 40
        assert entry.growth_rate == 15.0

    def test_digest_entry_validation(self):
        """Test DigestEntry field validation."""
        # Test velocity_score > 100
        with pytest.raises(ValidationError) as exc_info:
            DigestEntry(
                trend_id="test",
                trend_name="#test",
                velocity_score=101,
                saturation_percent=50,
                growth_rate=5.0
            )
        assert "velocity_score" in str(exc_info.value)

        # Test saturation_percent > 100
        with pytest.raises(ValidationError) as exc_info:
            DigestEntry(
                trend_id="test",
                trend_name="#test",
                velocity_score=50,
                saturation_percent=101,
                growth_rate=5.0
            )
        assert "saturation_percent" in str(exc_info.value)

        # Test negative growth_rate
        with pytest.raises(ValidationError) as exc_info:
            DigestEntry(
                trend_id="test",
                trend_name="#test",
                velocity_score=50,
                saturation_percent=50,
                growth_rate=-1.0
            )
        assert "growth_rate" in str(exc_info.value)


# =============================================================================
# EngagementEvent Model Tests
# =============================================================================

class TestEngagementEvent:
    """Tests for EngagementEvent model."""

    def test_engagement_event_creation(self):
        """Test EngagementEvent creation."""
        alert_id = uuid.uuid4()
        
        event = EngagementEvent(
            alert_id=alert_id,
            event_type="open",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1"
        )
        
        assert event.alert_id == alert_id
        assert event.event_type == "open"
        assert event.user_agent == "Mozilla/5.0"
        assert event.ip_address == "192.168.1.1"
        assert isinstance(event.timestamp, datetime)

    def test_engagement_event_defaults(self):
        """Test EngagementEvent default values."""
        event = EngagementEvent(
            alert_id=uuid.uuid4(),
            event_type="click"
        )
        
        assert event.user_agent is None
        assert event.ip_address is None
        assert event.metadata == {}


# =============================================================================
# EngagementStats Model Tests
# =============================================================================

class TestEngagementStats:
    """Tests for EngagementStats model."""

    def test_engagement_stats_defaults(self):
        """Test EngagementStats default values."""
        stats = EngagementStats()
        
        assert stats.total_alerts == 0
        assert stats.opened == 0
        assert stats.clicked == 0
        assert stats.open_rate == 0.0
        assert stats.click_rate == 0.0

    def test_engagement_stats_validation(self):
        """Test EngagementStats field validation."""
        # Test negative total_alerts
        with pytest.raises(ValidationError) as exc_info:
            EngagementStats(total_alerts=-1)
        assert "total_alerts" in str(exc_info.value)

        # Test open_rate > 100
        with pytest.raises(ValidationError) as exc_info:
            EngagementStats(open_rate=101.0)
        assert "open_rate" in str(exc_info.value)

        # Test negative click_rate
        with pytest.raises(ValidationError) as exc_info:
            EngagementStats(click_rate=-1.0)
        assert "click_rate" in str(exc_info.value)


# =============================================================================
# SlackMessage Model Tests
# =============================================================================

class TestSlackMessage:
    """Tests for SlackMessage model."""

    def test_slack_message_defaults(self):
        """Test SlackMessage default values."""
        message = SlackMessage()
        
        assert message.blocks == []
        assert message.text is None

    def test_slack_message_with_content(self):
        """Test SlackMessage with content."""
        message = SlackMessage(
            blocks=[
                {"type": "header", "text": {"type": "plain_text", "text": "Alert"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": "Trend detected"}}
            ],
            text="Trend Alert: #viraltrend"
        )
        
        assert len(message.blocks) == 2
        assert message.text == "Trend Alert: #viraltrend"


# =============================================================================
# EmailContent Model Tests
# =============================================================================

class TestEmailContent:
    """Tests for EmailContent model."""

    def test_email_content_creation(self):
        """Test EmailContent creation."""
        email = EmailContent(
            subject="Trend Alert: #viraltrend",
            html_body="<h1>Trend Alert</h1><p>#viraltrend is trending!</p>",
            text_body="Trend Alert: #viraltrend is trending!"
        )
        
        assert email.subject == "Trend Alert: #viraltrend"
        assert "<h1>" in email.html_body
        assert "#viraltrend is trending!" in email.text_body

    def test_email_content_optional_tracking(self):
        """Test EmailContent with optional tracking fields."""
        email = EmailContent(
            subject="Test",
            html_body="<p>Test</p>",
            text_body="Test",
            tracking_pixel_url="https://trendscope.io/pixel/123",
            tracking_link_base="https://trendscope.io/click"
        )
        
        assert email.tracking_pixel_url == "https://trendscope.io/pixel/123"
        assert email.tracking_link_base == "https://trendscope.io/click"

    def test_email_content_missing_required(self):
        """Test that missing required fields raise error."""
        with pytest.raises(ValidationError) as exc_info:
            EmailContent(
                html_body="<p>Test</p>",
                text_body="Test"
            )
        assert "subject" in str(exc_info.value)


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestModelEdgeCases:
    """Edge case tests for all models."""

    def test_empty_string_email(self):
        """Test that empty email string is accepted (validated at higher level)."""
        config = UserAlertConfig(
            user_id=uuid.uuid4(),
            email="",
            niche_id=uuid.uuid4()
        )
        assert config.email == ""

    def test_very_long_strings(self):
        """Test models with very long strings."""
        long_name = "#" + "a" * 1000
        
        trend = TrendForAlert(
            id=uuid.uuid4(),
            type="hashtag",
            name=long_name,
            velocity_score=50,
            saturation_percent=50,
            video_count_current=100,
            growth_rate=5.0
        )
        
        assert trend.name == long_name

    def test_special_characters_in_strings(self):
        """Test models with special characters."""
        special_name = "#test💯🔥<script>alert('xss')</script>"
        
        trend = TrendForAlert(
            id=uuid.uuid4(),
            type="hashtag",
            name=special_name,
            velocity_score=50,
            saturation_percent=50,
            video_count_current=100,
            growth_rate=5.0
        )
        
        assert trend.name == special_name

    def test_uuid_string_conversion(self):
        """Test that UUIDs can be created from strings."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        
        alert = Alert(
            user_id=uuid.UUID(uuid_str),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.EMAIL
        )
        
        assert str(alert.user_id) == uuid_str

    def test_datetime_timezone_awareness(self):
        """Test datetime handling."""
        # UTC now should work
        now = datetime.utcnow()
        
        alert = Alert(
            user_id=uuid.uuid4(),
            trend_id=uuid.uuid4(),
            channel=AlertChannel.EMAIL,
            sent_at=now
        )
        
        assert alert.sent_at == now
