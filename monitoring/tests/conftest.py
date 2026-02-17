"""
Test fixtures and configuration for monitoring module tests.

Provides fixtures for:
- Metrics collector
- Health aggregator
- Service registry
- Mock services
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from monitoring.metrics import MetricsCollector
from monitoring.health_aggregator import (
    HealthAggregator,
    HealthStatus,
    ComponentHealth,
    get_health_aggregator,
)
from monitoring.service_registry import ServiceRegistry, ServiceStatus, ServiceType
from monitoring.aggregator import MetricsAggregator
from monitoring.alerts import AlertNotifier, SystemHealthAlerter, AlertSeverity, AlertRule
from monitoring.config import MonitoringConfig, AlertThresholds


# =============================================================================
# Event Loop Fixture
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Metrics Collector Fixtures
# =============================================================================

@pytest.fixture
def metrics_collector() -> MetricsCollector:
    """Provide a fresh MetricsCollector instance."""
    return MetricsCollector(namespace="test")


@pytest.fixture
def mock_metrics_collector() -> MagicMock:
    """Provide a mocked MetricsCollector."""
    mock = MagicMock(spec=MetricsCollector)
    mock.namespace = "test"
    mock._start_time = datetime.utcnow().timestamp()
    return mock


# =============================================================================
# Health Aggregator Fixtures
# =============================================================================

@pytest.fixture
def health_aggregator() -> HealthAggregator:
    """Provide a fresh HealthAggregator instance."""
    return HealthAggregator(
        service_name="test-service",
        version="1.0.0",
    )


@pytest_asyncio.fixture
async def health_aggregator_with_checks() -> AsyncGenerator[HealthAggregator, None]:
    """Provide a HealthAggregator with some registered checks."""
    aggregator = HealthAggregator(
        service_name="test-service",
        version="1.0.0",
    )
    
    # Register a passing check
    async def passing_check():
        return ComponentHealth(
            status=HealthStatus.PASS,
            component_type="test",
            output="All good",
        )
    
    # Register a warning check
    async def warning_check():
        return ComponentHealth(
            status=HealthStatus.WARN,
            component_type="test",
            output="Something is slow",
        )
    
    # Register a failing check
    async def failing_check():
        return ComponentHealth(
            status=HealthStatus.FAIL,
            component_type="test",
            output="Connection failed",
        )
    
    aggregator.register_check("passing", passing_check, "test", critical=True)
    aggregator.register_check("warning", warning_check, "test", critical=False)
    aggregator.register_check("failing", failing_check, "test", critical=True)
    
    yield aggregator


@pytest.fixture
def mock_health_checker() -> MagicMock:
    """Provide a mocked health check function."""
    async def mock_check():
        return ComponentHealth(
            status=HealthStatus.PASS,
            component_type="mock",
            observed_value=10,
            observed_unit="ms",
            output="Mock check passed",
        )
    
    return MagicMock(side_effect=mock_check)


# =============================================================================
# Mock Database and Redis Fixtures
# =============================================================================

class FakeDatabasePool:
    """Mock database pool for testing."""
    
    def __init__(self, healthy: bool = True, latency_ms: int = 10):
        self.healthy = healthy
        self.latency_ms = latency_ms
    
    def acquire(self):
        return FakeConnection(self.healthy, self.latency_ms)
    
    async def close(self):
        pass


class FakeConnection:
    """Mock database connection for testing."""
    
    def __init__(self, healthy: bool = True, latency_ms: int = 10):
        self.healthy = healthy
        self.latency_ms = latency_ms
    
    async def __aenter__(self):
        if not self.healthy:
            raise Exception("Database connection failed")
        await asyncio.sleep(self.latency_ms / 1000)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def fetchval(self, query: str):
        return 1


class FakeRedis:
    """Mock Redis client for testing."""
    
    def __init__(self, healthy: bool = True, latency_ms: int = 5):
        self.healthy = healthy
        self.latency_ms = latency_ms
        self._queues: Dict[str, list] = {}
    
    async def ping(self):
        if not self.healthy:
            raise Exception("Redis connection failed")
        await asyncio.sleep(self.latency_ms / 1000)
        return True
    
    async def llen(self, key: str) -> int:
        return len(self._queues.get(key, []))
    
    async def lpush(self, key: str, value: str):
        if key not in self._queues:
            self._queues[key] = []
        self._queues[key].append(value)


@pytest.fixture
def mock_db_pool():
    """Provide a healthy mock database pool."""
    return FakeDatabasePool(healthy=True, latency_ms=10)


@pytest.fixture
def mock_db_pool_unhealthy():
    """Provide an unhealthy mock database pool."""
    return FakeDatabasePool(healthy=False)


@pytest.fixture
def mock_redis():
    """Provide a healthy mock Redis client."""
    return FakeRedis(healthy=True, latency_ms=5)


@pytest.fixture
def mock_redis_unhealthy():
    """Provide an unhealthy mock Redis client."""
    return FakeRedis(healthy=False)


@pytest.fixture
def mock_redis_slow():
    """Provide a slow mock Redis client (>100ms)."""
    return FakeRedis(healthy=True, latency_ms=150)


# =============================================================================
# Service Registry Fixtures
# =============================================================================

@pytest.fixture
def service_registry() -> ServiceRegistry:
    """Provide a fresh ServiceRegistry instance."""
    return ServiceRegistry(
        heartbeat_timeout_seconds=60,
        cleanup_interval_seconds=30,
    )


@pytest.fixture
def populated_registry() -> ServiceRegistry:
    """Provide a ServiceRegistry with some registered services."""
    registry = ServiceRegistry()
    
    # Register some services
    registry.register(
        service_name="trendscope-api",
        service_type=ServiceType.API,
        port=8000,
        version="1.0.0",
    )
    registry.register(
        service_name="trendscope-scraper",
        service_type=ServiceType.SCRAPER,
        port=8001,
        version="1.0.0",
    )
    registry.register(
        service_name="trendscope-detection",
        service_type=ServiceType.DETECTION,
        port=8002,
        version="1.0.0",
    )
    
    return registry


# =============================================================================
# Metrics Aggregator Fixtures
# =============================================================================

@pytest.fixture
def metrics_aggregator() -> MetricsAggregator:
    """Provide a fresh MetricsAggregator instance."""
    return MetricsAggregator(
        aggregation_interval_seconds=60,
        retention_minutes=60,
    )


@pytest.fixture
def metrics_aggregator_with_data() -> MetricsAggregator:
    """Provide a MetricsAggregator with sample data."""
    aggregator = MetricsAggregator()
    
    # Add some service metrics
    aggregator.update_service_metrics(
        service_name="scraper-1",
        service_type="scraper",
        healthy=True,
        metrics={
            "videos_processed": 1000,
            "errors": 10,
            "rate_limit_hits": 5,
            "circuit_breaker_state": 0,
            "queue_depth": 100,
            "ready": True,
        },
    )
    
    aggregator.update_service_metrics(
        service_name="api-1",
        service_type="api",
        healthy=True,
        metrics={
            "requests_total": 5000,
            "errors_total": 50,
            "p95_latency_ms": 150,
        },
    )
    
    return aggregator


# =============================================================================
# Alert Fixtures
# =============================================================================

@pytest.fixture
def alert_notifier() -> AlertNotifier:
    """Provide an AlertNotifier instance."""
    return AlertNotifier(
        slack_webhook_url="https://hooks.slack.com/test",
        email_recipients=["test@example.com"],
    )


@pytest.fixture
def system_alerter() -> SystemHealthAlerter:
    """Provide a SystemHealthAlerter instance."""
    return SystemHealthAlerter()


@pytest.fixture
def alert_thresholds() -> AlertThresholds:
    """Provide default alert thresholds."""
    return AlertThresholds()


@pytest.fixture
def custom_alert_rule() -> AlertRule:
    """Provide a custom alert rule."""
    return AlertRule(
        name="TestAlert",
        description="Test alert rule",
        severity=AlertSeverity.WARNING,
        condition="test_metric > 100",
        for_duration_seconds=60,
        cooldown_seconds=300,
    )


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture
def monitoring_config() -> MonitoringConfig:
    """Provide a MonitoringConfig instance."""
    return MonitoringConfig(
        service_name="test-service",
        version="1.0.0",
        log_level="INFO",
        metrics_enabled=True,
        health_enabled=True,
    )


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Import and reset singletons
    import monitoring.metrics as metrics_module
    import monitoring.health_aggregator as health_module
    import monitoring.aggregator as aggregator_module
    import monitoring.service_registry as registry_module
    import monitoring.alerts as alerts_module
    
    # Reset singletons
    metrics_module._metrics_collector = None
    health_module._health_aggregator = None
    aggregator_module._metrics_aggregator = None
    registry_module._service_registry = None
    alerts_module._system_health_alerter = None
    
    yield
