"""
Trend Detection Engine - Main Entry Point

Starts the trend detection consumer service.
Connects to Redis (for video queue) and PostgreSQL (for trend persistence).

Usage:
    python -m detection
    python -m detection.main

Environment Variables:
    REDIS_URL: Redis connection URL
    DATABASE_URL: PostgreSQL connection URL
    LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
    LOG_FORMAT: Log format (json, text)
"""

import asyncio
import signal
import sys
from typing import Optional

import redis.asyncio as redis
import asyncpg

from detection.config import settings
from detection.consumer import TrendConsumer, create_consumer
from detection.logging_config import configure_logging, get_logger

logger = get_logger(__name__)


class DetectionService:
    """
    Main detection service that manages the consumer lifecycle.

    Handles:
    - Service initialization
    - Graceful shutdown on signals
    - Health monitoring
    - Metrics reporting
    """

    def __init__(self):
        """Initialize detection service."""
        self.consumer: Optional[TrendConsumer] = None
        self.running = False
        self.start_time: Optional[float] = None

    async def start(self) -> None:
        """
        Start the detection service.

        Initializes connections and starts the consumer loop.
        """
        self.start_time = asyncio.get_event_loop().time()
        self.running = True

        logger.info(
            "detection_service_starting",
            environment=settings.app_env,
            batch_size=settings.consumer_batch_size,
            velocity_threshold=settings.trend_min_velocity_score,
            r_squared_threshold=settings.velocity_r_squared_threshold
        )

        try:
            # Create and start consumer
            self.consumer = await create_consumer()
            await self.consumer.consume()

        except Exception as e:
            logger.error(
                "detection_service_error",
                error=str(e),
                exc_info=True
            )
            raise

        finally:
            await self.stop()

    async def stop(self) -> None:
        """
        Stop the detection service gracefully.

        Stops the consumer and cleans up connections.
        """
        if not self.running:
            return

        self.running = False
        logger.info("detection_service_stopping")

        if self.consumer:
            await self.consumer.stop()

            # Log final metrics
            metrics = self.consumer.get_metrics()
            uptime = asyncio.get_event_loop().time() - self.start_time if self.start_time else 0

            logger.info(
                "detection_service_stopped",
                videos_processed=metrics["videos_processed"],
                trends_detected=metrics["trends_detected"],
                errors_count=metrics["errors_count"],
                uptime_seconds=round(uptime, 2)
            )

    def setup_signal_handlers(self) -> None:
        """
        Set up signal handlers for graceful shutdown.

        Handles SIGINT (Ctrl+C) and SIGTERM.
        """
        loop = asyncio.get_event_loop()

        def signal_handler(sig, frame):
            logger.info("shutdown_signal_received", signal=sig)
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def run_health_check_server(port: int = 8081) -> None:
    """
    Run a simple health check HTTP server.

    Provides a /health endpoint for monitoring.

    Args:
        port: Port to listen on
    """
    from aiohttp import web

    async def health_handler(request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({
            "status": "healthy",
            "service": "trend-detection",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        })

    app = web.Application()
    app.router.add_get('/health', health_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)

    await site.start()
    logger.info("health_check_server_started", port=port)

    # Keep running forever
    while True:
        await asyncio.sleep(3600)


async def main() -> None:
    """
    Main entry point for the detection service.

    Initializes logging, creates the service, and runs it.
    """
    # Configure logging
    configure_logging(
        log_level=settings.log_level,
        log_format=settings.log_format
    )

    logger.info(
        "detection_engine_initializing",
        log_level=settings.log_level,
        environment=settings.app_env
    )

    # Validate configuration
    if not settings.validate_saturation_weights():
        logger.warning(
            "saturation_weights_invalid",
            weights={
                "acceleration": settings.saturation_weight_acceleration,
                "time": settings.saturation_weight_time,
                "velocity": settings.saturation_weight_velocity,
                "volume": settings.saturation_weight_volume
            }
        )

    # Create and run service
    service = DetectionService()
    service.setup_signal_handlers()

    # Optionally start health check server
    if settings.app_env == "production":
        # Run health server in background
        health_task = asyncio.create_task(run_health_check_server())

    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt_received")
    except Exception as e:
        logger.error("service_failed", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
