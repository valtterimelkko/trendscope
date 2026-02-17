"""
Prometheus Metrics for Trendscope Platform

Comprehensive metrics collection organized by service component:
- Scraper metrics: Video processing, errors, rate limits
- API metrics: Request latency, errors, database queries
- Trend detection metrics: Detection count, velocity, latency
- Alert metrics: Delivery, failures, pending count

This module provides:
1. Pre-defined Prometheus metric objects
2. Decorators for easy instrumentation
3. MetricsCollector for high-level metrics operations
"""

import time
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Optional, Dict, Any

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    CollectorRegistry,
    REGISTRY,
    generate_latest,
    CONTENT_TYPE_LATEST,
)


# ==============================================================================
# SCRAPER METRICS
# ==============================================================================

# Counter: Total videos processed by the scraper
SCRAPER_VIDEOS_PROCESSED_TOTAL = Counter(
    "scraper_videos_processed_total",
    "Total number of videos processed by the scraper",
    ["scraper_type"],  # trending, hashtag, user
)

# Counter: Scraper errors by type
SCRAPER_ERRORS_TOTAL = Counter(
    "scraper_errors_total",
    "Total number of scraper errors",
    ["error_type"],  # rate_limit, blocked, timeout, empty_response, other
)

# Counter: Rate limit hits
SCRAPER_RATE_LIMIT_HITS_TOTAL = Counter(
    "scraper_rate_limit_hits_total",
    "Total number of rate limit hits",
    ["endpoint_type"],  # trending, hashtag, user
)

