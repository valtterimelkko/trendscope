"""
Monitoring Configuration

Centralized configuration for monitoring components.
Loads from environment variables with sensible defaults.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class MonitoringConfig(BaseSettings):
    """Configuration for monitoring components.

    Loads from environment variables with TRENDSCOPE_ prefix.

    Environment Variables:
        TRENDSCOPE_SERVICE_NAME: Name of this service
        TRENDSCOPE_LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR)
        TRENDSCOPE_METRICS_ENABLED: Enable Prometheus metrics
        TRENDSCOPE_METRICS_PORT: Port for metrics endpoint
        TRENDSCOPE_HEALTH_PORT: Port for health check endpoint
        TRENDSCOPE_JSON_LOGGING: Use JSON log format
        TRENDSCOPE_CORRELATION_HEADER: Header for correlation IDs
    """

    # Service identification
    service_name: str = Field(
        default="trendscope",
        description="Name of this service for logging and metrics",
    )
    version: str = Field(
        default="1.0.0",
        description="Service version",
    )
    environment: str = Field(
        default="development",
        description="Deployment environment (development, staging, production)",
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Minimum log level",
    )
    json_logging: bool = Field(
        default=True,
        description="Use JSON format for logs",
    )
    log_include_timestamp: bool = Field(
        default=True,
        description="Include ISO8601 timestamp in logs",
    )

    # Metrics configuration
    metrics_enabled: bool = Field(
        default=True,
        description="Enable Prometheus metrics collection",
    )
    metrics_port: int = Field(
        default=9090,
        description="Port for Prometheus metrics endpoint",
    )
    metrics_path: str = Field(
        default="/metrics",
        description="Path for metrics endpoint",
    )

    # Health check configuration
    health_enabled: bool = Field(
        default=True,
        description="Enable health check endpoints",
    )
    health_port: int = Field(
        default=8080,
        description="Port for health check endpoints",
    )
    health_path: str = Field(
        default="/health",
        description="Path for health check endpoint",
    )
    ready_path: str = Field(
        default="/ready",
        description="Path for readiness endpoint",
    )
    live_path: str = Field(
        default="/live",
        description="Path for liveness endpoint",
    )

    # Alerting configuration
    alert_check_interval_seconds: int = Field(
        default=60,
        description="How often to check alert conditions",
    )
    alert_cooldown_seconds: int = Field(
        default=300,
        description="Minimum time between alerts for same condition",
    )

    # Correlation tracing
    correlation_header: str = Field(
        default="X-Trace-ID",
        description="HTTP header for correlation IDs",
    )

    # Service registry
    registry_enabled: bool = Field(
        default=True,
        description="Enable service registry",
    )

    model_config = {
        "env_prefix": "TRENDSCOPE_",
        "env_file": ".env",
        "extra": "ignore",
    }


# Global config instance
_monitoring_config: Optional[MonitoringConfig] = None


def get_monitoring_config() -> MonitoringConfig:
    """Get the global monitoring configuration.

    Returns:
        MonitoringConfig instance

    Raises:
        RuntimeError: If configuration not initialized
    """
    global _monitoring_config
    if _monitoring_config is None:
        _monitoring_config = MonitoringConfig()
    return _monitoring_config


def set_monitoring_config(config: MonitoringConfig) -> None:
    """Set the global monitoring configuration.

    Args:
        config: Configuration to set
    """
    global _monitoring_config
    _monitoring_config = config


class AlertThresholds(BaseModel):
    """Thresholds for system health alerts.

    These define when alerts should trigger based on metric values.
    """

    # Scraper thresholds
    scraper_down_timeout_seconds: int = Field(
        default=600,  # 10 minutes
        description="Seconds without scraper activity before alerting",
    )
    scraper_error_rate_threshold: float = Field(
        default=0.1,
        description="Errors per second threshold for alerting",
    )
    scraper_circuit_breaker_open_seconds: int = Field(
        default=300,  # 5 minutes
        description="Seconds with circuit breaker open before alerting",
    )

    # API thresholds
    api_latency_p95_threshold_seconds: float = Field(
        default=1.0,
        description="P95 latency threshold for alerting",
    )
    api_error_rate_threshold: float = Field(
        default=0.05,
        description="Error rate threshold (5%) for alerting",
    )
    api_database_latency_threshold_seconds: float = Field(
        default=0.5,
        description="Database query latency threshold for alerting",
    )

    # Trend detection thresholds
    trend_detection_latency_threshold_seconds: int = Field(
        default=600,  # 10 minutes
        description="Detection latency threshold for alerting",
    )
    trend_detection_idle_hours: int = Field(
        default=2,
        description="Hours without trend detection before alerting",
    )

    # Alert delivery thresholds
    alert_failure_rate_threshold: float = Field(
        default=0.1,
        description="Alert delivery failure rate threshold for alerting",
    )
    alert_pending_threshold: int = Field(
        default=100,
        description="Number of pending alerts for alerting",
    )

    # Infrastructure thresholds
    redis_memory_utilization_threshold: float = Field(
        default=0.8,
        description="Redis memory utilization threshold for alerting",
    )
    database_connection_utilization_threshold: float = Field(
        default=0.8,
        description="Database connection utilization threshold for alerting",
    )


# Default alert thresholds
DEFAULT_ALERT_THRESHOLDS = AlertThresholds()
