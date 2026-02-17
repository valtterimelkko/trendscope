"""
Unit tests for System Health Alerts.

Tests AlertNotifier, SystemHealthAlerter, AlertRule, and AlertEvent.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from monitoring.alerts import (
    AlertSeverity,
    AlertRule,
    AlertEvent,
    AlertNotifier,
    SystemHealthAlerter,
    DEFAULT_ALERT_RULES,
    get_system_health_alerter,
)
from monitoring.config import AlertThresholds, DEFAULT_ALERT_THRESHOLDS


class TestAlertSeverity:
    """Test AlertSeverity enum."""

    def test_severity_values(self):
        """AlertSeverity should have correct values."""
        assert AlertSeverity.INFO == "info"
        assert AlertSeverity.WARNING == "warning"
        assert AlertSeverity.CRITICAL == "critical"


class TestAlertRule:
    """Test AlertRule model."""

    def test_alert_rule_creation(self):
        """Should create AlertRule with all fields."""
        rule = AlertRule(
            name="TestAlert",
            description="Test alert description",
            severity=AlertSeverity.WARNING,
            condition="metric > 100",
            for_duration_seconds=300,
            cooldown_seconds=600,
            enabled=True,
            labels={"component": "test"},
        )
        
        assert rule.name == "TestAlert"
        assert rule.description == "Test alert description"
        assert rule.severity == AlertSeverity.WARNING
        assert rule.condition == "metric > 100"
        assert rule.for_duration_seconds == 300
        assert rule.cooldown_seconds == 600
        assert rule.enabled is True
        assert rule.labels == {"component": "test"}

    def test_alert_rule_defaults(self):
        """Should use defaults for optional fields."""
        rule = AlertRule(
            name="TestAlert",
            description="Test",
            severity=AlertSeverity.INFO,
            condition="metric > 0",
        )
        
        assert rule.for_duration_seconds == 0
        assert rule.cooldown_seconds == 300
        assert rule.enabled is True
        assert rule.labels == {}


class TestAlertEvent:
    """Test AlertEvent model."""

    def test_alert_event_creation(self):
        """Should create AlertEvent with all fields."""
        event = AlertEvent(
            rule_name="TestAlert",
            severity=AlertSeverity.WARNING,
            message="Something happened",
            details={"key": "value"},
        )
        
        assert event.rule_name == "TestAlert"
        assert event.severity == AlertSeverity.WARNING
        assert event.message == "Something happened"
        assert event.details == {"key": "value"}
        assert isinstance(event.timestamp, datetime)
        assert event.resolved is False
        assert event.resolved_at is None

    def test_alert_event_defaults(self):
        """Should use defaults for optional fields."""
        event = AlertEvent(
            rule_name="TestAlert",
            severity=AlertSeverity.INFO,
            message="Test",
        )
        
        assert event.details == {}
        assert event.resolved is False
        assert event.resolved_at is None


class TestAlertNotifier:
    """Test AlertNotifier class."""

    def test_notifier_initialization(self):
        """Should initialize with configuration."""
        notifier = AlertNotifier(
            slack_webhook_url="https://hooks.slack.com/test",
            email_recipients=["test@example.com"],
        )
        
        assert notifier.slack_webhook_url == "https://hooks.slack.com/test"
        assert notifier.email_recipients == ["test@example.com"]

    def test_notifier_no_channels(self):
        """Should work with no channels configured."""
        notifier = AlertNotifier()
        
        assert notifier.slack_webhook_url is None
        assert notifier.email_recipients == []

    @pytest.mark.asyncio
    async def test_notify_slack_only(self):
        """Should send Slack notification when configured."""
        notifier = AlertNotifier(slack_webhook_url="https://hooks.slack.com/test")
        
        alert = AlertEvent(
            rule_name="TestAlert",
            severity=AlertSeverity.WARNING,
            message="Test message",
        )
        
        # Mock the Slack sending
        with patch.object(notifier, '_send_slack', new_callable=AsyncMock, return_value=True):
            result = await notifier.notify(alert)
            
            assert result is True

    @pytest.mark.asyncio
    async def test_notify_slack_failure(self):
        """Should handle Slack failure gracefully."""
        notifier = AlertNotifier(slack_webhook_url="https://hooks.slack.com/test")
        
        alert = AlertEvent(
            rule_name="TestAlert",
            severity=AlertSeverity.WARNING,
            message="Test message",
        )
        
        # Mock failed Slack sending
        with patch.object(notifier, '_send_slack', new_callable=AsyncMock, return_value=False):
            result = await notifier.notify(alert)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_send_slack_success(self):
        """Should successfully send Slack message."""
        notifier = AlertNotifier(slack_webhook_url="https://hooks.slack.com/test")
        
        alert = AlertEvent(
            rule_name="TestAlert",
            severity=AlertSeverity.WARNING,
            message="Test message",
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await notifier._send_slack(alert)
            
            assert result is True

    @pytest.mark.asyncio
    async def test_send_slack_no_webhook(self):
        """Should return False when no webhook configured."""
        notifier = AlertNotifier()
        
        alert = AlertEvent(
            rule_name="TestAlert",
            severity=AlertSeverity.WARNING,
            message="Test message",
        )
        
        result = await notifier._send_slack(alert)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_send_slack_error(self):
        """Should handle Slack API errors."""
        notifier = AlertNotifier(slack_webhook_url="https://hooks.slack.com/test")
        
        alert = AlertEvent(
            rule_name="TestAlert",
            severity=AlertSeverity.WARNING,
            message="Test message",
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=Exception("Network error"))
            
            result = await notifier._send_slack(alert)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_send_email(self):
        """Should handle email sending (placeholder)."""
        notifier = AlertNotifier(email_recipients=["test@example.com"])
        
        alert = AlertEvent(
            rule_name="TestAlert",
            severity=AlertSeverity.WARNING,
            message="Test message",
        )
        
        result = await notifier._send_email(alert)
        
        assert result is True  # Currently returns True as placeholder


class TestSystemHealthAlerter:
    """Test SystemHealthAlerter class."""

    def test_alerter_initialization(self):
        """Should initialize with configuration."""
        alerter = SystemHealthAlerter()
        
        assert alerter.thresholds is not None
        assert alerter.rules is not None
        assert alerter.notifier is not None
        assert alerter._last_alert_time == {}
        assert alerter._active_alerts == {}

    def test_alerter_with_custom_thresholds(self):
        """Should accept custom thresholds."""
        custom_thresholds = AlertThresholds(
            api_error_rate_threshold=0.1,
            scraper_error_rate_threshold=0.2,
        )
        
        alerter = SystemHealthAlerter(thresholds=custom_thresholds)
        
        assert alerter.thresholds.api_error_rate_threshold == 0.1
        assert alerter.thresholds.scraper_error_rate_threshold == 0.2

    def test_configure_slack(self):
        """Should configure Slack webhook."""
        alerter = SystemHealthAlerter()
        
        alerter.configure_slack("https://hooks.slack.com/new")
        
        assert alerter.notifier.slack_webhook_url == "https://hooks.slack.com/new"

    def test_configure_email(self):
        """Should configure email recipients."""
        alerter = SystemHealthAlerter()
        
        alerter.configure_email(["admin@example.com", "ops@example.com"])
        
        assert alerter.notifier.email_recipients == ["admin@example.com", "ops@example.com"]

    def test_can_alert_first_time(self):
        """Should allow alert on first trigger."""
        alerter = SystemHealthAlerter()
        
        assert alerter._can_alert("test_rule") is True

    def test_can_alert_cooldown_active(self):
        """Should block alert during cooldown."""
        alerter = SystemHealthAlerter()
        
        # Record an alert
        alert = AlertEvent(
            rule_name="test_rule",
            severity=AlertSeverity.WARNING,
            message="Test",
        )
        alerter._record_alert("test_rule", alert)
        
        # Should not allow another alert immediately
        assert alerter._can_alert("test_rule") is False

    def test_can_alert_cooldown_expired(self):
        """Should allow alert after cooldown expires."""
        alerter = SystemHealthAlerter()
        
        # Add rule with short cooldown
        alerter.rules["test_rule"] = AlertRule(
            name="test_rule",
            description="Test",
            severity=AlertSeverity.WARNING,
            condition="test",
            cooldown_seconds=0,  # No cooldown
        )
        
        # Record an alert in the past
        alert = AlertEvent(
            rule_name="test_rule",
            severity=AlertSeverity.WARNING,
            message="Test",
        )
        alerter._last_alert_time["test_rule"] = datetime.utcnow() - timedelta(seconds=1)
        
        # Should allow another alert
        assert alerter._can_alert("test_rule") is True

    def test_record_alert(self):
        """Should record alert and timestamp."""
        alerter = SystemHealthAlerter()
        
        alert = AlertEvent(
            rule_name="test_rule",
            severity=AlertSeverity.WARNING,
            message="Test",
        )
        
        alerter._record_alert("test_rule", alert)
        
        assert "test_rule" in alerter._last_alert_time
        assert "test_rule" in alerter._active_alerts

    def test_get_active_alerts(self):
        """Should return list of active alerts."""
        alerter = SystemHealthAlerter()
        
        alert1 = AlertEvent(rule_name="alert1", severity=AlertSeverity.WARNING, message="Test 1")
        alert2 = AlertEvent(rule_name="alert2", severity=AlertSeverity.CRITICAL, message="Test 2")
        
        alerter._active_alerts["alert1"] = alert1
        alerter._active_alerts["alert2"] = alert2
        
        active = alerter.get_active_alerts()
        
        assert len(active) == 2
        assert alert1 in active
        assert alert2 in active

    def test_resolve_alert(self):
        """Should resolve active alert."""
        alerter = SystemHealthAlerter()
        
        alert = AlertEvent(
            rule_name="test_alert",
            severity=AlertSeverity.WARNING,
            message="Test",
        )
        alerter._active_alerts["test_alert"] = alert
        
        resolved = alerter.resolve_alert("test_alert")
        
        assert resolved is not None
        assert resolved.resolved is True
        assert resolved.resolved_at is not None
        assert "test_alert" not in alerter._active_alerts

    def test_resolve_nonexistent_alert(self):
        """Should return None for nonexistent alert."""
        alerter = SystemHealthAlerter()
        
        resolved = alerter.resolve_alert("nonexistent")
        
        assert resolved is None


class TestDefaultAlertRules:
    """Test default alert rules."""

    def test_scraper_down_rule_exists(self):
        """Should have ScraperDown rule."""
        assert "scraper_down" in DEFAULT_ALERT_RULES
        rule = DEFAULT_ALERT_RULES["scraper_down"]
        assert rule.severity == AlertSeverity.CRITICAL
        assert rule.for_duration_seconds == 600

    def test_scraper_circuit_breaker_rule_exists(self):
        """Should have ScraperCircuitBreakerOpen rule."""
        assert "scraper_circuit_breaker_open" in DEFAULT_ALERT_RULES
        rule = DEFAULT_ALERT_RULES["scraper_circuit_breaker_open"]
        assert rule.severity == AlertSeverity.WARNING

    def test_api_high_latency_rule_exists(self):
        """Should have APIHighLatency rule."""
        assert "api_high_latency" in DEFAULT_ALERT_RULES
        rule = DEFAULT_ALERT_RULES["api_high_latency"]
        assert rule.severity == AlertSeverity.WARNING

    def test_api_high_error_rate_rule_exists(self):
        """Should have APIHighErrorRate rule."""
        assert "api_high_error_rate" in DEFAULT_ALERT_RULES
        rule = DEFAULT_ALERT_RULES["api_high_error_rate"]
        assert rule.severity == AlertSeverity.CRITICAL

    def test_alert_delivery_failures_rule_exists(self):
        """Should have AlertDeliveryFailures rule."""
        assert "alert_delivery_failures" in DEFAULT_ALERT_RULES
        rule = DEFAULT_ALERT_RULES["alert_delivery_failures"]
        assert rule.severity == AlertSeverity.CRITICAL

    def test_redis_down_rule_exists(self):
        """Should have RedisDown rule."""
        assert "redis_down" in DEFAULT_ALERT_RULES
        rule = DEFAULT_ALERT_RULES["redis_down"]
        assert rule.severity == AlertSeverity.CRITICAL


class TestDefaultAlertThresholds:
    """Test default alert thresholds."""

    def test_scraper_thresholds(self):
        """Should have scraper thresholds."""
        assert DEFAULT_ALERT_THRESHOLDS.scraper_error_rate_threshold == 0.1
        assert DEFAULT_ALERT_THRESHOLDS.scraper_circuit_breaker_open_seconds == 300

    def test_api_thresholds(self):
        """Should have API thresholds."""
        assert DEFAULT_ALERT_THRESHOLDS.api_latency_p95_threshold_seconds == 1.0
        assert DEFAULT_ALERT_THRESHOLDS.api_error_rate_threshold == 0.05

    def test_trend_detection_thresholds(self):
        """Should have trend detection thresholds."""
        assert DEFAULT_ALERT_THRESHOLDS.trend_detection_latency_threshold_seconds == 600

    def test_alert_delivery_thresholds(self):
        """Should have alert delivery thresholds."""
        assert DEFAULT_ALERT_THRESHOLDS.alert_failure_rate_threshold == 0.1
        assert DEFAULT_ALERT_THRESHOLDS.alert_pending_threshold == 100

    def test_infrastructure_thresholds(self):
        """Should have infrastructure thresholds."""
        assert DEFAULT_ALERT_THRESHOLDS.redis_memory_utilization_threshold == 0.8
        assert DEFAULT_ALERT_THRESHOLDS.database_connection_utilization_threshold == 0.8


class TestGetSystemHealthAlerter:
    """Test the get_system_health_alerter singleton function."""

    def test_singleton_instance(self):
        """Should return the same instance."""
        # Reset singleton
        import monitoring.alerts as alerts_module
        alerts_module._system_health_alerter = None
        
        alerter1 = get_system_health_alerter()
        alerter2 = get_system_health_alerter()
        
        assert alerter1 is alerter2

    def test_returns_system_health_alerter(self):
        """Should return a SystemHealthAlerter instance."""
        # Reset singleton
        import monitoring.alerts as alerts_module
        alerts_module._system_health_alerter = None
        
        alerter = get_system_health_alerter()
        
        assert isinstance(alerter, SystemHealthAlerter)