# Histogram: Processing duration per batch
SCRAPER_PROCESSING_DURATION_SECONDS = Histogram(
    "scraper_processing_duration_seconds",
    "Time spent processing video batches",
    ["scraper_type"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

# Gauge: Circuit breaker state (0=closed, 1=open, 2=half_open)
SCRAPER_CIRCUIT_BREAKER_STATE = Gauge(
    "scraper_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    [],
)

# Gauge: Current queue depth
SCRAPER_QUEUE_DEPTH = Gauge(
    "scraper_queue_depth",
    "Current number of videos in Redis queue",
    [],
)

# Gauge: Scraper ready status
SCRAPER_READY = Gauge(
    "scraper_ready",
    "Whether the scraper is ready (1=ready, 0=not ready)",
    [],
)

# Counter: Scraper proxy rotations
SCRAPER_PROXY_ROTATIONS_TOTAL = Counter(
    "scraper_proxy_rotations_total",
    "Total number of proxy rotations",
    [],
)

# ==============================================================================
# API METRICS
# ==============================================================================

# Counter: Total API requests
API_REQUESTS_TOTAL = Counter(
    "api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status_code"],
)

# Histogram: Request latency
API_REQUEST_DURATION_SECONDS = Histogram(
    "api_request_duration_seconds",
    "API request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# Counter: API errors
API_ERRORS_TOTAL = Counter(
    "api_errors_total",
    "Total number of API errors",
    ["endpoint", "error_type"],
)

# Gauge: Active connections
API_ACTIVE_CONNECTIONS = Gauge(
    "api_active_connections",
    "Number of active API connections",
    [],
)

# Counter: Database query count
API_DATABASE_QUERIES_TOTAL = Counter(
    "api_database_queries_total",
    "Total number of database queries",
    ["operation", "table"],
)

# Histogram: Database query latency
API_DATABASE_QUERY_DURATION_SECONDS = Histogram(
    "api_database_query_duration_seconds",
    "Database query latency in seconds",
    ["operation", "table"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
)

# Counter: Cache hits/misses
API_CACHE_TOTAL = Counter(
    "api_cache_total",
    "Total cache operations",
    ["operation"],  # hit, miss, set
)

# ==============================================================================
# TREND DETECTION METRICS
# ==============================================================================

# Counter: Total trends detected
TRENDS_DETECTED_TOTAL = Counter(
    "trends_detected_total",
    "Total number of trends detected",
    ["niche", "trend_type"],  # trend_type: sound, hashtag, format
)

# Gauge: Current velocity score of detected trends
TREND_VELOCITY_SCORE = Gauge(
    "trend_velocity_score",
    "Velocity score of detected trends",
    ["trend_id", "trend_name"],
)

# Histogram: Trend detection latency
TREND_DETECTION_LATENCY_SECONDS = Histogram(
    "trend_detection_latency_seconds",
    "Time from video ingestion to trend detection",
    [],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0],
)

# Gauge: Active trends by status
TRENDS_ACTIVE_BY_STATUS = Gauge(
    "trends_active_by_status",
    "Number of active trends by status",
    ["status"],  # emerging, peaking, saturated, expired
)

# Counter: Velocity calculations performed
TREND_VELOCITY_CALCULATIONS_TOTAL = Counter(
    "trend_velocity_calculations_total",
    "Total number of velocity calculations performed",
    [],
)

# Histogram: Video processing time
TREND_VIDEO_PROCESSING_SECONDS = Histogram(
    "trend_video_processing_seconds",
    "Time to process a single video for trend detection",
    [],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
)

# Counter: Saturation level changes
TREND_SATURATION_CHANGES_TOTAL = Counter(
    "trend_saturation_changes_total",
    "Total number of trend saturation level changes",
    ["from_stage", "to_stage"],
)

# ==============================================================================
# ALERT METRICS
# ==============================================================================

# Counter: Total alerts sent
ALERTS_SENT_TOTAL = Counter(
    "alerts_sent_total",
    "Total number of alerts sent",
    ["channel", "tier"],  # channel: slack, email, webhook; tier: free, solo, agency, enterprise
)

# Histogram: Alert delivery duration
ALERT_DELIVERY_DURATION_SECONDS = Histogram(
    "alert_delivery_duration_seconds",
    "Time to deliver an alert",
    ["channel"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

# Counter: Alert delivery failures
ALERT_DELIVERY_FAILURES_TOTAL = Counter(
    "alert_delivery_failures_total",
    "Total number of alert delivery failures",
    ["channel", "error_type"],
)

# Gauge: Pending alerts in queue
ALERTS_PENDING = Gauge(
    "alerts_pending",
    "Number of pending alerts waiting to be sent",
    [],
)

# Counter: Alert digest generated
ALERT_DIGESTS_GENERATED_TOTAL = Counter(
    "alert_digests_generated_total",
    "Total number of alert digests generated",
    ["tier"],  # free, solo, agency
)

# Counter: Alerts deduplicated
ALERTS_DEDUPLICATED_TOTAL = Counter(
    "alerts_deduplicated_total",
    "Total number of alerts deduplicated",
    [],
)

# Counter: Alerts throttled
ALERTS_THROTTLED_TOTAL = Counter(
    "alerts_throttled_total",
    "Total number of alerts throttled",
    [],
)

# Counter: Alert engagement events
ALERT_ENGAGEMENT_TOTAL = Counter(
    "alert_engagement_total",
    "Total alert engagement events",
    ["event_type"],  # open, click, dismiss
)

# ==============================================================================
# SYSTEM METRICS
# ==============================================================================

# Info: Application version
APP_INFO = Info(
    "trendscope_app",
    "Trendscope application information",
)

# Gauge: Application uptime
APP_UPTIME_SECONDS = Gauge(
    "app_uptime_seconds",
    "Application uptime in seconds",
    [],
)

# Gauge: Health check status
APP_HEALTH_STATUS = Gauge(
    "app_health_status",
    "Health check status (1=healthy, 0=unhealthy)",
    ["component"],
)

# Gauge: Service ready status
APP_READY = Gauge(
    "app_ready",
    "Whether the service is ready (1=ready, 0=not ready)",
    [],
)

# Info: Service build information
APP_BUILD_INFO = Info(
    "trendscope_build",
    "Build information",
)


# ==============================================================================
# DECORATORS FOR EASY INSTRUMENTATION
# ==============================================================================


def track_request_metrics(endpoint: str):
    """Decorator to track API request metrics.

    Automatically records request count, latency, and errors.

    Usage:
        @track_request_metrics("/api/v1/trends")
        async def get_trends(request):
            ...

    Args:
        endpoint: Endpoint pattern (e.g., "/api/v1/trends/{id}")
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            method = "GET"  # Default, can be extracted from request

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                API_ERRORS_TOTAL.labels(
                    endpoint=endpoint,
                    error_type=type(e).__name__,
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                API_REQUESTS_TOTAL.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code,
                ).inc()
                API_REQUEST_DURATION_SECONDS.labels(
                    method=method,
                    endpoint=endpoint,
                ).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            method = "GET"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                API_ERRORS_TOTAL.labels(
                    endpoint=endpoint,
                    error_type=type(e).__name__,
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                API_REQUESTS_TOTAL.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code,
                ).inc()
                API_REQUEST_DURATION_SECONDS.labels(
                    method=method,
                    endpoint=endpoint,
                ).observe(duration)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def track_database_query(operation: str, table: str):
    """Decorator to track database query metrics.

    Usage:
        @track_database_query("SELECT", "trends")
        async def get_trends_from_db():
            ...

    Args:
        operation: SQL operation (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                API_DATABASE_QUERIES_TOTAL.labels(
                    operation=operation,
                    table=table,
                ).inc()
                API_DATABASE_QUERY_DURATION_SECONDS.labels(
                    operation=operation,
                    table=table,
                ).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                API_DATABASE_QUERIES_TOTAL.labels(
                    operation=operation,
                    table=table,
                ).inc()
                API_DATABASE_QUERY_DURATION_SECONDS.labels(
                    operation=operation,
                    table=table,
                ).observe(duration)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ==============================================================================
# METRICS COLLECTOR
# ==============================================================================


class MetricsCollector:
    """High-level metrics collection interface.

    Provides convenient methods for recording metrics without
    needing to interact with Prometheus primitives directly.

    Example:
        collector = MetricsCollector()

        # Track processing time
        with collector.track_processing("scraper", "trending"):
            # ... do work ...
            pass

        # Increment counters
        collector.increment_videos_processed("trending", 100)
        collector.increment_scraper_error("rate_limit")
    """

    def __init__(self, namespace: str = "trendscope"):
        """Initialize the metrics collector.

        Args:
            namespace: Namespace prefix for metrics
        """
        self.namespace = namespace
        self._start_time = time.time()

    @contextmanager
    def track_processing(self, service: str, operation: str):
        """Context manager to track processing duration.

        Usage:
            with collector.track_processing("scraper", "trending"):
                process_videos()

        Args:
            service: Service name (scraper, api, detection, alerts)
            operation: Operation name
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time

            if service == "scraper":
                SCRAPER_PROCESSING_DURATION_SECONDS.labels(
                    scraper_type=operation,
                ).observe(duration)
            elif service == "detection":
                TREND_DETECTION_LATENCY_SECONDS.observe(duration)
            elif service == "alerts":
                ALERT_DELIVERY_DURATION_SECONDS.labels(
                    channel=operation,
                ).observe(duration)

    @contextmanager
    def track_database_query(self, operation: str, table: str):
        """Context manager to track database query duration.

        Args:
            operation: SQL operation
            table: Table name
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            API_DATABASE_QUERIES_TOTAL.labels(
                operation=operation,
                table=table,
            ).inc()
            API_DATABASE_QUERY_DURATION_SECONDS.labels(
                operation=operation,
                table=table,
            ).observe(duration)

    # Scraper metrics
    def increment_videos_processed(self, scraper_type: str, count: int = 1) -> None:
        """Increment videos processed counter."""
        SCRAPER_VIDEOS_PROCESSED_TOTAL.labels(scraper_type=scraper_type).inc(count)

    def increment_scraper_error(self, error_type: str, count: int = 1) -> None:
        """Increment scraper error counter."""
        SCRAPER_ERRORS_TOTAL.labels(error_type=error_type).inc(count)

    def increment_rate_limit_hit(self, endpoint_type: str) -> None:
        """Increment rate limit hit counter."""
        SCRAPER_RATE_LIMIT_HITS_TOTAL.labels(endpoint_type=endpoint_type).inc()

    def set_circuit_breaker_state(self, state: int) -> None:
        """Set circuit breaker state (0=closed, 1=open, 2=half_open)."""
        SCRAPER_CIRCUIT_BREAKER_STATE.set(state)

    def set_queue_depth(self, depth: int) -> None:
        """Set current queue depth."""
        SCRAPER_QUEUE_DEPTH.set(depth)

    def set_scraper_ready(self, ready: bool) -> None:
        """Set scraper ready status."""
        SCRAPER_READY.set(1 if ready else 0)

    # API metrics
    def increment_api_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
    ) -> None:
        """Increment API request counter."""
        API_REQUESTS_TOTAL.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()

    def observe_api_latency(self, method: str, endpoint: str, duration: float) -> None:
        """Observe API request latency."""
        API_REQUEST_DURATION_SECONDS.labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration)

    def increment_api_error(self, endpoint: str, error_type: str) -> None:
        """Increment API error counter."""
        API_ERRORS_TOTAL.labels(
            endpoint=endpoint,
            error_type=error_type,
        ).inc()

    def set_active_connections(self, count: int) -> None:
        """Set active connection count."""
        API_ACTIVE_CONNECTIONS.set(count)

    def increment_cache_operation(self, operation: str) -> None:
        """Increment cache operation (hit, miss, set)."""
        API_CACHE_TOTAL.labels(operation=operation).inc()

    # Trend detection metrics
    def increment_trends_detected(
        self,
        niche: str,
        trend_type: str,
        count: int = 1,
    ) -> None:
        """Increment trends detected counter."""
        TRENDS_DETECTED_TOTAL.labels(
            niche=niche,
            trend_type=trend_type,
        ).inc(count)

    def set_velocity_score(self, trend_id: str, trend_name: str, score: int) -> None:
        """Set trend velocity score."""
        # Use truncated trend_id to avoid cardinality explosion
        short_id = trend_id[:8] if len(trend_id) > 8 else trend_id
        TREND_VELOCITY_SCORE.labels(
            trend_id=short_id,
            trend_name=trend_name[:50],  # Truncate long names
        ).set(score)

    def set_trends_by_status(self, status: str, count: int) -> None:
        """Set count of trends by status."""
        TRENDS_ACTIVE_BY_STATUS.labels(status=status).set(count)

    def increment_velocity_calculations(self) -> None:
        """Increment velocity calculations counter."""
        TREND_VELOCITY_CALCULATIONS_TOTAL.inc()

    def observe_video_processing_time(self, duration: float) -> None:
        """Observe video processing time."""
        TREND_VIDEO_PROCESSING_SECONDS.observe(duration)

    # Alert metrics
    def increment_alerts_sent(self, channel: str, tier: str) -> None:
        """Increment alerts sent counter."""
        ALERTS_SENT_TOTAL.labels(channel=channel, tier=tier).inc()

    def increment_alert_failure(self, channel: str, error_type: str) -> None:
        """Increment alert delivery failure counter."""
        ALERT_DELIVERY_FAILURES_TOTAL.labels(
            channel=channel,
            error_type=error_type,
        ).inc()

    def set_pending_alerts(self, count: int) -> None:
        """Set pending alerts count."""
        ALERTS_PENDING.set(count)

    def increment_digest_generated(self, tier: str) -> None:
        """Increment digest generated counter."""
        ALERT_DIGESTS_GENERATED_TOTAL.labels(tier=tier).inc()

    def increment_deduplicated(self) -> None:
        """Increment deduplicated alerts counter."""
        ALERTS_DEDUPLICATED_TOTAL.inc()

    def increment_throttled(self) -> None:
        """Increment throttled alerts counter."""
        ALERTS_THROTTLED_TOTAL.inc()

    def increment_engagement(self, event_type: str) -> None:
        """Increment engagement event counter."""
        ALERT_ENGAGEMENT_TOTAL.labels(event_type=event_type).inc()

    # System metrics
    def set_health_status(self, component: str, healthy: bool) -> None:
        """Set component health status."""
        APP_HEALTH_STATUS.labels(component=component).set(1 if healthy else 0)

    def set_ready_status(self, ready: bool) -> None:
        """Set service ready status."""
        APP_READY.set(1 if ready else 0)

    def get_uptime(self) -> float:
        """Get service uptime in seconds."""
        return time.time() - self._start_time

    def set_app_info(self, version: str, commit: str = "") -> None:
        """Set application info."""
        APP_INFO.info({
            "version": version,
            "commit": commit[:8] if commit else "unknown",
        })


# Singleton instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global MetricsCollector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_metrics_output() -> bytes:
    """Get Prometheus metrics output.

    Returns:
        Metrics in Prometheus text exposition format
    """
    return generate_latest()


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST
