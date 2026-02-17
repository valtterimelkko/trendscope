"""
Unit tests for Prometheus Metrics Collection.

Tests Counter, Histogram, Gauge metrics, labeling, and the MetricsCollector class.
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, patch

from prometheus_client import REGISTRY, Counter, Histogram, Gauge, generate_latest

from monitoring.metrics import (
    # Scraper metrics
    SCRAPER_VIDEOS_PROCESSED_TOTAL,
    SCRAPER_ERRORS_TOTAL,
    SCRAPER_RATE_LIMIT_HITS_TOTAL,
    SCRAPER_PROCESSING_DURATION_SECONDS,
    SCRAPER_CIRCUIT_BREAKER_STATE,
    SCRAPER_QUEUE_DEPTH,
    SCRAPER_READY,
    # API metrics
    API_REQUESTS_TOTAL,
    API_REQUEST_DURATION_SECONDS,
    API_ERRORS_TOTAL,
    API_ACTIVE_CONNECTIONS,
    API_DATABASE_QUERIES_TOTAL,
    API_DATABASE_QUERY_DURATION_SECONDS,
    API_CACHE_TOTAL,
    # Trend detection metrics
    TRENDS_DETECTED_TOTAL,
    TREND_VELOCITY_SCORE,
    TREND_DETECTION_LATENCY_SECONDS,
    TRENDS_ACTIVE_BY_STATUS,
    TREND_VELOCITY_CALCULATIONS_TOTAL,
    # Alert metrics
    ALERTS_SENT_TOTAL,
    ALERT_DELIVERY_DURATION_SECONDS,
    ALERT_DELIVERY_FAILURES_TOTAL,
    ALERTS_PENDING,
    ALERT_DIGESTS_GENERATED_TOTAL,
    # System metrics
    APP_HEALTH_STATUS,
    APP_READY,
    # Classes and functions
    MetricsCollector,
    get_metrics_collector,
    get_metrics_output,
    get_metrics_content_type,
    track_request_metrics,
    track_database_query,
)


class TestScraperMetrics:
    """Test scraper-related metrics."""

    def test_videos_processed_counter_increment(self):
        """Counter should increment correctly for videos processed."""
        # Get initial value
        initial = SCRAPER_VIDEOS_PROCESSED_TOTAL.labels(scraper_type="trending")._value.get()
        
        # Increment
        SCRAPER_VIDEOS_PROCESSED_TOTAL.labels(scraper_type="trending").inc()
        SCRAPER_VIDEOS_PROCESSED_TOTAL.labels(scraper_type="trending").inc(5)
        
        # Check new value
        new_value = SCRAPER_VIDEOS_PROCESSED_TOTAL.labels(scraper_type="trending")._value.get()
        assert new_value == initial + 6

    def test_videos_processed_multiple_labels(self):
        """Counter should track different label values separately."""
        # Reset and increment different types
        SCRAPER_VIDEOS_PROCESSED_TOTAL.labels(scraper_type="trending").inc(10)
        SCRAPER_VIDEOS_PROCESSED_TOTAL.labels(scraper_type="hashtag").inc(5)
        SCRAPER_VIDEOS_PROCESSED_TOTAL.labels(scraper_type="user").inc(3)
        
        trending_val = SCRAPER_VIDEOS_PROCESSED_TOTAL.labels(scraper_type="trending")._value.get()
        hashtag_val = SCRAPER_VIDEOS_PROCESSED_TOTAL.labels(scraper_type="hashtag")._value.get()
        user_val = SCRAPER_VIDEOS_PROCESSED_TOTAL.labels(scraper_type="user")._value.get()
        
        assert trending_val >= 10
        assert hashtag_val >= 5
        assert user_val >= 3

    def test_scraper_errors_by_type(self):
        """Error counter should track different error types."""
        SCRAPER_ERRORS_TOTAL.labels(error_type="rate_limit").inc()
        SCRAPER_ERRORS_TOTAL.labels(error_type="timeout").inc()
        SCRAPER_ERRORS_TOTAL.labels(error_type="blocked").inc()
        
        rate_limit_val = SCRAPER_ERRORS_TOTAL.labels(error_type="rate_limit")._value.get()
        timeout_val = SCRAPER_ERRORS_TOTAL.labels(error_type="timeout")._value.get()
        
        assert rate_limit_val >= 1
        assert timeout_val >= 1

    def test_rate_limit_hits_counter(self):
        """Rate limit hits should be tracked by endpoint type."""
        SCRAPER_RATE_LIMIT_HITS_TOTAL.labels(endpoint_type="trending").inc()
        SCRAPER_RATE_LIMIT_HITS_TOTAL.labels(endpoint_type="hashtag").inc()
        
        trending_val = SCRAPER_RATE_LIMIT_HITS_TOTAL.labels(endpoint_type="trending")._value.get()
        assert trending_val >= 1

    def test_processing_duration_histogram(self):
        """Histogram should record processing durations."""
        SCRAPER_PROCESSING_DURATION_SECONDS.labels(scraper_type="trending").observe(0.5)
        SCRAPER_PROCESSING_DURATION_SECONDS.labels(scraper_type="trending").observe(1.0)
        SCRAPER_PROCESSING_DURATION_SECONDS.labels(scraper_type="trending").observe(2.5)
        
        # Histogram should have samples
        samples = SCRAPER_PROCESSING_DURATION_SECONDS.labels(scraper_type="trending")._sum.get()
        assert samples >= 4.0  # Sum of observations

    def test_circuit_breaker_state_gauge(self):
        """Gauge should track circuit breaker state."""
        SCRAPER_CIRCUIT_BREAKER_STATE.set(0)  # closed
        assert SCRAPER_CIRCUIT_BREAKER_STATE._value.get() == 0
        
        SCRAPER_CIRCUIT_BREAKER_STATE.set(1)  # open
        assert SCRAPER_CIRCUIT_BREAKER_STATE._value.get() == 1
        
        SCRAPER_CIRCUIT_BREAKER_STATE.set(2)  # half_open
        assert SCRAPER_CIRCUIT_BREAKER_STATE._value.get() == 2

    def test_queue_depth_gauge(self):
        """Gauge should track queue depth."""
        SCRAPER_QUEUE_DEPTH.set(100)
        assert SCRAPER_QUEUE_DEPTH._value.get() == 100
        
        SCRAPER_QUEUE_DEPTH.set(500)
        assert SCRAPER_QUEUE_DEPTH._value.get() == 500

    def test_scraper_ready_gauge(self):
        """Gauge should track scraper ready status."""
        SCRAPER_READY.set(1)
        assert SCRAPER_READY._value.get() == 1
        
        SCRAPER_READY.set(0)
        assert SCRAPER_READY._value.get() == 0


class TestAPIMetrics:
    """Test API-related metrics."""

    def test_api_requests_total_counter(self):
        """Counter should track API requests with labels."""
        API_REQUESTS_TOTAL.labels(method="GET", endpoint="/api/v1/trends", status_code=200).inc()
        API_REQUESTS_TOTAL.labels(method="POST", endpoint="/api/v1/trends", status_code=201).inc()
        API_REQUESTS_TOTAL.labels(method="GET", endpoint="/api/v1/trends", status_code=500).inc()
        
        get_200 = API_REQUESTS_TOTAL.labels(method="GET", endpoint="/api/v1/trends", status_code=200)._value.get()
        assert get_200 >= 1

    def test_api_request_duration_histogram(self):
        """Histogram should track request latencies."""
        API_REQUEST_DURATION_SECONDS.labels(method="GET", endpoint="/api/v1/trends").observe(0.05)
        API_REQUEST_DURATION_SECONDS.labels(method="GET", endpoint="/api/v1/trends").observe(0.1)
        API_REQUEST_DURATION_SECONDS.labels(method="POST", endpoint="/api/v1/trends").observe(0.2)
        
        # Should have recorded observations
        samples = API_REQUEST_DURATION_SECONDS.labels(method="GET", endpoint="/api/v1/trends")._sum.get()
        assert samples >= 0.15

    def test_api_errors_counter(self):
        """Counter should track API errors."""
        API_ERRORS_TOTAL.labels(endpoint="/api/v1/trends", error_type="ValidationError").inc()
        API_ERRORS_TOTAL.labels(endpoint="/api/v1/trends", error_type="DatabaseError").inc()
        
        val = API_ERRORS_TOTAL.labels(endpoint="/api/v1/trends", error_type="ValidationError")._value.get()
        assert val >= 1

    def test_api_active_connections_gauge(self):
        """Gauge should track active connections."""
        API_ACTIVE_CONNECTIONS.set(10)
        assert API_ACTIVE_CONNECTIONS._value.get() == 10
        
        API_ACTIVE_CONNECTIONS.inc()
        assert API_ACTIVE_CONNECTIONS._value.get() == 11
        
        API_ACTIVE_CONNECTIONS.dec()
        assert API_ACTIVE_CONNECTIONS._value.get() == 10

    def test_database_queries_counter(self):
        """Counter should track database queries."""
        API_DATABASE_QUERIES_TOTAL.labels(operation="SELECT", table="trends").inc()
        API_DATABASE_QUERIES_TOTAL.labels(operation="INSERT", table="trends").inc()
        
        select_val = API_DATABASE_QUERIES_TOTAL.labels(operation="SELECT", table="trends")._value.get()
        assert select_val >= 1

    def test_database_query_duration_histogram(self):
        """Histogram should track query latencies."""
        API_DATABASE_QUERY_DURATION_SECONDS.labels(operation="SELECT", table="trends").observe(0.01)
        API_DATABASE_QUERY_DURATION_SECONDS.labels(operation="SELECT", table="trends").observe(0.05)
        
        samples = API_DATABASE_QUERY_DURATION_SECONDS.labels(operation="SELECT", table="trends")._sum.get()
        assert samples >= 0.06

    def test_cache_operations_counter(self):
        """Counter should track cache operations."""
        API_CACHE_TOTAL.labels(operation="hit").inc()
        API_CACHE_TOTAL.labels(operation="miss").inc()
        API_CACHE_TOTAL.labels(operation="set").inc()
        
        hit_val = API_CACHE_TOTAL.labels(operation="hit")._value.get()
        miss_val = API_CACHE_TOTAL.labels(operation="miss")._value.get()
        assert hit_val >= 1
        assert miss_val >= 1


class TestTrendDetectionMetrics:
    """Test trend detection metrics."""

    def test_trends_detected_counter(self):
        """Counter should track trends by niche and type."""
        TRENDS_DETECTED_TOTAL.labels(niche="beauty", trend_type="sound").inc()
        TRENDS_DETECTED_TOTAL.labels(niche="fitness", trend_type="hashtag").inc()
        TRENDS_DETECTED_TOTAL.labels(niche="beauty", trend_type="sound").inc(5)
        
        beauty_sound = TRENDS_DETECTED_TOTAL.labels(niche="beauty", trend_type="sound")._value.get()
        assert beauty_sound >= 6

    def test_velocity_score_gauge(self):
        """Gauge should track velocity scores for trends."""
        TREND_VELOCITY_SCORE.labels(trend_id="abc123", trend_name="Viral Sound").set(85)
        TREND_VELOCITY_SCORE.labels(trend_id="def456", trend_name="Dance Challenge").set(92)
        
        val1 = TREND_VELOCITY_SCORE.labels(trend_id="abc123", trend_name="Viral Sound")._value.get()
        assert val1 == 85

    def test_detection_latency_histogram(self):
        """Histogram should track detection latencies."""
        TREND_DETECTION_LATENCY_SECONDS.observe(10.0)
        TREND_DETECTION_LATENCY_SECONDS.observe(30.0)
        TREND_DETECTION_LATENCY_SECONDS.observe(60.0)
        
        samples = TREND_DETECTION_LATENCY_SECONDS._sum.get()
        assert samples >= 100.0

    def test_trends_by_status_gauge(self):
        """Gauge should track trends by status."""
        TRENDS_ACTIVE_BY_STATUS.labels(status="emerging").set(10)
        TRENDS_ACTIVE_BY_STATUS.labels(status="peaking").set(5)
        TRENDS_ACTIVE_BY_STATUS.labels(status="saturated").set(3)
        TRENDS_ACTIVE_BY_STATUS.labels(status="expired").set(2)
        
        emerging = TRENDS_ACTIVE_BY_STATUS.labels(status="emerging")._value.get()
        assert emerging == 10

    def test_velocity_calculations_counter(self):
        """Counter should track velocity calculations."""
        initial = TREND_VELOCITY_CALCULATIONS_TOTAL._value.get()
        
        TREND_VELOCITY_CALCULATIONS_TOTAL.inc()
        TREND_VELOCITY_CALCULATIONS_TOTAL.inc()
        
        new_val = TREND_VELOCITY_CALCULATIONS_TOTAL._value.get()
        assert new_val == initial + 2


class TestAlertMetrics:
    """Test alert pipeline metrics."""

    def test_alerts_sent_counter(self):
        """Counter should track alerts by channel and tier."""
        ALERTS_SENT_TOTAL.labels(channel="slack", tier="solo").inc()
        ALERTS_SENT_TOTAL.labels(channel="email", tier="agency").inc()
        ALERTS_SENT_TOTAL.labels(channel="webhook", tier="enterprise").inc()
        
        slack_solo = ALERTS_SENT_TOTAL.labels(channel="slack", tier="solo")._value.get()
        assert slack_solo >= 1

    def test_alert_delivery_duration_histogram(self):
        """Histogram should track delivery latencies."""
        ALERT_DELIVERY_DURATION_SECONDS.labels(channel="slack").observe(0.5)
        ALERT_DELIVERY_DURATION_SECONDS.labels(channel="email").observe(2.0)
        
        slack_sum = ALERT_DELIVERY_DURATION_SECONDS.labels(channel="slack")._sum.get()
        assert slack_sum >= 0.5

    def test_alert_delivery_failures_counter(self):
        """Counter should track delivery failures."""
        ALERT_DELIVERY_FAILURES_TOTAL.labels(channel="slack", error_type="timeout").inc()
        ALERT_DELIVERY_FAILURES_TOTAL.labels(channel="email", error_type="connection_error").inc()
        
        timeout_val = ALERT_DELIVERY_FAILURES_TOTAL.labels(channel="slack", error_type="timeout")._value.get()
        assert timeout_val >= 1

    def test_pending_alerts_gauge(self):
        """Gauge should track pending alerts."""
        ALERTS_PENDING.set(50)
        assert ALERTS_PENDING._value.get() == 50
        
        ALERTS_PENDING.set(0)
        assert ALERTS_PENDING._value.get() == 0

    def test_digest_generated_counter(self):
        """Counter should track digest generation by tier."""
        ALERT_DIGESTS_GENERATED_TOTAL.labels(tier="free").inc()
        ALERT_DIGESTS_GENERATED_TOTAL.labels(tier="solo").inc()
        ALERT_DIGESTS_GENERATED_TOTAL.labels(tier="agency").inc()
        
        free_val = ALERT_DIGESTS_GENERATED_TOTAL.labels(tier="free")._value.get()
        assert free_val >= 1


class TestSystemMetrics:
    """Test system-level metrics."""

    def test_health_status_gauge(self):
        """Gauge should track health status by component."""
        APP_HEALTH_STATUS.labels(component="database").set(1)
        APP_HEALTH_STATUS.labels(component="redis").set(1)
        APP_HEALTH_STATUS.labels(component="scraper").set(0)
        
        db_val = APP_HEALTH_STATUS.labels(component="database")._value.get()
        scraper_val = APP_HEALTH_STATUS.labels(component="scraper")._value.get()
        
        assert db_val == 1
        assert scraper_val == 0

    def test_ready_gauge(self):
        """Gauge should track service ready status."""
        APP_READY.set(1)
        assert APP_READY._value.get() == 1
        
        APP_READY.set(0)
        assert APP_READY._value.get() == 0


class TestMetricsCollector:
    """Test the MetricsCollector class."""

    def test_collector_initialization(self):
        """Collector should initialize with correct values."""
        collector = MetricsCollector(namespace="test")
        
        assert collector.namespace == "test"
        assert collector.get_uptime() >= 0

    def test_increment_videos_processed(self):
        """Collector should increment videos processed."""
        collector = MetricsCollector()
        
        collector.increment_videos_processed("trending", 10)
        collector.increment_videos_processed("hashtag", 5)
        
        # Values should be recorded (we can check by incrementing again)
        trending_val = SCRAPER_VIDEOS_PROCESSED_TOTAL.labels(scraper_type="trending")._value.get()
        assert trending_val >= 10

    def test_increment_scraper_error(self):
        """Collector should increment scraper errors."""
        collector = MetricsCollector()
        
        collector.increment_scraper_error("rate_limit")
        collector.increment_scraper_error("timeout")
        
        rate_limit_val = SCRAPER_ERRORS_TOTAL.labels(error_type="rate_limit")._value.get()
        assert rate_limit_val >= 1

    def test_set_circuit_breaker_state(self):
        """Collector should set circuit breaker state."""
        collector = MetricsCollector()
        
        collector.set_circuit_breaker_state(0)
        assert SCRAPER_CIRCUIT_BREAKER_STATE._value.get() == 0
        
        collector.set_circuit_breaker_state(1)
        assert SCRAPER_CIRCUIT_BREAKER_STATE._value.get() == 1

    def test_set_queue_depth(self):
        """Collector should set queue depth."""
        collector = MetricsCollector()
        
        collector.set_queue_depth(100)
        assert SCRAPER_QUEUE_DEPTH._value.get() == 100

    def test_increment_api_request(self):
        """Collector should increment API requests."""
        collector = MetricsCollector()
        
        collector.increment_api_request("GET", "/api/v1/trends", 200)
        collector.increment_api_request("POST", "/api/v1/trends", 201)
        
        get_200 = API_REQUESTS_TOTAL.labels(method="GET", endpoint="/api/v1/trends", status_code=200)._value.get()
        assert get_200 >= 1

    def test_observe_api_latency(self):
        """Collector should observe API latency."""
        collector = MetricsCollector()
        
        collector.observe_api_latency("GET", "/api/v1/trends", 0.05)
        collector.observe_api_latency("GET", "/api/v1/trends", 0.1)
        
        samples = API_REQUEST_DURATION_SECONDS.labels(method="GET", endpoint="/api/v1/trends")._sum.get()
        assert samples >= 0.15

    def test_increment_trends_detected(self):
        """Collector should increment trends detected."""
        collector = MetricsCollector()
        
        collector.increment_trends_detected("beauty", "sound", 3)
        collector.increment_trends_detected("fitness", "hashtag", 2)
        
        beauty_sound = TRENDS_DETECTED_TOTAL.labels(niche="beauty", trend_type="sound")._value.get()
        assert beauty_sound >= 3

    def test_set_velocity_score(self):
        """Collector should set velocity scores."""
        collector = MetricsCollector()
        
        collector.set_velocity_score("abc12345-1234-1234-1234-123456789abc", "Viral Sound", 88)
        
        # Should truncate trend_id to 8 chars
        val = TREND_VELOCITY_SCORE.labels(trend_id="abc12345", trend_name="Viral Sound")._value.get()
        assert val == 88

    def test_set_trends_by_status(self):
        """Collector should set trends by status."""
        collector = MetricsCollector()
        
        collector.set_trends_by_status("emerging", 15)
        collector.set_trends_by_status("peaking", 8)
        
        emerging = TRENDS_ACTIVE_BY_STATUS.labels(status="emerging")._value.get()
        assert emerging == 15

    def test_increment_alerts_sent(self):
        """Collector should increment alerts sent."""
        collector = MetricsCollector()
        
        collector.increment_alerts_sent("slack", "solo")
        collector.increment_alerts_sent("email", "agency")
        
        slack_solo = ALERTS_SENT_TOTAL.labels(channel="slack", tier="solo")._value.get()
        assert slack_solo >= 1

    def test_set_pending_alerts(self):
        """Collector should set pending alerts."""
        collector = MetricsCollector()
        
        collector.set_pending_alerts(25)
        assert ALERTS_PENDING._value.get() == 25

    def test_set_health_status(self):
        """Collector should set health status."""
        collector = MetricsCollector()
        
        collector.set_health_status("database", True)
        collector.set_health_status("redis", False)
        
        db_val = APP_HEALTH_STATUS.labels(component="database")._value.get()
        redis_val = APP_HEALTH_STATUS.labels(component="redis")._value.get()
        
        assert db_val == 1
        assert redis_val == 0

    def test_track_processing_context_manager(self):
        """Context manager should track processing time."""
        collector = MetricsCollector()
        
        with collector.track_processing("scraper", "trending"):
            time.sleep(0.01)  # 10ms
        
        # Histogram should have recorded the observation
        samples = SCRAPER_PROCESSING_DURATION_SECONDS.labels(scraper_type="trending")._sum.get()
        assert samples > 0

    def test_track_database_query_context_manager(self):
        """Context manager should track database query time."""
        collector = MetricsCollector()
        
        with collector.track_database_query("SELECT", "trends"):
            time.sleep(0.001)  # 1ms
        
        # Histogram should have recorded the observation
        samples = API_DATABASE_QUERY_DURATION_SECONDS.labels(operation="SELECT", table="trends")._sum.get()
        assert samples > 0

    def test_get_uptime(self):
        """Collector should track uptime."""
        collector = MetricsCollector()
        
        time.sleep(0.01)  # 10ms
        uptime = collector.get_uptime()
        
        assert uptime >= 0.01


class TestTrackRequestMetricsDecorator:
    """Test the track_request_metrics decorator."""

    @pytest.mark.asyncio
    async def test_async_function_tracking(self):
        """Decorator should track async function calls."""
        
        @track_request_metrics("/api/v1/test")
        async def async_endpoint():
            await asyncio.sleep(0.001)
            return {"status": "ok"}
        
        result = await async_endpoint()
        
        assert result == {"status": "ok"}
        # Metrics should have been recorded
        requests = API_REQUESTS_TOTAL.labels(method="GET", endpoint="/api/v1/test", status_code=200)._value.get()
        assert requests >= 1

    def test_sync_function_tracking(self):
        """Decorator should track sync function calls."""
        
        @track_request_metrics("/api/v1/sync")
        def sync_endpoint():
            return {"status": "ok"}
        
        result = sync_endpoint()
        
        assert result == {"status": "ok"}
        requests = API_REQUESTS_TOTAL.labels(method="GET", endpoint="/api/v1/sync", status_code=200)._value.get()
        assert requests >= 1

    @pytest.mark.asyncio
    async def test_error_tracking(self):
        """Decorator should track errors."""
        
        @track_request_metrics("/api/v1/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await error_endpoint()
        
        # Error should be recorded
        errors = API_ERRORS_TOTAL.labels(endpoint="/api/v1/error", error_type="ValueError")._value.get()
        assert errors >= 1


class TestTrackDatabaseQueryDecorator:
    """Test the track_database_query decorator."""

    @pytest.mark.asyncio
    async def test_async_query_tracking(self):
        """Decorator should track async database queries."""
        
        @track_database_query("SELECT", "trends")
        async def async_query():
            await asyncio.sleep(0.001)
            return [{"id": 1}]
        
        result = await async_query()
        
        assert result == [{"id": 1}]
        queries = API_DATABASE_QUERIES_TOTAL.labels(operation="SELECT", table="trends")._value.get()
        assert queries >= 1

    def test_sync_query_tracking(self):
        """Decorator should track sync database queries."""
        
        @track_database_query("INSERT", "alerts")
        def sync_query():
            return True
        
        result = sync_query()
        
        assert result is True
        queries = API_DATABASE_QUERIES_TOTAL.labels(operation="INSERT", table="alerts")._value.get()
        assert queries >= 1


class TestMetricsExport:
    """Test metrics export functionality."""

    def test_get_metrics_output(self):
        """Should return Prometheus format metrics."""
        output = get_metrics_output()
        
        assert isinstance(output, bytes)
        assert b"# HELP" in output
        assert b"# TYPE" in output

    def test_get_metrics_content_type(self):
        """Should return correct content type."""
        from prometheus_client import CONTENT_TYPE_LATEST
        content_type = get_metrics_content_type()
        
        assert content_type == CONTENT_TYPE_LATEST

    def test_metrics_output_contains_expected_metrics(self):
        """Output should contain expected metric names."""
        # Add some metrics first
        SCRAPER_VIDEOS_PROCESSED_TOTAL.labels(scraper_type="trending").inc()
        API_REQUESTS_TOTAL.labels(method="GET", endpoint="/test", status_code=200).inc()
        
        output = get_metrics_output().decode()
        
        assert "scraper_videos_processed_total" in output
        assert "api_requests_total" in output


class TestGetMetricsCollector:
    """Test the get_metrics_collector singleton function."""

    def test_singleton_instance(self):
        """Should return the same instance."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        
        assert collector1 is collector2

    def test_collector_is_configured(self):
        """Should return a configured collector."""
        collector = get_metrics_collector()
        
        assert isinstance(collector, MetricsCollector)
