"""
Unit tests for the Health Check service.

Tests HealthChecker class, health endpoint logic,
component status aggregation, and healthy/unhealthy state detection.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from scraper.health import HealthChecker, get_health_checker
from scraper.models import HealthStatus, CheckStatus, ComponentCheck, ScraperHealth
from scraper.circuit_breaker import CircuitBreaker, CircuitState


class MockRedis:
    """Mock Redis client for testing."""
    
    def __init__(self, healthy=True, latency_ms=10):
        self.healthy = healthy
        self.latency_ms = latency_ms
    
    async def ping(self):
        if not self.healthy:
            raise Exception("Redis connection failed")
        await asyncio.sleep(self.latency_ms / 1000)
        return True


class TestHealthCheckerInitialization:
    """Test HealthChecker initialization."""

    def test_initialization_sets_defaults(self):
        """HealthChecker should initialize with default values."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        
        checker = HealthChecker(redis, circuit)
        
        assert checker.redis is redis
        assert checker.circuit_breaker is circuit
        assert checker.total_videos_scraped == 0
        assert checker.total_errors == 0
        assert checker.last_scrape_time is None
        assert checker._is_ready is False

    def test_startup_time_is_set(self):
        """startup_time should be set on initialization."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        
        before = datetime.utcnow()
        checker = HealthChecker(redis, circuit)
        after = datetime.utcnow()
        
        assert before <= checker.startup_time <= after


class TestHealthCheckerUpdateMetrics:
    """Test update_scrape_metrics method."""

    def test_updates_video_count(self):
        """update_scrape_metrics should increment video count."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        checker.update_scrape_metrics(videos_scraped=10)
        
        assert checker.total_videos_scraped == 10

    def test_updates_error_count(self):
        """update_scrape_metrics should increment error count."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        checker.update_scrape_metrics(errors=3)
        
        assert checker.total_errors == 3

    def test_updates_last_scrape_time(self):
        """update_scrape_metrics should update last_scrape_time."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        scrape_time = datetime.utcnow()
        checker.update_scrape_metrics(last_scrape=scrape_time)
        
        assert checker.last_scrape_time == scrape_time

    def test_marks_ready_when_last_scrape_provided(self):
        """update_scrape_metrics should mark ready when last_scrape provided."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        checker.update_scrape_metrics(last_scrape=datetime.utcnow())
        
        assert checker._is_ready is True

    def test_accumulates_videos_across_calls(self):
        """update_scrape_metrics should accumulate video counts."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        checker.update_scrape_metrics(videos_scraped=10)
        checker.update_scrape_metrics(videos_scraped=5)
        
        assert checker.total_videos_scraped == 15

    def test_accumulates_errors_across_calls(self):
        """update_scrape_metrics should accumulate error counts."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        checker.update_scrape_metrics(errors=2)
        checker.update_scrape_metrics(errors=3)
        
        assert checker.total_errors == 5


class TestHealthCheckerMarkReady:
    """Test mark_ready and mark_not_ready methods."""

    def test_mark_ready_sets_ready_true(self):
        """mark_ready should set _is_ready to True."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        checker.mark_ready()
        
        assert checker._is_ready is True

    def test_mark_not_ready_sets_ready_false(self):
        """mark_not_ready should set _is_ready to False."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        checker.mark_ready()
        checker.mark_not_ready()
        
        assert checker._is_ready is False


class TestHealthCheckerRedisCheck:
    """Test _check_redis method."""

    @pytest.mark.asyncio
    async def test_healthy_redis_returns_pass(self):
        """Healthy Redis should return PASS status."""
        redis = MockRedis(healthy=True, latency_ms=10)
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        check = await checker._check_redis()
        
        assert check.status == CheckStatus.PASS
        assert check.latency_ms >= 10
        assert check.error is None

    @pytest.mark.asyncio
    async def test_slow_redis_returns_warn(self):
        """Slow Redis (>100ms) should return WARN status."""
        redis = MockRedis(healthy=True, latency_ms=150)
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        check = await checker._check_redis()
        
        assert check.status == CheckStatus.WARN
        assert check.latency_ms >= 150

    @pytest.mark.asyncio
    async def test_unhealthy_redis_returns_fail(self):
        """Unhealthy Redis should return FAIL status."""
        redis = MockRedis(healthy=False)
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        check = await checker._check_redis()
        
        assert check.status == CheckStatus.FAIL
        assert check.error is not None
        assert check.latency_ms is None


class TestHealthCheckerCircuitBreakerCheck:
    """Test _check_circuit_breaker method."""

    def test_closed_circuit_returns_pass(self):
        """Closed circuit breaker should return PASS."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        circuit.state = CircuitState.CLOSED
        checker = HealthChecker(redis, circuit)
        
        check = checker._check_circuit_breaker()
        
        assert check.status == CheckStatus.PASS
        assert check.state == "closed"

    def test_half_open_circuit_returns_warn(self):
        """Half-open circuit breaker should return WARN."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        circuit.state = CircuitState.HALF_OPEN
        checker = HealthChecker(redis, circuit)
        
        check = checker._check_circuit_breaker()
        
        assert check.status == CheckStatus.WARN
        assert check.state == "half_open"

    def test_open_circuit_returns_warn(self):
        """Open circuit breaker should return WARN."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        circuit.state = CircuitState.OPEN
        checker = HealthChecker(redis, circuit)
        
        check = checker._check_circuit_breaker()
        
        assert check.status == CheckStatus.WARN
        assert check.state == "open"

    def test_failure_count_included(self):
        """Failure count should be included in check."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        circuit.failure_count = 5
        checker = HealthChecker(redis, circuit)
        
        check = checker._check_circuit_breaker()
        
        assert check.failure_count == 5


class TestHealthCheckerScraperCheck:
    """Test _check_scraper method."""

    @pytest.mark.asyncio
    async def test_no_scrapes_returns_warn(self):
        """No scrapes completed should return WARN."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        check = checker._check_scraper()
        
        assert check.status == CheckStatus.WARN
        assert check.error == "No scrapes completed yet"

    @pytest.mark.asyncio
    async def test_recent_scrape_returns_pass(self):
        """Recent scrape should return PASS."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        checker.last_scrape_time = datetime.utcnow()
        checker.total_videos_scraped = 100
        
        check = checker._check_scraper()
        
        assert check.status == CheckStatus.PASS
        assert check.videos_scraped == 100

    @pytest.mark.asyncio
    async def test_old_scrape_returns_warn(self):
        """Old scrape should return WARN."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        # Scrape from 20 minutes ago (assuming 300s interval, 2x = 600s)
        checker.last_scrape_time = datetime.utcnow() - timedelta(seconds=600)
        
        with patch('scraper.health.settings') as mock_settings:
            mock_settings.scrape_interval = 300
            check = checker._check_scraper()
        
        assert check.status == CheckStatus.WARN

    @pytest.mark.asyncio
    async def test_very_old_scrape_returns_fail(self):
        """Very old scrape should return FAIL."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        # Scrape from 40 minutes ago (4x interval)
        checker.last_scrape_time = datetime.utcnow() - timedelta(seconds=1200)
        
        with patch('scraper.health.settings') as mock_settings:
            mock_settings.scrape_interval = 300
            check = checker._check_scraper()
        
        assert check.status == CheckStatus.FAIL

    @pytest.mark.asyncio
    async def test_last_scrape_iso_format(self):
        """last_scrape should be in ISO format."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        scrape_time = datetime.utcnow()
        checker.last_scrape_time = scrape_time
        
        check = checker._check_scraper()
        
        assert check.last_scrape == scrape_time.isoformat()


class TestHealthCheckerOverallStatus:
    """Test overall status determination."""

    @pytest.mark.asyncio
    async def test_all_pass_returns_healthy(self):
        """All checks passing should return HEALTHY."""
        redis = MockRedis(healthy=True, latency_ms=10)
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        checker.last_scrape_time = datetime.utcnow()
        
        health = await checker.check()
        
        assert health.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_any_warn_returns_degraded(self):
        """Any warning should return DEGRADED."""
        redis = MockRedis(healthy=True, latency_ms=150)  # Slow Redis
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        checker.last_scrape_time = datetime.utcnow()
        
        health = await checker.check()
        
        assert health.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_any_fail_returns_unhealthy(self):
        """Any failure should return UNHEALTHY."""
        redis = MockRedis(healthy=False)  # Failed Redis
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        health = await checker.check()
        
        assert health.status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_no_scrapes_is_degraded_not_unhealthy(self):
        """No scrapes should be DEGRADED not UNHEALTHY."""
        redis = MockRedis(healthy=True, latency_ms=10)
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        # No scrapes yet
        
        health = await checker.check()
        
        assert health.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_health_response_format(self):
        """Health response should have correct format."""
        redis = MockRedis(healthy=True, latency_ms=10)
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        checker.last_scrape_time = datetime.utcnow()
        checker.total_videos_scraped = 100
        checker.total_errors = 5
        
        health = await checker.check()
        
        assert health.version == "1.0.0"
        assert isinstance(health.timestamp, datetime)
        assert "redis" in health.checks
        assert "circuit_breaker" in health.checks
        assert "scraper" in health.checks
        assert "videos_scraped" in health.metrics
        assert "errors" in health.metrics
        assert "uptime_seconds" in health.metrics


class TestHealthCheckerIsReady:
    """Test is_ready method."""

    def test_not_ready_when_never_scraped(self):
        """Should not be ready when never scraped."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        assert checker.is_ready() is False

    def test_ready_after_scrape(self):
        """Should be ready after at least one scrape."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        checker.update_scrape_metrics(last_scrape=datetime.utcnow())
        
        assert checker.is_ready() is True

    def test_not_ready_when_circuit_open(self):
        """Should not be ready when circuit is open."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        circuit.state = CircuitState.OPEN
        checker = HealthChecker(redis, circuit)
        checker.update_scrape_metrics(last_scrape=datetime.utcnow())
        
        assert checker.is_ready() is False

    def test_not_ready_when_marked_not_ready(self):
        """Should not be ready when marked not ready."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        checker.mark_ready()
        checker.mark_not_ready()
        
        assert checker.is_ready() is False


class TestHealthCheckerGetMetrics:
    """Test get_metrics method."""

    def test_returns_dict(self):
        """get_metrics should return dictionary."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        metrics = checker.get_metrics()
        
        assert isinstance(metrics, dict)

    def test_includes_required_metrics(self):
        """Metrics should include all required fields."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        checker.total_videos_scraped = 100
        checker.total_errors = 5
        
        metrics = checker.get_metrics()
        
        assert "scraper_videos_scraped_total" in metrics
        assert "scraper_errors_total" in metrics
        assert "scraper_circuit_breaker_state" in metrics
        assert "scraper_ready" in metrics
        assert "scraper_uptime_seconds" in metrics

    def test_circuit_breaker_state_closed(self):
        """Circuit breaker state should be 0 when closed."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        circuit.state = CircuitState.CLOSED
        checker = HealthChecker(redis, circuit)
        
        metrics = checker.get_metrics()
        
        assert metrics["scraper_circuit_breaker_state"] == 0

    def test_circuit_breaker_state_half_open(self):
        """Circuit breaker state should be 1 when half-open."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        circuit.state = CircuitState.HALF_OPEN
        checker = HealthChecker(redis, circuit)
        
        metrics = checker.get_metrics()
        
        assert metrics["scraper_circuit_breaker_state"] == 1

    def test_circuit_breaker_state_open(self):
        """Circuit breaker state should be 2 when open."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        circuit.state = CircuitState.OPEN
        checker = HealthChecker(redis, circuit)
        
        metrics = checker.get_metrics()
        
        assert metrics["scraper_circuit_breaker_state"] == 2

    def test_ready_metric_true(self):
        """scraper_ready should be 1 when ready."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        checker.mark_ready()
        
        metrics = checker.get_metrics()
        
        assert metrics["scraper_ready"] == 1

    def test_ready_metric_false(self):
        """scraper_ready should be 0 when not ready."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        metrics = checker.get_metrics()
        
        assert metrics["scraper_ready"] == 0

    def test_uptime_seconds_calculated(self):
        """uptime_seconds should be calculated correctly."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        checker.startup_time = datetime.utcnow() - timedelta(seconds=60)
        
        metrics = checker.get_metrics()
        
        assert metrics["scraper_uptime_seconds"] >= 60


class TestHealthCheckerEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_health_check_with_zero_metrics(self):
        """Health check should work with zero metrics."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        health = await checker.check()
        
        assert health.metrics["videos_scraped"] == 0
        assert health.metrics["errors"] == 0

    @pytest.mark.asyncio
    async def test_health_check_duration_measured(self):
        """Health check should measure its own duration."""
        redis = MockRedis(healthy=True, latency_ms=50)
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        
        health = await checker.check()
        
        assert health.metrics["check_duration_ms"] >= 50

    @pytest.mark.asyncio
    async def test_multiple_health_checks_accumulate(self):
        """Multiple health checks should accumulate metrics."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        checker.total_videos_scraped = 100
        
        health1 = await checker.check()
        health2 = await checker.check()
        
        assert health1.metrics["videos_scraped"] == 100
        assert health2.metrics["videos_scraped"] == 100

    @pytest.mark.asyncio
    async def test_scraper_check_with_zero_scrape_interval(self):
        """Scraper check should handle edge case intervals."""
        redis = MockRedis()
        circuit = CircuitBreaker()
        checker = HealthChecker(redis, circuit)
        checker.last_scrape_time = datetime.utcnow() - timedelta(seconds=1)
        
        with patch('scraper.health.settings') as mock_settings:
            mock_settings.scrape_interval = 0
            check = checker._check_scraper()
        
        # With 0 interval, any time is beyond 2x interval
        assert check.status == CheckStatus.FAIL
