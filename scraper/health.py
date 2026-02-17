"""
Health Check Service

Provides health monitoring endpoints for the scraper service.
Supports Kubernetes liveness and readiness probes.

Endpoints:
- GET /health - Full health check with component status
- GET /ready - Readiness probe (returns 503 if not ready)
- GET /live - Liveness probe (always returns 200 if process running)

Health Status Levels:
- healthy: All components passing
- degraded: Some components degraded but service functional
- unhealthy: Critical components failing
"""

import asyncio
import time
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
import redis.asyncio as redis

from .config import settings
from .models import ScraperHealth, HealthStatus, CheckStatus, ComponentCheck
from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

# FastAPI app for health endpoints
app = FastAPI(
    title="Trendscope Scraper Health",
    description="Health check endpoints for scraper service",
    version="1.0.0",
)


class HealthChecker:
    """Scraper health monitoring service.

    Aggregates health status from multiple components:
    - Redis connectivity
    - Circuit breaker state
    - Last successful scrape time
    - Error rates

    Attributes:
        redis_client: Redis connection to check
        circuit_breaker: Circuit breaker to monitor
        last_scrape_time: Timestamp of last successful scrape
        total_videos_scraped: Total videos scraped since startup
        total_errors: Total errors since startup
        startup_time: When the health checker was initialized
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        circuit_breaker: CircuitBreaker,
    ):
        """Initialize health checker.

        Args:
            redis_client: Redis connection for health checks
            circuit_breaker: Circuit breaker to monitor
        """
        self.redis = redis_client
        self.circuit_breaker = circuit_breaker
        self.last_scrape_time: Optional[datetime] = None
        self.total_videos_scraped = 0
        self.total_errors = 0
        self.startup_time = datetime.utcnow()
        self._is_ready = False  # Set to True after initial scrape

    def update_scrape_metrics(
        self,
        videos_scraped: int = 0,
        errors: int = 0,
        last_scrape: Optional[datetime] = None,
    ) -> None:
        """Update scraper metrics.

        Args:
            videos_scraped: Videos scraped in last cycle
            errors: Errors in last cycle
            last_scrape: Timestamp of last scrape
        """
        self.total_videos_scraped += videos_scraped
        self.total_errors += errors
        if last_scrape:
            self.last_scrape_time = last_scrape
            self._is_ready = True  # At least one scrape completed

    def mark_ready(self) -> None:
        """Mark the service as ready."""
        self._is_ready = True

    def mark_not_ready(self) -> None:
        """Mark the service as not ready."""
        self._is_ready = False

    async def check(self) -> ScraperHealth:
        """Perform health check and return status.

        Returns:
            ScraperHealth with component check results
        """
        checks: dict[str, ComponentCheck] = {}
        start_time = time.time()

        # Check Redis connectivity
        redis_check = await self._check_redis()
        checks["redis"] = redis_check

        # Check circuit breaker state
        cb_check = self._check_circuit_breaker()
        checks["circuit_breaker"] = cb_check

        # Check scraper status
        scraper_check = self._check_scraper()
        checks["scraper"] = scraper_check

        # Determine overall status
        overall_status = self._determine_overall_status(checks)

        # Calculate uptime
        uptime = (datetime.utcnow() - self.startup_time).total_seconds()

        return ScraperHealth(
            status=overall_status,
            version="1.0.0",
            timestamp=datetime.utcnow(),
            checks=checks,
            metrics={
                "videos_scraped": self.total_videos_scraped,
                "errors": self.total_errors,
                "uptime_seconds": uptime,
                "check_duration_ms": int((time.time() - start_time) * 1000),
            }
        )

    async def _check_redis(self) -> ComponentCheck:
        """Check Redis connectivity and latency.

        Returns:
            ComponentCheck with Redis status
        """
        try:
            start = time.time()
            await self.redis.ping()
            latency_ms = int((time.time() - start) * 1000)

            # Consider degraded if latency > 100ms
            status = CheckStatus.PASS if latency_ms < 100 else CheckStatus.WARN

            return ComponentCheck(
                status=status,
                latency_ms=latency_ms,
            )

        except redis.RedisError as e:
            logger.error("redis_health_check_failed", extra={"error": str(e)})
            return ComponentCheck(
                status=CheckStatus.FAIL,
                error=str(e),
            )
        except Exception as e:
            logger.error("redis_health_check_error", extra={"error": str(e)})
            return ComponentCheck(
                status=CheckStatus.FAIL,
                error=f"Unexpected error: {e}",
            )

    def _check_circuit_breaker(self) -> ComponentCheck:
        """Check circuit breaker state.

        Returns:
            ComponentCheck with circuit breaker status
        """
        cb_state = self.circuit_breaker.get_state()

        if cb_state["state"] == "closed":
            status = CheckStatus.PASS
        elif cb_state["state"] == "half_open":
            status = CheckStatus.WARN
        else:  # open
            status = CheckStatus.WARN

        return ComponentCheck(
            status=status,
            state=cb_state["state"],
            failure_count=cb_state["failure_count"],
        )

    def _check_scraper(self) -> ComponentCheck:
        """Check scraper status based on last scrape time.

        Returns:
            ComponentCheck with scraper status
        """
        if self.last_scrape_time is None:
            return ComponentCheck(
                status=CheckStatus.WARN,
                last_scrape=None,
                videos_scraped=0,
                error="No scrapes completed yet",
            )

        # Check if last scrape was recent (within 2x interval)
        seconds_since_scrape = (
            datetime.utcnow() - self.last_scrape_time
        ).total_seconds()
        max_age = settings.scrape_interval * 2

        if seconds_since_scrape <= max_age:
            status = CheckStatus.PASS
        elif seconds_since_scrape <= max_age * 2:
            status = CheckStatus.WARN
        else:
            status = CheckStatus.FAIL

        return ComponentCheck(
            status=status,
            last_scrape=self.last_scrape_time.isoformat(),
            videos_scraped=self.total_videos_scraped,
        )

    def _determine_overall_status(
        self,
        checks: dict[str, ComponentCheck]
    ) -> HealthStatus:
        """Determine overall health status from component checks.

        Args:
            checks: Dictionary of component checks

        Returns:
            Overall HealthStatus
        """
        # If any critical component fails, unhealthy
        if any(c.status == CheckStatus.FAIL for c in checks.values()):
            return HealthStatus.UNHEALTHY

        # If any component is degraded, degraded
        if any(c.status == CheckStatus.WARN for c in checks.values()):
            return HealthStatus.DEGRADED

        # All passing
        return HealthStatus.HEALTHY

    def is_ready(self) -> bool:
        """Check if service is ready to receive traffic.

        Returns:
            True if ready
        """
        return self._is_ready and not self.circuit_breaker.is_open()

    def get_metrics(self) -> dict:
        """Get current metrics for Prometheus scraping.

        Returns:
            Dictionary of metrics
        """
        return {
            "scraper_videos_scraped_total": self.total_videos_scraped,
            "scraper_errors_total": self.total_errors,
            "scraper_circuit_breaker_state": (
                0 if self.circuit_breaker.is_closed()
                else 1 if self.circuit_breaker.is_half_open()
                else 2
            ),
            "scraper_ready": 1 if self.is_ready() else 0,
            "scraper_uptime_seconds": (
                datetime.utcnow() - self.startup_time
            ).total_seconds(),
        }


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get or raise error if health checker not initialized."""
    if _health_checker is None:
        raise RuntimeError("Health checker not initialized")
    return _health_checker


def init_health_checker(
    redis_client: redis.Redis,
    circuit_breaker: CircuitBreaker,
) -> HealthChecker:
    """Initialize global health checker instance."""
    global _health_checker
    _health_checker = HealthChecker(redis_client, circuit_breaker)
    return _health_checker


# FastAPI route handlers
@app.get("/health", response_model=None)
async def health_endpoint() -> Response:
    """Full health check endpoint.

    Returns detailed health status including all component checks.
    Returns 503 if unhealthy, 200 otherwise.
    """
    try:
        checker = get_health_checker()
        health = await checker.check()

        status_code = 200 if health.status != HealthStatus.UNHEALTHY else 503

        return JSONResponse(
            content=health.model_dump(mode="json"),
            status_code=status_code,
        )
    except Exception as e:
        logger.error("health_check_error", extra={"error": str(e)})
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
            status_code=503,
        )


@app.get("/ready")
async def readiness_endpoint() -> Response:
    """Readiness probe for Kubernetes.

    Returns 200 if service is ready to receive traffic, 503 otherwise.
    """
    try:
        checker = get_health_checker()

        if checker.is_ready():
            return JSONResponse(
                content={"ready": True},
                status_code=200,
            )
        else:
            return JSONResponse(
                content={"ready": False},
                status_code=503,
            )
    except Exception as e:
        return JSONResponse(
            content={"ready": False, "error": str(e)},
            status_code=503,
        )


@app.get("/live")
async def liveness_endpoint() -> dict:
    """Liveness probe for Kubernetes.

    Returns 200 if the process is running.
    This should always succeed unless the process is deadlocked.
    """
    return {"alive": True}


@app.get("/metrics")
async def metrics_endpoint() -> Response:
    """Prometheus metrics endpoint.

    Returns metrics in Prometheus text format.
    """
    try:
        checker = get_health_checker()
        metrics = checker.get_metrics()

        # Convert to Prometheus format
        lines = []
        for name, value in metrics.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")

        return Response(
            content="\n".join(lines) + "\n",
            media_type="text/plain",
        )
    except Exception as e:
        return Response(
            content=f"# Error collecting metrics: {e}\n",
            media_type="text/plain",
            status_code=500,
        )


async def run_health_server(port: Optional[int] = None) -> None:
    """Run health check HTTP server.

    Args:
        port: Port to listen on (default from settings)
    """
    import uvicorn

    port = port or settings.health_port

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="warning",  # Reduce noise
        access_log=False,
    )
    server = uvicorn.Server(config)

    logger.info("health_server_starting", extra={"port": port})

    await server.serve()
