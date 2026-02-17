"""
System Health Alerts

Monitors system health and generates alerts when conditions are met.
These are internal system alerts (not user trend alerts).

Alert conditions include:
- Scraper down or circuit breaker open
- API error rate or latency too high
- Trend detection lagging
- Alert delivery failures
- Redis/Database connectivity issues

Alerts are sent via Slack or other configured channels.
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Awaitable
from pydantic import BaseModel, Field
import structlog

from monitoring.config import AlertThresholds, DEFAULT_ALERT_THRESHOLDS
from monitoring.health_aggregator import HealthStatus


logger = structlog.get_logger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertRule(BaseModel):
    """Definition of an alert rule."""

    name: str = Field(
        ...,
        description="Unique rule name",
    )
    description: str = Field(
        ...,
        description="Human-readable description",
    )
    severity: AlertSeverity = Field(
        ...,
        description="Alert severity level",
    )
    condition: str = Field(
        ...,
        description="Condition expression (for documentation)",
    )
    for_duration_seconds: int = Field(
        default=0,
        description="How long condition must be true before alerting",
    )
    cooldown_seconds: int = Field(
        default=300,
        description="Minimum time between alerts for this rule",
    )
    enabled: bool = Field(
        default=True,
        description="Whether this rule is active",
    )
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional labels for routing",
    )


class AlertEvent(BaseModel):
    """An alert event that was triggered."""

    rule_name: str = Field(
        ...,
        description="Name of the rule that triggered",
    )
    severity: AlertSeverity = Field(
        ...,
        description="Alert severity",
    )
    message: str = Field(
        ...,
        description="Alert message",
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional details",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the alert was triggered",
    )
    resolved: bool = Field(
        default=False,
        description="Whether the alert has been resolved",
    )
    resolved_at: Optional[datetime] = Field(
        default=None,
        description="When the alert was resolved",
    )


# Predefined alert rules
DEFAULT_ALERT_RULES: Dict[str, AlertRule] = {
    "scraper_down": AlertRule(
        name="ScraperDown",
        description="Scraper service is down or unreachable",
        severity=AlertSeverity.CRITICAL,
        condition="up{job='scraper'} == 0 for 10m",
        for_duration_seconds=600,
        cooldown_seconds=300,
        labels={"component": "scraper"},
    ),
    "scraper_circuit_breaker_open": AlertRule(
        name="ScraperCircuitBreakerOpen",
        description="Scraper circuit breaker has been open for 5 minutes",
        severity=AlertSeverity.WARNING,
        condition="scraper_circuit_breaker_state == 1 for 5m",
        for_duration_seconds=300,
        cooldown_seconds=600,
        labels={"component": "scraper"},
    ),
    "scraper_high_error_rate": AlertRule(
        name="ScraperHighErrorRate",
        description="Scraper error rate is high",
        severity=AlertSeverity.WARNING,
        condition="rate(scraper_errors_total[5m]) > 0.1 for 10m",
        for_duration_seconds=600,
        cooldown_seconds=300,
        labels={"component": "scraper"},
    ),
    "api_high_latency": AlertRule(
        name="APIHighLatency",
        description="API P95 latency exceeds 1 second",
        severity=AlertSeverity.WARNING,
        condition="histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m])) > 1.0 for 10m",
        for_duration_seconds=600,
        cooldown_seconds=300,
        labels={"component": "api"},
    ),
    "api_high_error_rate": AlertRule(
        name="APIHighErrorRate",
        description="API error rate exceeds 5%",
        severity=AlertSeverity.CRITICAL,
        condition="rate(api_requests_total{status_code=~'5..'}[5m]) / rate(api_requests_total[5m]) > 0.05 for 5m",
        for_duration_seconds=300,
        cooldown_seconds=180,
        labels={"component": "api"},
    ),
    "trend_detection_lagging": AlertRule(
        name="TrendDetectionLagging",
        description="Trend detection latency exceeds 10 minutes",
        severity=AlertSeverity.WARNING,
        condition="avg(trend_detection_latency_seconds) > 600 for 15m",
        for_duration_seconds=900,
        cooldown_seconds=600,
        labels={"component": "detection"},
    ),
    "no_trends_detected": AlertRule(
        name="NoTrendsDetected",
        description="No trends detected in the last hour",
        severity=AlertSeverity.WARNING,
        condition="increase(trends_detected_total[1h]) == 0 for 2h",
        for_duration_seconds=7200,
        cooldown_seconds=3600,
        labels={"component": "detection"},
    ),
    "alert_delivery_failures": AlertRule(
        name="AlertDeliveryFailures",
        description="Alert delivery failure rate is high",
        severity=AlertSeverity.CRITICAL,
        condition="rate(alert_delivery_failures_total[5m]) > 0.1 for 10m",
        for_duration_seconds=600,
        cooldown_seconds=300,
        labels={"component": "alerts"},
    ),
    "high_pending_alerts": AlertRule(
        name="HighPendingAlerts",
        description="High number of pending alerts",
        severity=AlertSeverity.WARNING,
        condition="alerts_pending > 100 for 15m",
        for_duration_seconds=900,
        cooldown_seconds=600,
        labels={"component": "alerts"},
    ),
    "redis_memory_high": AlertRule(
        name="RedisMemoryHigh",
        description="Redis memory usage exceeds 80%",
        severity=AlertSeverity.WARNING,
        condition="redis_memory_used_bytes / redis_memory_max_bytes > 0.8 for 10m",
        for_duration_seconds=600,
        cooldown_seconds=900,
        labels={"component": "infrastructure"},
    ),
    "redis_down": AlertRule(
        name="RedisDown",
        description="Redis is unreachable",
        severity=AlertSeverity.CRITICAL,
        condition="up{job='redis'} == 0 for 5m",
        for_duration_seconds=300,
        cooldown_seconds=180,
        labels={"component": "infrastructure"},
    ),
    "database_connections_exhausted": AlertRule(
        name="DatabaseConnectionsExhausted",
        description="Database connection pool near capacity",
        severity=AlertSeverity.WARNING,
        condition="pg_stat_activity_count / pg_settings_max_connections > 0.8 for 10m",
        for_duration_seconds=600,
        cooldown_seconds=600,
        labels={"component": "infrastructure"},
    ),
}


class AlertNotifier:
    """Sends alert notifications to configured channels."""

    def __init__(
        self,
        slack_webhook_url: Optional[str] = None,
        email_recipients: Optional[List[str]] = None,
    ):
        """Initialize the notifier.

        Args:
            slack_webhook_url: Slack webhook URL for notifications
            email_recipients: List of email addresses for notifications
        """
        self.slack_webhook_url = slack_webhook_url
        self.email_recipients = email_recipients or []

    async def notify(self, alert: AlertEvent) -> bool:
        """Send alert notification.

        Args:
            alert: The alert event

        Returns:
            True if notification was sent successfully
        """
        success = False

        if self.slack_webhook_url:
            success = await self._send_slack(alert)

        if self.email_recipients:
            success = await self._send_email(alert) or success

        return success

    async def _send_slack(self, alert: AlertEvent) -> bool:
        """Send alert to Slack.

        Args:
            alert: The alert event

        Returns:
            True if sent successfully
        """
        if not self.slack_webhook_url:
            return False

        import httpx

        # Build Slack message
        color = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9900",
            AlertSeverity.CRITICAL: "#ff0000",
        }.get(alert.severity, "#808080")

        emoji = {
            AlertSeverity.INFO: ":information_source:",
            AlertSeverity.WARNING: ":warning:",
            AlertSeverity.CRITICAL: ":rotating_light:",
        }.get(alert.severity, ":bell:")

        status_text = "Resolved" if alert.resolved else "Triggered"
        message = {
            "attachments": [
                {
                    "color": color if not alert.resolved else "#36a64f",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{emoji} {alert.rule_name} - {status_text}",
                            },
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Severity:*\n{alert.severity.value.upper()}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Time:*\n{alert.timestamp.isoformat()}",
                                },
                            ],
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Message:*\n{alert.message}",
                            },
                        },
                    ],
                }
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.slack_webhook_url,
                    json=message,
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(
                "slack_alert_failed",
                alert=alert.rule_name,
                error=str(e),
            )
            return False

    async def _send_email(self, alert: AlertEvent) -> bool:
        """Send alert via email.

        Args:
            alert: The alert event

        Returns:
            True if sent successfully
        """
        # Email sending would be implemented here
        # For now, just log it
        logger.info(
            "alert_email_would_be_sent",
            alert=alert.rule_name,
            recipients=self.email_recipients,
        )
        return True


class SystemHealthAlerter:
    """Monitors system health and generates alerts.

    Evaluates health check results and metric values against
    alert rules, and sends notifications when conditions are met.
    """

    def __init__(
        self,
        thresholds: Optional[AlertThresholds] = None,
        rules: Optional[Dict[str, AlertRule]] = None,
        notifier: Optional[AlertNotifier] = None,
    ):
        """Initialize the health alerter.

        Args:
            thresholds: Alert thresholds configuration
            rules: Alert rules to evaluate
            notifier: Alert notifier for sending notifications
        """
        self.thresholds = thresholds or DEFAULT_ALERT_THRESHOLDS
        self.rules = rules or DEFAULT_ALERT_RULES
        self.notifier = notifier or AlertNotifier()

        # Track last alert times for cooldown
        self._last_alert_time: Dict[str, datetime] = {}

        # Track condition start times for duration requirements
        self._condition_start: Dict[str, datetime] = {}

        # Active alerts
        self._active_alerts: Dict[str, AlertEvent] = {}

    def configure_slack(self, webhook_url: str) -> None:
        """Configure Slack notifications.

        Args:
            webhook_url: Slack webhook URL
        """
        self.notifier.slack_webhook_url = webhook_url

    def configure_email(self, recipients: List[str]) -> None:
        """Configure email notifications.

        Args:
            recipients: List of email addresses
        """
        self.notifier.email_recipients = recipients

    async def evaluate_health(
        self,
        health_status: Dict[str, Any],
    ) -> List[AlertEvent]:
        """Evaluate health status and generate alerts.

        Args:
            health_status: Current health status from health aggregator

        Returns:
            List of new alert events
        """
        new_alerts: List[AlertEvent] = []

        # Check overall health
        if not health_status.get("overall_healthy", True):
            # Check each component
            services = health_status.get("services", {})
            for service_name, service_info in services.items():
                if not service_info.get("healthy", True):
                    alert = await self._check_component_alert(
                        service_name,
                        service_info,
                    )
                    if alert:
                        new_alerts.append(alert)

        return new_alerts

    async def evaluate_metrics(
        self,
        metrics: Dict[str, Any],
    ) -> List[AlertEvent]:
        """Evaluate metrics and generate alerts.

        Args:
            metrics: Current metrics from aggregator

        Returns:
            List of new alert events
        """
        new_alerts: List[AlertEvent] = []

        # Check scraper metrics
        scraper_metrics = metrics.get("scraper", {})
        if scraper_metrics:
            alert = await self._check_scraper_metrics(scraper_metrics)
            if alert:
                new_alerts.append(alert)

        # Check API metrics
        api_metrics = metrics.get("api", {})
        if api_metrics:
            alert = await self._check_api_metrics(api_metrics)
            if alert:
                new_alerts.append(alert)

        # Check alert delivery metrics
        alert_metrics = metrics.get("alerts", {})
        if alert_metrics:
            alert = await self._check_alert_metrics(alert_metrics)
            if alert:
                new_alerts.append(alert)

        return new_alerts

    async def _check_component_alert(
        self,
        component_name: str,
        component_info: Dict[str, Any],
    ) -> Optional[AlertEvent]:
        """Check if a component needs an alert.

        Args:
            component_name: Name of the component
            component_info: Component health info

        Returns:
            AlertEvent if alert triggered, None otherwise
        """
        rule_name = f"{component_name}_unhealthy"

        # Check cooldown
        if not self._can_alert(rule_name):
            return None

        # Create alert
        alert = AlertEvent(
            rule_name=rule_name,
            severity=AlertSeverity.CRITICAL,
            message=f"Component {component_name} is unhealthy",
            details={
                "component_type": component_info.get("type", "unknown"),
                "last_seen": component_info.get("last_seen"),
            },
        )

        # Record and notify
        self._record_alert(rule_name, alert)
        await self.notifier.notify(alert)

        return alert

    async def _check_scraper_metrics(
        self,
        metrics: Dict[str, Any],
    ) -> Optional[AlertEvent]:
        """Check scraper metrics for alert conditions.

        Args:
            metrics: Scraper metrics

        Returns:
            AlertEvent if triggered
        """
        error_rate = metrics.get("error_rate", 0)

        if error_rate > self.thresholds.scraper_error_rate_threshold:
            rule_name = "scraper_high_error_rate"
            if self._can_alert(rule_name):
                alert = AlertEvent(
                    rule_name=rule_name,
                    severity=AlertSeverity.WARNING,
                    message=f"Scraper error rate is high: {error_rate:.2%}",
                    details=metrics,
                )
                self._record_alert(rule_name, alert)
                await self.notifier.notify(alert)
                return alert

        return None

    async def _check_api_metrics(
        self,
        metrics: Dict[str, Any],
    ) -> Optional[AlertEvent]:
        """Check API metrics for alert conditions.

        Args:
            metrics: API metrics

        Returns:
            AlertEvent if triggered
        """
        error_rate = metrics.get("error_rate", 0)
        p95_latency = metrics.get("p95_latency_ms", 0) / 1000

        if error_rate > self.thresholds.api_error_rate_threshold:
            rule_name = "api_high_error_rate"
            if self._can_alert(rule_name):
                alert = AlertEvent(
                    rule_name=rule_name,
                    severity=AlertSeverity.CRITICAL,
                    message=f"API error rate is high: {error_rate:.2%}",
                    details=metrics,
                )
                self._record_alert(rule_name, alert)
                await self.notifier.notify(alert)
                return alert

        if p95_latency > self.thresholds.api_latency_p95_threshold_seconds:
            rule_name = "api_high_latency"
            if self._can_alert(rule_name):
                alert = AlertEvent(
                    rule_name=rule_name,
                    severity=AlertSeverity.WARNING,
                    message=f"API P95 latency is high: {p95_latency:.3f}s",
                    details=metrics,
                )
                self._record_alert(rule_name, alert)
                await self.notifier.notify(alert)
                return alert

        return None

    async def _check_alert_metrics(
        self,
        metrics: Dict[str, Any],
    ) -> Optional[AlertEvent]:
        """Check alert pipeline metrics for alert conditions.

        Args:
            metrics: Alert metrics

        Returns:
            AlertEvent if triggered
        """
        failure_rate = metrics.get("failure_rate", 0)
        pending = metrics.get("pending", 0)

        if failure_rate > self.thresholds.alert_failure_rate_threshold:
            rule_name = "alert_delivery_failures"
            if self._can_alert(rule_name):
                alert = AlertEvent(
                    rule_name=rule_name,
                    severity=AlertSeverity.CRITICAL,
                    message=f"Alert delivery failure rate is high: {failure_rate:.2%}",
                    details=metrics,
                )
                self._record_alert(rule_name, alert)
                await self.notifier.notify(alert)
                return alert

        if pending > self.thresholds.alert_pending_threshold:
            rule_name = "high_pending_alerts"
            if self._can_alert(rule_name):
                alert = AlertEvent(
                    rule_name=rule_name,
                    severity=AlertSeverity.WARNING,
                    message=f"High number of pending alerts: {pending}",
                    details=metrics,
                )
                self._record_alert(rule_name, alert)
                await self.notifier.notify(alert)
                return alert

        return None

    def _can_alert(self, rule_name: str) -> bool:
        """Check if we can send an alert (cooldown expired).

        Args:
            rule_name: Name of the alert rule

        Returns:
            True if alert can be sent
        """
        last_time = self._last_alert_time.get(rule_name)
        if last_time is None:
            return True

        rule = self.rules.get(rule_name)
        cooldown = rule.cooldown_seconds if rule else 300

        elapsed = (datetime.utcnow() - last_time).total_seconds()
        return elapsed >= cooldown

    def _record_alert(self, rule_name: str, alert: AlertEvent) -> None:
        """Record that an alert was sent.

        Args:
            rule_name: Name of the alert rule
            alert: The alert event
        """
        self._last_alert_time[rule_name] = datetime.utcnow()
        self._active_alerts[rule_name] = alert

    def resolve_alert(self, rule_name: str) -> Optional[AlertEvent]:
        """Mark an alert as resolved.

        Args:
            rule_name: Name of the alert rule

        Returns:
            The resolved alert, or None if not found
        """
        if rule_name in self._active_alerts:
            alert = self._active_alerts[rule_name]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            del self._active_alerts[rule_name]
            return alert
        return None

    def get_active_alerts(self) -> List[AlertEvent]:
        """Get all active (unresolved) alerts.

        Returns:
            List of active alerts
        """
        return list(self._active_alerts.values())


# Singleton instance
_system_health_alerter: Optional[SystemHealthAlerter] = None


def get_system_health_alerter() -> SystemHealthAlerter:
    """Get the global SystemHealthAlerter instance."""
    global _system_health_alerter
    if _system_health_alerter is None:
        _system_health_alerter = SystemHealthAlerter()
    return _system_health_alerter
