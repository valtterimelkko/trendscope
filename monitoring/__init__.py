"""
Monitoring & Observability Module for Trendscope

Provides unified monitoring infrastructure across all services:
- Prometheus metrics collection and aggregation
- Structured logging with correlation IDs
- Health check aggregation
- Service registry for discovery
- System health alerting

This module consolidates observability patterns from all stages:
- Stage 03 (Scraper): Video processing, circuit breaker metrics
- Stage 04 (Detection): Trend detection, velocity metrics
- Stage 05 (Alerts): Alert delivery, channel metrics
- Stage 01 (API): Request latency, error metrics

Usage:
    from monitoring import configure_monitoring, MetricsCollector, HealthAggregator

    # Initialize monitoring for a service
    configure_monitoring(
        service_name="trendscope-api",
        log_level="INFO",
        metrics_enabled=True
    )

    # Get metrics collector
    collector = get_metrics_collector()

    # Track operations
    with collector.track_processing("scraper", "trending"):
        # ... do work ...
        pass

    # Record custom metrics
    collector.increment("videos_processed", labels={"type": "trending"})
"""

from monitoring.config import MonitoringConfig, get_monitoring_config
from monitoring.metrics import (
    MetricsCollector,
    get_metrics_collector,
    track_request_metrics,
    track_database_query,
    # Prometheus metrics
    SCRAPER_VIDEOS_PROCESSED_TOTAL,
    SCRAPER_ERRORS_TOTAL,
    SCRAPER_RATE_LIMIT_HITS_TOTAL,
    SCRAPER_PROCESSING_DURATION_SECONDS,
    SCRAPER_CIRCUIT_BREAKER_STATE,
    SCRAPER_QUEUE_DEPTH,
    API_REQUESTS_TOTAL,
    API_REQUEST_DURATION_SECONDS,
    API_ERRORS_TOTAL,
    API_ACTIVE_CONNECTIONS,
    API_DATABASE_QUERIES_TOTAL,
    API_DATABASE_QUERY_DURATION_SECONDS,
    TRENDS_DETECTED_TOTAL,
    TREND_VELOCITY_SCORE,
    TREND_DETECTION_LATENCY_SECONDS,
    TRENDS_ACTIVE_BY_STATUS,
    ALERTS_SENT_TOTAL,
    ALERT_DELIVERY_DURATION_SECONDS,
    ALERT_DELIVERY_FAILURES_TOTAL,
    ALERTS_PENDING,
    APP_HEALTH_STATUS,
)
from monitoring.logging_config import (
    configure_logging,
    get_logger,
    get_correlation_id,
    set_correlation_id,
    LogContext,
)
from monitoring.health_aggregator import (
    HealthAggregator,
    HealthStatus,
    ComponentHealth,
    get_health_aggregator,
)
from monitoring.service_registry import (
    ServiceRegistry,
    ServiceInfo,
    ServiceStatus,
    get_service_registry,
)
from monitoring.alerts import (
    SystemHealthAlerter,
    AlertSeverity,
    AlertRule,
    get_system_health_alerter,
)
from monitoring.aggregator import (
    MetricsAggregator,
    AggregatedMetrics,
    get_metrics_aggregator,
)


__all__ = [
    # Configuration
    "MonitoringConfig",
    "get_monitoring_config",
    # Metrics
    "MetricsCollector",
    "get_metrics_collector",
    "track_request_metrics",
    "track_database_query",
    # Scraper Metrics
    "SCRAPER_VIDEOS_PROCESSED_TOTAL",
    "SCRAPER_ERRORS_TOTAL",
    "SCRAPER_RATE_LIMIT_HITS_TOTAL",
    "SCRAPER_PROCESSING_DURATION_SECONDS",
    "SCRAPER_CIRCUIT_BREAKER_STATE",
    "SCRAPER_QUEUE_DEPTH",
    # API Metrics
    "API_REQUESTS_TOTAL",
    "API_REQUEST_DURATION_SECONDS",
    "API_ERRORS_TOTAL",
    "API_ACTIVE_CONNECTIONS",
    "API_DATABASE_QUERIES_TOTAL",
    "API_DATABASE_QUERY_DURATION_SECONDS",
    # Trend Metrics
    "TRENDS_DETECTED_TOTAL",
    "TREND_VELOCITY_SCORE",
    "TREND_DETECTION_LATENCY_SECONDS",
    "TRENDS_ACTIVE_BY_STATUS",
    # Alert Metrics
    "ALERTS_SENT_TOTAL",
    "ALERT_DELIVERY_DURATION_SECONDS",
    "ALERT_DELIVERY_FAILURES_TOTAL",
    "ALERTS_PENDING",
    # System Metrics
    "APP_HEALTH_STATUS",
    # Logging
    "configure_logging",
    "get_logger",
    "get_correlation_id",
    "set_correlation_id",
    "LogContext",
    # Health
    "HealthAggregator",
    "HealthStatus",
    "ComponentHealth",
    "get_health_aggregator",
    # Service Registry
    "ServiceRegistry",
    "ServiceInfo",
    "ServiceStatus",
    "get_service_registry",
    # Alerts
    "SystemHealthAlerter",
    "AlertSeverity",
    "AlertRule",
    "get_system_health_alerter",
    # Aggregation
    "MetricsAggregator",
    "AggregatedMetrics",
    "get_metrics_aggregator",
]


def configure_monitoring(
    service_name: str,
    log_level: str = "INFO",
    metrics_enabled: bool = True,
    json_logging: bool = True,
) -> None:
    """Configure all monitoring components for a service.

    This is the main entry point for setting up monitoring.
    Call this at service startup.

    Args:
        service_name: Name of the service (e.g., "trendscope-api", "trendscope-scraper")
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
        metrics_enabled: Whether to enable Prometheus metrics
        json_logging: If True, use JSON log format; if False, use human-readable
    """
    from monitoring.config import set_monitoring_config

    # Set up configuration
    config = MonitoringConfig(
        service_name=service_name,
        log_level=log_level,
        metrics_enabled=metrics_enabled,
        json_logging=json_logging,
    )
    set_monitoring_config(config)

    # Configure logging
    configure_logging(
        service_name=service_name,
        log_level=log_level,
        json_output=json_logging,
    )

    # Initialize health aggregator
    health_aggregator = get_health_aggregator(
        service_name=service_name,
        version=config.version,
    )

    # Initialize service registry
    registry = get_service_registry()
    registry.register(
        service_name=service_name,
        version=config.version,
        port=config.metrics_port,
    )

    logger = get_logger(__name__)
    logger.info(
        "monitoring_configured",
        service_name=service_name,
        log_level=log_level,
        metrics_enabled=metrics_enabled,
        json_logging=json_logging,
    )
