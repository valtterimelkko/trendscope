"""
Unit tests for Health Check System.

Tests HealthAggregator, ComponentHealth, HealthCheckResponse,
and built-in health check functions.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Import FakeDatabasePool and FakeRedis from conftest
from monitoring.tests.conftest import FakeDatabasePool, FakeRedis

from monitoring.health_aggregator import (
    HealthStatus,
    ComponentHealth,
    HealthCheckResponse,
    HealthCheck,
    HealthAggregator,
    get_health_aggregator,
    check_database,
    check_redis,
    check_queue_depth,
    check_circuit_breaker,
    check_scraper_status,
)


class TestHealthStatus:
    """Test HealthStatus enum."""

    def test_health_status_values(self):
        """HealthStatus should have correct values."""
        assert HealthStatus.PASS == "pass"
        assert HealthStatus.WARN == "warn"
        assert HealthStatus.FAIL == "fail"

    def test_health_status_comparison(self):
        """HealthStatus should be comparable."""
        assert HealthStatus.PASS != HealthStatus.FAIL
        assert HealthStatus.WARN != HealthStatus.PASS


class TestComponentHealth:
    """Test ComponentHealth model."""

    def test_component_health_creation(self):
        """Should create ComponentHealth with required fields."""
        health = ComponentHealth(
            status=HealthStatus.PASS,
            component_id="test-1",
            component_type="database",
            observed_value=10,
            observed_unit="ms",
            output="Connection successful",
        )
        
        assert health.status == HealthStatus.PASS
        assert health.component_id == "test-1"
        assert health.component_type == "database"
        assert health.observed_value == 10
        assert health.observed_unit == "ms"
        assert health.output == "Connection successful"
        assert isinstance(health.time, datetime)

    def test_component_health_defaults(self):
        """Should use defaults for optional fields."""
        health = ComponentHealth(status=HealthStatus.PASS)
        
        assert health.component_id is None
        assert health.component_type is None
        assert health.observed_value is None
        assert health.observed_unit is None
        assert health.output is None
        assert health.links is None

    def test_to_prometheus_value_pass(self):
        """PASS should convert to 1."""
        health = ComponentHealth(status=HealthStatus.PASS)
        assert health.to_prometheus_value() == 1

    def test_to_prometheus_value_warn(self):
        """WARN should convert to 0."""
        health = ComponentHealth(status=HealthStatus.WARN)
        assert health.to_prometheus_value() == 0

    def test_to_prometheus_value_fail(self):
        """FAIL should convert to 0."""
        health = ComponentHealth(status=HealthStatus.FAIL)
        assert health.to_prometheus_value() == 0


class TestHealthCheckResponse:
    """Test HealthCheckResponse model."""

    def test_response_creation(self):
        """Should create response with all fields."""
        checks = {
            "database": ComponentHealth(
                status=HealthStatus.PASS,
                component_type="database",
                output="Connected",
            ),
            "redis": ComponentHealth(
                status=HealthStatus.PASS,
                component_type="cache",
                output="Connected",
            ),
        }
        
        response = HealthCheckResponse(
            status=HealthStatus.PASS,
            version="1.0.0",
            release_id="1.0.0",
            service_id="test-service",
            checks=checks,
            description="Test health check",
        )
        
        assert response.status == HealthStatus.PASS
        assert response.version == "1.0.0"
        assert response.release_id == "1.0.0"
        assert response.service_id == "test-service"
        assert len(response.checks) == 2
        assert response.description == "Test health check"


class TestHealthCheck:
    """Test HealthCheck class."""

    def test_health_check_creation(self):
        """Should create health check with metadata."""
        async def check_func():
            return ComponentHealth(status=HealthStatus.PASS)
        
        check = HealthCheck(
            name="database",
            check_func=check_func,
            component_type="database",
            critical=True,
        )
        
        assert check.name == "database"
        assert check.check_func == check_func
        assert check.component_type == "database"
        assert check.critical is True

    def test_health_check_non_critical(self):
        """Should support non-critical checks."""
        async def check_func():
            return ComponentHealth(status=HealthStatus.WARN)
        
        check = HealthCheck(
            name="cache",
            check_func=check_func,
            component_type="cache",
            critical=False,
        )
        
        assert check.critical is False


class TestHealthAggregatorInitialization:
    """Test HealthAggregator initialization."""

    def test_initialization_with_defaults(self):
        """Should initialize with default values."""
        aggregator = HealthAggregator(service_name="test-service")
        
        assert aggregator.service_name == "test-service"
        assert aggregator.version == "1.0.0"
        assert aggregator.release_id == "1.0.0"
        assert aggregator._checks == {}
        assert aggregator._is_ready is False

    def test_initialization_with_custom_version(self):
        """Should accept custom version."""
        aggregator = HealthAggregator(
            service_name="test-service",
            version="2.0.0",
            release_id="2.0.0-build123",
        )
        
        assert aggregator.version == "2.0.0"
        assert aggregator.release_id == "2.0.0-build123"

    def test_uptime_tracking(self):
        """Should track uptime from initialization."""
        aggregator = HealthAggregator(service_name="test-service")
        
        import time
        time.sleep(0.01)
        
        uptime = aggregator.get_uptime()
        assert uptime >= 0.01


class TestHealthAggregatorRegistration:
    """Test health check registration."""

    def test_register_check(self):
        """Should register a health check."""
        aggregator = HealthAggregator(service_name="test-service")
        
        async def check_func():
            return ComponentHealth(status=HealthStatus.PASS)
        
        aggregator.register_check(
            name="database",
            check_func=check_func,
            component_type="database",
            critical=True,
        )
        
        assert "database" in aggregator._checks
        assert aggregator._checks["database"].name == "database"

    def test_register_multiple_checks(self):
        """Should register multiple checks."""
        aggregator = HealthAggregator(service_name="test-service")
        
        async def db_check():
            return ComponentHealth(status=HealthStatus.PASS)
        
        async def redis_check():
            return ComponentHealth(status=HealthStatus.PASS)
        
        aggregator.register_check("database", db_check, "database", True)
        aggregator.register_check("redis", redis_check, "cache", True)
        
        assert len(aggregator._checks) == 2


class TestHealthAggregatorCheckHealth:
    """Test health check execution."""

    @pytest.mark.asyncio
    async def test_all_checks_pass(self):
        """Should return PASS when all checks pass."""
        aggregator = HealthAggregator(service_name="test-service")
        
        async def passing_check():
            return ComponentHealth(status=HealthStatus.PASS)
        
        aggregator.register_check("check1", passing_check, "test", True)
        aggregator.register_check("check2", passing_check, "test", True)
        
        result = await aggregator.check_health()
        
        assert result.status == HealthStatus.PASS
        assert len(result.checks) == 2

    @pytest.mark.asyncio
    async def test_any_fail_returns_fail(self):
        """Should return FAIL when any critical check fails."""
        aggregator = HealthAggregator(service_name="test-service")
        
        async def passing_check():
            return ComponentHealth(status=HealthStatus.PASS)
        
        async def failing_check():
            return ComponentHealth(status=HealthStatus.FAIL)
        
        aggregator.register_check("passing", passing_check, "test", True)
        aggregator.register_check("failing", failing_check, "test", True)
        
        result = await aggregator.check_health()
        
        assert result.status == HealthStatus.FAIL

    @pytest.mark.asyncio
    async def test_warning_returns_warn(self):
        """Should return WARN when no failures but warnings exist."""
        aggregator = HealthAggregator(service_name="test-service")
        
        async def warning_check():
            return ComponentHealth(status=HealthStatus.WARN)
        
        aggregator.register_check("warning", warning_check, "test", True)
        
        result = await aggregator.check_health()
        
        assert result.status == HealthStatus.WARN

    @pytest.mark.asyncio
    async def test_non_critical_failure_returns_fail(self):
        """Should return FAIL when any check fails, regardless of critical flag."""
        aggregator = HealthAggregator(service_name="test-service")
        
        async def passing_check():
            return ComponentHealth(status=HealthStatus.PASS)
        
        async def failing_check():
            return ComponentHealth(status=HealthStatus.FAIL)
        
        aggregator.register_check("passing", passing_check, "test", True)
        aggregator.register_check("failing", failing_check, "test", False)  # Non-critical
        
        result = await aggregator.check_health()
        
        # Any failure (critical or not) results in FAIL status
        assert result.status == HealthStatus.FAIL

    @pytest.mark.asyncio
    async def test_check_exception_handling(self):
        """Should handle exceptions in check functions."""
        aggregator = HealthAggregator(service_name="test-service")
        
        async def error_check():
            raise Exception("Check failed")
        
        aggregator.register_check("error", error_check, "test", True)
        
        result = await aggregator.check_health()
        
        assert result.status == HealthStatus.FAIL
        assert result.checks["error"].status == HealthStatus.FAIL
        assert "Check failed" in result.checks["error"].output

    @pytest.mark.asyncio
    async def test_concurrent_check_execution(self):
        """Should execute checks concurrently."""
        aggregator = HealthAggregator(service_name="test-service")
        
        execution_order = []
        
        async def slow_check():
            execution_order.append("slow_start")
            await asyncio.sleep(0.05)
            execution_order.append("slow_end")
            return ComponentHealth(status=HealthStatus.PASS)
        
        async def fast_check():
            execution_order.append("fast_start")
            await asyncio.sleep(0.01)
            execution_order.append("fast_end")
            return ComponentHealth(status=HealthStatus.PASS)
        
        aggregator.register_check("slow", slow_check, "test", True)
        aggregator.register_check("fast", fast_check, "test", True)
        
        await aggregator.check_health()
        
        # Both should start before either ends
        assert execution_order[0] in ["slow_start", "fast_start"]
        assert execution_order[1] in ["slow_start", "fast_start"]


class TestHealthAggregatorReadiness:
    """Test readiness probe functionality."""

    @pytest.mark.asyncio
    async def test_not_ready_when_not_marked(self):
        """Should return False when not marked ready."""
        aggregator = HealthAggregator(service_name="test-service")
        
        is_ready = await aggregator.is_ready()
        
        assert is_ready is False

    @pytest.mark.asyncio
    async def test_ready_when_marked_and_healthy(self):
        """Should return True when marked ready and all checks pass."""
        aggregator = HealthAggregator(service_name="test-service")
        
        async def passing_check():
            return ComponentHealth(status=HealthStatus.PASS)
        
        aggregator.register_check("database", passing_check, "database", True)
        aggregator.mark_ready()
        
        is_ready = await aggregator.is_ready()
        
        assert is_ready is True

    @pytest.mark.asyncio
    async def test_not_ready_when_critical_fails(self):
        """Should return False when critical check fails."""
        aggregator = HealthAggregator(service_name="test-service")
        
        async def failing_check():
            return ComponentHealth(status=HealthStatus.FAIL)
        
        aggregator.register_check("database", failing_check, "database", True)
        aggregator.mark_ready()
        
        is_ready = await aggregator.is_ready()
        
        assert is_ready is False

    def test_mark_ready(self):
        """Should mark service as ready."""
        aggregator = HealthAggregator(service_name="test-service")
        
        assert aggregator._is_ready is False
        
        aggregator.mark_ready()
        
        assert aggregator._is_ready is True

    def test_mark_not_ready(self):
        """Should mark service as not ready."""
        aggregator = HealthAggregator(service_name="test-service")
        
        aggregator.mark_ready()
        assert aggregator._is_ready is True
        
        aggregator.mark_not_ready()
        assert aggregator._is_ready is False


class TestHealthAggregatorLiveness:
    """Test liveness probe functionality."""

    @pytest.mark.asyncio
    async def test_always_live(self):
        """Should always return True for liveness."""
        aggregator = HealthAggregator(service_name="test-service")
        
        is_live = await aggregator.is_live()
        
        assert is_live is True


class TestCheckDatabase:
    """Test database health check function."""

    @pytest.mark.asyncio
    async def test_healthy_database(self, mock_db_pool):
        """Should return PASS for healthy database."""
        result = await check_database(mock_db_pool)
        
        assert result.status == HealthStatus.PASS
        assert result.component_type == "database"
        assert result.observed_value is not None
        assert result.observed_unit == "ms"
        assert "Connected" in result.output

    @pytest.mark.asyncio
    async def test_slow_database_returns_warn(self):
        """Should return WARN for slow database (>100ms)."""
        slow_db = FakeDatabasePool(healthy=True, latency_ms=150)
        
        result = await check_database(slow_db)
        
        assert result.status == HealthStatus.WARN

    @pytest.mark.asyncio
    async def test_unhealthy_database_returns_fail(self, mock_db_pool_unhealthy):
        """Should return FAIL for unhealthy database."""
        result = await check_database(mock_db_pool_unhealthy)
        
        assert result.status == HealthStatus.FAIL
        assert result.component_type == "database"
        assert "failed" in result.output


class TestCheckRedis:
    """Test Redis health check function."""

    @pytest.mark.asyncio
    async def test_healthy_redis(self, mock_redis):
        """Should return PASS for healthy Redis."""
        result = await check_redis(mock_redis)
        
        assert result.status == HealthStatus.PASS
        assert result.component_type == "cache"
        assert result.observed_value is not None
        assert result.observed_unit == "ms"

    @pytest.mark.asyncio
    async def test_slow_redis_returns_warn(self, mock_redis_slow):
        """Should return WARN for slow Redis (>50ms)."""
        result = await check_redis(mock_redis_slow)
        
        assert result.status == HealthStatus.WARN

    @pytest.mark.asyncio
    async def test_unhealthy_redis_returns_fail(self, mock_redis_unhealthy):
        """Should return FAIL for unhealthy Redis."""
        result = await check_redis(mock_redis_unhealthy)
        
        assert result.status == HealthStatus.FAIL


class TestCheckQueueDepth:
    """Test queue depth health check function."""

    @pytest.mark.asyncio
    async def test_healthy_queue_depth(self, mock_redis):
        """Should return PASS for healthy queue depth (<70%)."""
        # Add some items (50% of max)
        for i in range(500):
            await mock_redis.lpush("tiktok:videos", f"video_{i}")
        
        result = await check_queue_depth(mock_redis, "tiktok:videos", max_depth=1000)
        
        assert result.status == HealthStatus.PASS
        assert result.observed_value == 500
        assert result.observed_unit == "items"

    @pytest.mark.asyncio
    async def test_warning_queue_depth(self, mock_redis):
        """Should return WARN for warning queue depth (70-90%)."""
        # Add items to 80% capacity
        for i in range(800):
            await mock_redis.lpush("tiktok:videos", f"video_{i}")
        
        result = await check_queue_depth(mock_redis, "tiktok:videos", max_depth=1000)
        
        assert result.status == HealthStatus.WARN

    @pytest.mark.asyncio
    async def test_critical_queue_depth(self, mock_redis):
        """Should return FAIL for critical queue depth (>90%)."""
        # Add items to 95% capacity
        for i in range(950):
            await mock_redis.lpush("tiktok:videos", f"video_{i}")
        
        result = await check_queue_depth(mock_redis, "tiktok:videos", max_depth=1000)
        
        assert result.status == HealthStatus.FAIL


class MockCircuitBreaker:
    """Mock circuit breaker for testing."""
    
    def __init__(self, state: str = "closed", failure_count: int = 0):
        self._state = state
        self._failure_count = failure_count
    
    def get_state(self):
        return {
            "state": self._state,
            "failure_count": self._failure_count,
        }


class TestCheckCircuitBreaker:
    """Test circuit breaker health check function."""

    @pytest.mark.asyncio
    async def test_closed_circuit_returns_pass(self):
        """Should return PASS for closed circuit."""
        cb = MockCircuitBreaker(state="closed")
        
        result = await check_circuit_breaker(cb)
        
        assert result.status == HealthStatus.PASS
        assert result.component_type == "circuit_breaker"
        assert result.observed_value == "closed"

    @pytest.mark.asyncio
    async def test_half_open_circuit_returns_warn(self):
        """Should return WARN for half-open circuit."""
        cb = MockCircuitBreaker(state="half_open")
        
        result = await check_circuit_breaker(cb)
        
        assert result.status == HealthStatus.WARN

    @pytest.mark.asyncio
    async def test_open_circuit_returns_warn(self):
        """Should return WARN for open circuit."""
        cb = MockCircuitBreaker(state="open")
        
        result = await check_circuit_breaker(cb)
        
        assert result.status == HealthStatus.WARN

    @pytest.mark.asyncio
    async def test_failure_count_included(self):
        """Should include failure count in output."""
        cb = MockCircuitBreaker(state="open", failure_count=10)
        
        result = await check_circuit_breaker(cb)
        
        assert "Failures: 10" in result.output


class TestCheckScraperStatus:
    """Test scraper status health check function."""

    @pytest.mark.asyncio
    async def test_no_scrapes_returns_warn(self):
        """Should return WARN when no scrapes completed."""
        result = await check_scraper_status(None)
        
        assert result.status == HealthStatus.WARN
        assert "No scrapes completed yet" in result.output

    @pytest.mark.asyncio
    async def test_recent_scrape_returns_pass(self):
        """Should return PASS for recent scrape."""
        last_scrape = datetime.utcnow()
        
        result = await check_scraper_status(last_scrape, max_age_seconds=600)
        
        assert result.status == HealthStatus.PASS
        assert result.observed_value == 0

    @pytest.mark.asyncio
    async def test_old_scrape_returns_warn(self):
        """Should return WARN for old scrape."""
        last_scrape = datetime.utcnow() - timedelta(seconds=900)
        
        result = await check_scraper_status(last_scrape, max_age_seconds=600)
        
        assert result.status == HealthStatus.WARN

    @pytest.mark.asyncio
    async def test_very_old_scrape_returns_fail(self):
        """Should return FAIL for very old scrape."""
        last_scrape = datetime.utcnow() - timedelta(seconds=1500)
        
        result = await check_scraper_status(last_scrape, max_age_seconds=600)
        
        assert result.status == HealthStatus.FAIL


class TestGetHealthAggregator:
    """Test the get_health_aggregator singleton function."""

    def test_singleton_instance(self):
        """Should return the same instance."""
        # Reset singleton first
        import monitoring.health_aggregator as ha
        ha._health_aggregator = None
        
        agg1 = get_health_aggregator("test-service", "1.0.0")
        agg2 = get_health_aggregator("test-service", "1.0.0")
        
        assert agg1 is agg2

    def test_requires_service_name_on_first_call(self):
        """Should require service name on first initialization."""
        # Reset singleton
        import monitoring.health_aggregator as ha
        ha._health_aggregator = None
        
        with pytest.raises(ValueError, match="service_name required"):
            get_health_aggregator()

    def test_returns_existing_without_service_name(self):
        """Should return existing instance without service name."""
        # Reset singleton
        import monitoring.health_aggregator as ha
        ha._health_aggregator = None
        
        # Initialize first
        agg1 = get_health_aggregator("test-service", "1.0.0")
        
        # Get without service name
        agg2 = get_health_aggregator()
        
        assert agg1 is agg2
