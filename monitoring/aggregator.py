"""
Metrics Aggregation Service

Aggregates metrics from multiple services into unified views.
Provides health summaries, trend summaries, and cross-service metrics.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel, Field
import structlog

from monitoring.metrics import (
    get_metrics_collector,
    SCRAPER_VIDEOS_PROCESSED_TOTAL,
    SCRAPER_ERRORS_TOTAL,
    TRENDS_DETECTED_TOTAL,
    ALERTS_SENT_TOTAL,
    API_REQUESTS_TOTAL,
)


logger = structlog.get_logger(__name__)


class AggregatedMetrics(BaseModel):
    """Aggregated metrics from all services.

    Provides a unified view of system health and performance.
    """

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When these metrics were aggregated",
    )

    # Scraper metrics
    scraper_videos_total: int = Field(
        default=0,
        description="Total videos processed across all scraper types",
    )
    scraper_errors_total: int = Field(
        default=0,
        description="Total scraper errors",
    )
    scraper_rate_limit_hits: int = Field(
        default=0,
        description="Total rate limit hits",
    )
    scraper_circuit_breaker_state: int = Field(
        default=0,
        description="Circuit breaker state (0=closed, 1=open, 2=half_open)",
    )
    scraper_queue_depth: int = Field(
        default=0,
        description="Current queue depth",
    )
    scraper_ready: bool = Field(
        default=False,
        description="Whether scraper is ready",
    )

    # API metrics
    api_requests_total: int = Field(
        default=0,
        description="Total API requests",
    )
    api_errors_total: int = Field(
        default=0,
        description="Total API errors",
    )
    api_p95_latency_ms: int = Field(
        default=0,
        description="P95 API latency in milliseconds",
    )

    # Trend detection metrics
    trends_detected_total: int = Field(
        default=0,
        description="Total trends detected",
    )
    trends_by_status: Dict[str, int] = Field(
        default_factory=lambda: {
            "emerging": 0,
            "peaking": 0,
            "saturated": 0,
            "expired": 0,
        },
        description="Trends count by status",
    )

    # Alert metrics
    alerts_sent_total: int = Field(
        default=0,
        description="Total alerts sent",
    )
    alerts_failures_total: int = Field(
        default=0,
        description="Total alert delivery failures",
    )
    alerts_pending: int = Field(
        default=0,
        description="Current pending alerts",
    )

    # System metrics
    services_healthy: int = Field(
        default=0,
        description="Number of healthy services",
    )
    services_total: int = Field(
        default=0,
        description="Total number of services",
    )
    uptime_seconds: float = Field(
        default=0.0,
        description="Service uptime in seconds",
    )


class ServiceMetrics(BaseModel):
    """Metrics from a single service."""

    service_name: str
    service_type: str  # scraper, api, detection, alerts
    healthy: bool
    last_seen: datetime
    metrics: Dict[str, Any] = Field(default_factory=dict)


class MetricsAggregator:
    """Aggregates metrics from all Trendscope services.

    Collects metrics from:
    - Scraper service (Stage 03)
    - Trend detection service (Stage 04)
    - Alert pipeline (Stage 05)
    - API service (Stage 01)

    Provides:
    - Unified metrics summary
    - Health aggregation
    - Performance statistics
    """

    def __init__(
        self,
        aggregation_interval_seconds: int = 60,
        retention_minutes: int = 60,
    ):
        """Initialize the metrics aggregator.

        Args:
            aggregation_interval_seconds: How often to aggregate metrics
            retention_minutes: How long to keep historical aggregations
        """
        self.aggregation_interval = aggregation_interval_seconds
        self.retention = timedelta(minutes=retention_minutes)
        self._start_time = time.time()

        # In-memory storage for service metrics
        self._service_metrics: Dict[str, ServiceMetrics] = {}

        # Historical aggregations
        self._aggregation_history: List[AggregatedMetrics] = []

        # Callbacks for collecting metrics from services
        self._collectors: Dict[str, Callable] = {}

    def register_collector(self, service_name: str, collector: Callable) -> None:
        """Register a metrics collector for a service.

        Args:
            service_name: Name of the service
            collector: Async callable that returns ServiceMetrics
        """
        self._collectors[service_name] = collector
        logger.info(
            "metrics_collector_registered",
            service_name=service_name,
        )

    def update_service_metrics(
        self,
        service_name: str,
        service_type: str,
        healthy: bool,
        metrics: Dict[str, Any],
    ) -> None:
        """Update metrics for a service.

        Called by services to push their metrics.

        Args:
            service_name: Name of the service
            service_type: Type of service (scraper, api, detection, alerts)
            healthy: Whether the service is healthy
            metrics: Service-specific metrics
        """
        self._service_metrics[service_name] = ServiceMetrics(
            service_name=service_name,
            service_type=service_type,
            healthy=healthy,
            last_seen=datetime.utcnow(),
            metrics=metrics,
        )

    async def collect_and_aggregate(self) -> AggregatedMetrics:
        """Collect metrics from all services and aggregate.

        Returns:
            AggregatedMetrics with combined data
        """
        # Run all collectors
        for service_name, collector in self._collectors.items():
            try:
                if asyncio.iscoroutinefunction(collector):
                    service_metrics = await collector()
                else:
                    service_metrics = collector()

                if isinstance(service_metrics, ServiceMetrics):
                    self._service_metrics[service_name] = service_metrics

            except Exception as e:
                logger.error(
                    "metrics_collection_failed",
                    service_name=service_name,
                    error=str(e),
                )

        # Build aggregated metrics
        aggregated = self._build_aggregated_metrics()

        # Store in history
        self._aggregation_history.append(aggregated)

        # Clean old history
        self._cleanup_history()

        return aggregated

    def _build_aggregated_metrics(self) -> AggregatedMetrics:
        """Build aggregated metrics from service data."""
        metrics = AggregatedMetrics()
        metrics.uptime_seconds = time.time() - self._start_time

        # Count services
        metrics.services_total = len(self._service_metrics)
        metrics.services_healthy = sum(
            1 for s in self._service_metrics.values() if s.healthy
        )

        # Aggregate by service type
        for service in self._service_metrics.values():
            service_data = service.metrics

            if service.service_type == "scraper":
                metrics.scraper_videos_total += service_data.get("videos_processed", 0)
                metrics.scraper_errors_total += service_data.get("errors", 0)
                metrics.scraper_rate_limit_hits += service_data.get("rate_limit_hits", 0)
                metrics.scraper_circuit_breaker_state = service_data.get(
                    "circuit_breaker_state", 0
                )
                metrics.scraper_queue_depth = service_data.get("queue_depth", 0)
                metrics.scraper_ready = service_data.get("ready", False)

            elif service.service_type == "api":
                metrics.api_requests_total += service_data.get("requests_total", 0)
                metrics.api_errors_total += service_data.get("errors_total", 0)
                metrics.api_p95_latency_ms = max(
                    metrics.api_p95_latency_ms,
                    service_data.get("p95_latency_ms", 0),
                )

            elif service.service_type == "detection":
                metrics.trends_detected_total += service_data.get("trends_detected", 0)

                # Merge status counts
                status_counts = service_data.get("trends_by_status", {})
                for status, count in status_counts.items():
                    if status in metrics.trends_by_status:
                        metrics.trends_by_status[status] += count

            elif service.service_type == "alerts":
                metrics.alerts_sent_total += service_data.get("alerts_sent", 0)
                metrics.alerts_failures_total += service_data.get("failures", 0)
                metrics.alerts_pending = max(
                    metrics.alerts_pending,
                    service_data.get("pending", 0),
                )

        return metrics

    def _cleanup_history(self) -> None:
        """Remove old aggregation records."""
        cutoff = datetime.utcnow() - self.retention
        self._aggregation_history = [
            m for m in self._aggregation_history
            if m.timestamp > cutoff
        ]

    def get_current_metrics(self) -> AggregatedMetrics:
        """Get the most recent aggregated metrics.

        Returns:
            Current AggregatedMetrics, or empty if none collected
        """
        if self._aggregation_history:
            return self._aggregation_history[-1]
        return AggregatedMetrics()

    def get_metrics_history(
        self,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AggregatedMetrics]:
        """Get historical aggregated metrics.

        Args:
            since: Only return metrics after this time
            limit: Maximum number of records to return

        Returns:
            List of AggregatedMetrics
        """
        history = self._aggregation_history

        if since:
            history = [m for m in history if m.timestamp >= since]

        return history[-limit:]

    def get_service_metrics(self, service_name: str) -> Optional[ServiceMetrics]:
        """Get metrics for a specific service.

        Args:
            service_name: Name of the service

        Returns:
            ServiceMetrics or None if not found
        """
        return self._service_metrics.get(service_name)

    def get_all_service_metrics(self) -> Dict[str, ServiceMetrics]:
        """Get metrics for all services.

        Returns:
            Dict mapping service names to their metrics
        """
        return self._service_metrics.copy()

    def get_health_summary(self) -> Dict[str, Any]:
        """Get a health summary across all services.

        Returns:
            Dict with health status and details
        """
        current = self.get_current_metrics()

        # Determine overall health
        all_healthy = all(s.healthy for s in self._service_metrics.values())

        # Check for stale services (not seen in 5 minutes)
        stale_threshold = datetime.utcnow() - timedelta(minutes=5)
        stale_services = [
            name for name, service in self._service_metrics.items()
            if service.last_seen < stale_threshold
        ]

        return {
            "overall_healthy": all_healthy and len(stale_services) == 0,
            "services_healthy": current.services_healthy,
            "services_total": current.services_total,
            "stale_services": stale_services,
            "uptime_seconds": current.uptime_seconds,
            "last_updated": current.timestamp.isoformat(),
            "services": {
                name: {
                    "healthy": service.healthy,
                    "last_seen": service.last_seen.isoformat(),
                    "type": service.service_type,
                }
                for name, service in self._service_metrics.items()
            },
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a performance summary across all services.

        Returns:
            Dict with performance metrics
        """
        current = self.get_current_metrics()

        return {
            "scraper": {
                "videos_processed": current.scraper_videos_total,
                "errors": current.scraper_errors_total,
                "error_rate": (
                    current.scraper_errors_total / current.scraper_videos_total
                    if current.scraper_videos_total > 0 else 0
                ),
                "queue_depth": current.scraper_queue_depth,
                "circuit_breaker": ["closed", "open", "half_open"][
                    min(current.scraper_circuit_breaker_state, 2)
                ],
            },
            "api": {
                "requests_total": current.api_requests_total,
                "errors_total": current.api_errors_total,
                "error_rate": (
                    current.api_errors_total / current.api_requests_total
                    if current.api_requests_total > 0 else 0
                ),
                "p95_latency_ms": current.api_p95_latency_ms,
            },
            "detection": {
                "trends_detected": current.trends_detected_total,
                "by_status": current.trends_by_status,
            },
            "alerts": {
                "sent_total": current.alerts_sent_total,
                "failures": current.alerts_failures_total,
                "failure_rate": (
                    current.alerts_failures_total / current.alerts_sent_total
                    if current.alerts_sent_total > 0 else 0
                ),
                "pending": current.alerts_pending,
            },
        }


# Singleton instance
_metrics_aggregator: Optional[MetricsAggregator] = None


def get_metrics_aggregator() -> MetricsAggregator:
    """Get the global MetricsAggregator instance."""
    global _metrics_aggregator
    if _metrics_aggregator is None:
        _metrics_aggregator = MetricsAggregator()
    return _metrics_aggregator
