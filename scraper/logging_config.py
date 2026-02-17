"""
Structured Logging Configuration

Provides JSON structured logging using structlog for observability.
Supports both JSON format (production) and human-readable format (development).

Features:
- JSON output for production log aggregation
- Colored output for development
- Correlation IDs for request tracing
- Context variables for structured metadata
"""

import logging
import sys
from typing import Optional

import structlog
from structlog.types import Processor


def configure_logging(
    log_level: str = "INFO",
    log_format: str = "json",
) -> None:
    """Configure structured logging for the scraper service.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Output format ('json' or 'text')
    """
    # Common processors for all formats
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "json":
        # JSON format for production
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Human-readable format for development
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured structlog logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog BoundLogger
    """
    return structlog.get_logger(name)


class CorrelationIdMiddleware:
    """Middleware for adding correlation IDs to requests.

    This can be used with FastAPI or other web frameworks
    to trace requests through the system.
    """

    def __init__(self, app, header_name: str = "X-Correlation-ID"):
        self.app = app
        self.header_name = header_name

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Get or generate correlation ID
        headers = dict(scope.get("headers", []))
        correlation_id = headers.get(self.header_name.lower().encode())

        if correlation_id:
            correlation_id = correlation_id.decode()
        else:
            import uuid
            correlation_id = str(uuid.uuid4())

        # Bind to context
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        # Add to response headers
        async def send_with_header(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append(
                    (self.header_name.encode(), correlation_id.encode())
                )
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_header)
        finally:
            structlog.contextvars.unbind_contextvars("correlation_id")
