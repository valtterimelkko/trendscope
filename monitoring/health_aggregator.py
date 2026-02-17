"""
Health Check Aggregator

Aggregates health status from all Trendscope components:
- Database connectivity
- Redis connectivity
- Scraper status
- Queue depth
- Circuit breaker state

Provides unified health check endpoints following the RFC standard:
https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-health-check
"""

import asyncio
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Awaitable

from pydantic import BaseModel, Field
import structlog


logger = structlog.get_logger(__name__)


class HealthStatus(str, Enum):
    """Health check status values."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class ComponentHealth(BaseModel):
    """Health status for a single component.

    Follows RFC draft-ietf-httpapi-health-check format.
    """

    status: HealthStatus
    component_id: Optional[str] = None
    component_type: Optional[str] = None
    observed_value: Optional[Any] = None
    observed_unit: Optional[str] = None
    time: datetime = Field(default_factory=datetime.utcnow)
    output: Optional[str] = None
    links: Optional[Dict[str, str]] = None

    def to_prometheus_value(self) -> int:
        """Convert status to Prometheus gauge value.

        Returns:
            1 for pass, 0 for fail, 0.5 for warn
        """
        if self.status == HealthStatus.PASS:
            return 1
        elif self.status == HealthStatus.WARN:
            return 0
        else:
            return 0


class HealthCheckResponse(BaseModel):
    """Health check response following RFC standard.

    https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-health-check
    """

    status: HealthStatus
    version: str
    release_id: str
    notes: Optional[List[str]] = None
    output: Optional[str] = None
    checks: Dict[str, ComponentHealth] = Field(default_factory=dict)
    links: Optional[Dict[str, str]] = None
    service_id: Optional[str] = None
    description: Optional[str] = None


class HealthCheck:
    """Definition of a health check.

    Wraps a check function with metadata.
    """

    def __init__(
        self,
        name: str,
        check_func: Callable[[], Awaitable[ComponentHealth]],
        component_type: Optional[str] = None,
        critical: bool = True,
    ):
        """Initialize a health check.

        Args:
            name: Unique name for this check
            check_func: Async function that returns ComponentHealth
            component_type: Type of component (database, cache, etc.)
            critical: If True, failure makes overall status unhealthy
        """
        self.name = name
        self.check_func = check_func
        self.component_type = component_type
        self.critical = critical


class HealthAggregator:
    """Aggregates health status from multiple components.

    Provides:
    - Overall health status
    - Individual component checks
    - Readiness probes for Kubernetes
    - Prometheus metrics integration

    Example:
        aggregator = HealthAggregator("trendscope-api", "1.0.0")

        # Register checks
        aggregator.register_check("database", check_database, "database")
        aggregator.register_check("redis", check_redis, "cache")

        # Get health status
        health = await aggregator.check_health()
    """

    def __init__(
        self,
        service_name: str,
        version: str = "1.0.0",
        release_id: Optional[str] = None,
    ):
        """Initialize the health aggregator.

        Args:
            service_name: Name of the service
            version: Service version
            release_id: Release identifier (defaults to version)
        """
        self.service_name = service_name
        self.version = version
        self.release_id = release_id or version
        self._checks: Dict[str, HealthCheck] = {}
        self._start_time = time.time()
        self._is_ready = False

    def register_check(
        self,
        name: str,
        check_func: Callable[[], Awaitable[ComponentHealth]],
        component_type: Optional[str] = None,
        critical: bool = True,
    ) -> None:
        """Register a health check.

        Args:
            name: Unique name for this check
            check_func: Async function returning ComponentHealth
            component_type: Type of component being checked
            critical: If True, failure affects overall health
        """
        self._checks[name] = HealthCheck(
            name=name,
            check_func=check_func,
            component_type=component_type,
            critical=critical,
        )
        logger.debug(
            "health_check_registered",
            name=name,
            component_type=component_type,
            critical=critical,
        )

    def mark_ready(self) -> None:
        """Mark the service as ready to accept traffic."""
        self._is_ready = True
        logger.info("service_marked_ready", service=self.service_name)

    def mark_not_ready(self) -> None:
        """Mark the service as not ready."""
        self._is_ready = False
        logger.info("service_marked_not_ready", service=self.service_name)

    async def check_health(self) -> HealthCheckResponse:
        """Run all health checks and return aggregated status.

        Returns:
            HealthCheckResponse with overall and component status
        """
        checks: Dict[str, ComponentHealth] = {}
        all_critical_pass = True
        any_fail = False
        any_warn = False

        # Run all checks concurrently
        tasks = {
            name: check.check_func()
            for name, check in self._checks.items()
        }

        results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True,
        )

        for (name, check), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                # Check threw an exception
                component_health = ComponentHealth(
                    status=HealthStatus.FAIL,
                    component_type=check.component_type,
                    output=f"Check failed: {str(result)}",
                )
                if check.critical:
                    all_critical_pass = False
                any_fail = True
            else:
                component_health = result
                if check.critical and component_health.status == HealthStatus.FAIL:
                    all_critical_pass = False
                if component_health.status == HealthStatus.FAIL:
                    any_fail = True
                if component_health.status == HealthStatus.WARN:
                    any_warn = True

            checks[name] = component_health

        # Determine overall status
        if all_critical_pass and not any_fail:
            status = HealthStatus.PASS
        elif any_fail:
            status = HealthStatus.FAIL
        else:
            status = HealthStatus.WARN

        return HealthCheckResponse(
            status=status,
            version=self.version,
            release_id=self.release_id,
            service_id=self.service_name,
            checks=checks,
            description=f"Health status for {self.service_name}",
        )

    async def is_ready(self) -> bool:
        """Check if service is ready to accept traffic.

        This is stricter than health - it checks:
        1. Service has explicitly marked itself ready
        2. All critical components are passing

        Returns:
            True if ready to accept traffic
        """
        if not self._is_ready:
            return False

        # Check critical components
        for name, check in self._checks.items():
            if check.critical:
                try:
                    result = await check.check_func()
                    if result.status == HealthStatus.FAIL:
                        return False
                except Exception:
                    return False

        return True

    async def is_live(self) -> bool:
        """Check if service is alive (liveness probe).

        This is the most basic check - just that the process is running.

        Returns:
            Always True if this method executes
        """
        return True

    def get_uptime(self) -> float:
        """Get service uptime in seconds.

        Returns:
            Uptime in seconds
        """
        return time.time() - self._start_time


# Built-in health check functions


async def check_database(db_pool) -> ComponentHealth:
    """Check database connectivity.

    Args:
        db_pool: asyncpg connection pool

    Returns:
        ComponentHealth with database status
    """
    start_time = time.time()
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        latency_ms = int((time.time() - start_time) * 1000)
        status = HealthStatus.PASS if latency_ms < 100 else HealthStatus.WARN

        return ComponentHealth(
            status=status,
            component_type="database",
            observed_value=latency_ms,
            observed_unit="ms",
            output=f"Connected, latency: {latency_ms}ms",
        )

    except Exception as e:
        return ComponentHealth(
            status=HealthStatus.FAIL,
            component_type="database",
            output=f"Connection failed: {str(e)}",
        )


async def check_redis(redis_client) -> ComponentHealth:
    """Check Redis connectivity.

    Args:
        redis_client: Redis client instance

    Returns:
        ComponentHealth with Redis status
    """
    start_time = time.time()
    try:
        await redis_client.ping()
        latency_ms = int((time.time() - start_time) * 1000)

        status = HealthStatus.PASS if latency_ms < 50 else HealthStatus.WARN

        return ComponentHealth(
            status=status,
            component_type="cache",
            observed_value=latency_ms,
            observed_unit="ms",
            output=f"Connected, latency: {latency_ms}ms",
        )

    except Exception as e:
        return ComponentHealth(
            status=HealthStatus.FAIL,
            component_type="cache",
            output=f"Connection failed: {str(e)}",
        )


async def check_queue_depth(
    redis_client,
    queue_name: str = "tiktok:videos",
    max_depth: int = 10000,
) -> ComponentHealth:
    """Check queue depth is within acceptable limits.

    Args:
        redis_client: Redis client instance
        queue_name: Name of the queue to check
        max_depth: Maximum acceptable queue depth

    Returns:
        ComponentHealth with queue status
    """
    try:
        depth = await redis_client.llen(queue_name)
        utilization = (depth / max_depth) * 100

        if utilization < 70:
            status = HealthStatus.PASS
        elif utilization < 90:
            status = HealthStatus.WARN
        else:
            status = HealthStatus.FAIL

        return ComponentHealth(
            status=status,
            component_type="queue",
            observed_value=depth,
            observed_unit="items",
            output=f"Queue depth: {depth}/{max_depth} ({utilization:.1f}%)",
        )

    except Exception as e:
        return ComponentHealth(
            status=HealthStatus.FAIL,
            component_type="queue",
            output=f"Queue check failed: {str(e)}",
        )


async def check_circuit_breaker(circuit_breaker) -> ComponentHealth:
    """Check circuit breaker state.

    Args:
        circuit_breaker: CircuitBreaker instance

    Returns:
        ComponentHealth with circuit breaker status
    """
    try:
        state = circuit_breaker.get_state()
        cb_state = state.get("state", "unknown")
        failure_count = state.get("failure_count", 0)

        if cb_state == "closed":
            status = HealthStatus.PASS
        elif cb_state == "half_open":
            status = HealthStatus.WARN
        else:  # open
            status = HealthStatus.WARN

        return ComponentHealth(
            status=status,
            component_type="circuit_breaker",
            observed_value=cb_state,
            output=f"State: {cb_state}, Failures: {failure_count}",
        )

    except Exception as e:
        return ComponentHealth(
            status=HealthStatus.FAIL,
            component_type="circuit_breaker",
            output=f"Check failed: {str(e)}",
        )


async def check_scraper_status(
    last_scrape_time: Optional[datetime],
    max_age_seconds: int = 600,
) -> ComponentHealth:
    """Check scraper status based on last scrape time.

    Args:
        last_scrape_time: When the last scrape completed
        max_age_seconds: Maximum acceptable age since last scrape

    Returns:
        ComponentHealth with scraper status
    """
    if last_scrape_time is None:
        return ComponentHealth(
            status=HealthStatus.WARN,
            component_type="scraper",
            output="No scrapes completed yet",
        )

    seconds_since = (datetime.utcnow() - last_scrape_time).total_seconds()

    if seconds_since <= max_age_seconds:
        status = HealthStatus.PASS
    elif seconds_since <= max_age_seconds * 2:
        status = HealthStatus.WARN
    else:
        status = HealthStatus.FAIL

    return ComponentHealth(
        status=status,
        component_type="scraper",
        observed_value=int(seconds_since),
        observed_unit="seconds",
        output=f"Last scrape: {int(seconds_since)}s ago",
    )


# Singleton instance
_health_aggregator: Optional[HealthAggregator] = None


def get_health_aggregator(
    service_name: Optional[str] = None,
    version: Optional[str] = None,
) -> HealthAggregator:
    """Get the global HealthAggregator instance.

    Args:
        service_name: Service name (required on first call)
        version: Service version (required on first call)

    Returns:
        HealthAggregator instance

    Raises:
        ValueError: If not initialized and no service_name provided
    """
    global _health_aggregator
    if _health_aggregator is None:
        if service_name is None:
            raise ValueError("service_name required for first initialization")
        _health_aggregator = HealthAggregator(
            service_name=service_name,
            version=version or "1.0.0",
        )
    return _health_aggregator
