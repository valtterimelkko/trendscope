"""
Trendscope Scraper Service - Main Entry Point

Orchestrates the TikTok scraping pipeline:
1. Initializes Redis connection
2. Creates rate limiters and circuit breaker
3. Starts producer for continuous data collection
4. Runs health check server for monitoring
5. Handles graceful shutdown

Usage:
    python -m scraper.main

Environment Variables:
    See config.py for all configurable settings
    Critical: PROXY_URL must be set for production use
"""

import asyncio
import signal
import sys
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import redis.asyncio as redis

from scraper.config import settings
from scraper.producer import TikTokProducer
from scraper.circuit_breaker import get_circuit_breaker
from scraper.health import init_health_checker, run_health_server, get_health_checker
from scraper.logging_config import configure_logging, get_logger

# Configure logging early
configure_logging(settings.log_level, settings.log_format)
logger = get_logger(__name__)


class ScraperService:
    """Main scraper service orchestrator.

    Manages the lifecycle of the scraper service:
    - Redis connection
    - Producer instance
    - Health check server
    - Graceful shutdown

    Attributes:
        redis_client: Redis connection
        producer: TikTok producer instance
        running: Flag indicating if service is running
        shutdown_event: Event for graceful shutdown coordination
    """

    def __init__(self):
        """Initialize scraper service."""
        self.redis_client: Optional[redis.Redis] = None
        self.producer: Optional[TikTokProducer] = None
        self.running = False
        self.shutdown_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start the scraper service.

        This method:
        1. Connects to Redis
        2. Initializes health checker
        3. Creates producer
        4. Starts background tasks
        5. Registers signal handlers
        """
        logger.info(
            "scraper_service_starting",
            extra={
                "environment": settings.app_env,
                "redis_url": settings.redis_url.split("@")[-1] if "@" in settings.redis_url else settings.redis_url,
                "health_port": settings.health_port,
                "scrape_interval": settings.scrape_interval,
                "hashtags": settings.hashtag_list,
            }
        )

        try:
            # Connect to Redis
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=False,  # Keep bytes for JSON handling
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("redis_connected")

            # Initialize health checker
            circuit_breaker = get_circuit_breaker()
            init_health_checker(self.redis_client, circuit_breaker)
            logger.info("health_checker_initialized")

            # Create producer
            self.producer = TikTokProducer(
                redis_client=self.redis_client,
                proxy=settings.proxy_url,
            )
            logger.info(
                "producer_created",
                extra={"has_proxy": settings.proxy_url is not None}
            )

            # Mark service as running
            self.running = True

            # Register signal handlers
            self._register_signal_handlers()

            # Start background tasks
            await self._start_background_tasks()

            logger.info("scraper_service_started")

        except Exception as e:
            logger.error(
                "scraper_service_start_failed",
                extra={"error": str(e)},
                exc_info=True
            )
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the scraper service gracefully.

        This method:
        1. Sets shutdown event
        2. Cancels background tasks
        3. Closes Redis connection
        """
        if not self.running:
            return

        logger.info("scraper_service_stopping")
        self.running = False
        self.shutdown_event.set()

        # Cancel all background tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
            logger.info("redis_connection_closed")

        logger.info("scraper_service_stopped")

    def _register_signal_handlers(self) -> None:
        """Register handlers for graceful shutdown signals."""
        loop = asyncio.get_running_loop()

        def handle_signal(sig):
            logger.info(
                "shutdown_signal_received",
                extra={"signal": sig.name}
            )
            asyncio.create_task(self.stop())

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))

    async def _start_background_tasks(self) -> None:
        """Start background tasks for scraping and health checks."""
        # Health check server task
        health_task = asyncio.create_task(
            self._run_health_server(),
            name="health_server"
        )
        self._tasks.append(health_task)

        # Main scraper task
        scraper_task = asyncio.create_task(
            self._run_scraper(),
            name="scraper"
        )
        self._tasks.append(scraper_task)

        # Wait for shutdown
        await self.shutdown_event.wait()

    async def _run_health_server(self) -> None:
        """Run health check server."""
        try:
            await run_health_server()
        except asyncio.CancelledError:
            logger.info("health_server_cancelled")
        except Exception as e:
            logger.error(
                "health_server_error",
                extra={"error": str(e)},
                exc_info=True
            )

    async def _run_scraper(self) -> None:
        """Run main scraper loop."""
        try:
            # Wait a moment for health server to start
            await asyncio.sleep(1)

            # Mark as ready after first successful scrape
            health_checker = get_health_checker()

            # Run continuous scraping
            await self.producer.run_continuous(
                interval=settings.scrape_interval,
                hashtags=settings.hashtag_list,
            )

            # Mark ready after first cycle
            health_checker.mark_ready()

        except asyncio.CancelledError:
            logger.info("scraper_cancelled")
        except Exception as e:
            logger.error(
                "scraper_error",
                extra={"error": str(e)},
                exc_info=True
            )
            # Signal shutdown on unrecoverable error
            self.shutdown_event.set()

    async def run_forever(self) -> None:
        """Run the service until shutdown signal."""
        await self.start()
        await self.shutdown_event.wait()


async def main() -> None:
    """Main entry point for the scraper service."""
    service = ScraperService()

    try:
        await service.run_forever()
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt_received")
    except Exception as e:
        logger.error(
            "scraper_service_error",
            extra={"error": str(e)},
            exc_info=True
        )
        sys.exit(1)
    finally:
        await service.stop()


def run() -> None:
    """Synchronous entry point for poetry script."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
