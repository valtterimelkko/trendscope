"""
Structured Logging Configuration

Provides JSON-formatted logs with:
- Correlation IDs for distributed tracing
- Service identification
- Structured context data
- Log level filtering

Usage:
    from monitoring.logging_config import configure_logging, get_logger

    # Initialize at service startup
    configure_logging(
        service_name="trendscope-api",
        log_level="INFO",
        json_output=True
    )

    # Get a logger
    logger = get_logger(__name__)

    # Log with structured context
    logger.info("request_completed", method="GET", endpoint="/api/v1/trends", duration_ms=45)
"""

import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Optional, Dict
import uuid

import structlog
from structlog.types import Processor


# Context variable for correlation ID (trace ID)
correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

# Context variable for request metadata
request_context: ContextVar[Dict[str, Any]] = ContextVar(
    "request_context", default={}
)


def get_correlation_id() -> str:
    """Get or create correlation ID for current context.

    Returns:
        8-character correlation ID
    """
    existing = correlation_id.get()
    if existing is None:
        existing = str(uuid.uuid4())[:8]
        correlation_id.set(existing)
    return existing


def set_correlation_id(trace_id: str) -> None:
    """Set correlation ID for current context.

    Args:
        trace_id: The correlation/trace ID to set
    """
    correlation_id.set(trace_id)


def clear_correlation_id() -> None:
    """Clear the correlation ID from context."""
    correlation_id.set(None)


def bind_request_context(**kwargs: Any) -> None:
    """Bind additional context to all subsequent log entries.

    Args:
        **kwargs: Key-value pairs to add to context
    """
    current = request_context.get().copy()
    current.update(kwargs)
    request_context.set(current)


def unbind_request_context(*keys: str) -> None:
    """Remove keys from request context.

    Args:
        *keys: Keys to remove
    """
    current = request_context.get().copy()
    for key in keys:
        current.pop(key, None)
    request_context.set(current)


def clear_request_context() -> None:
    """Clear all request context."""
    request_context.set({})


class LogContext:
    """Context manager for adding temporary context to logs.

    Usage:
        with LogContext(user_id="123", request_id="abc"):
            logger.info("processing_request")  # Will include user_id and request_id
    """

    def __init__(self, **kwargs: Any):
        """Initialize with context key-value pairs.

        Args:
            **kwargs: Context to add within the scope
        """
        self.context = kwargs
        self._token: Optional[Any] = None

    def __enter__(self) -> "LogContext":
        """Enter context and bind variables."""
        structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context and unbind variables."""
        structlog.contextvars.unbind_contextvars(*self.context.keys())


# Structlog processors


def add_correlation_id(
    logger: logging.Logger,
    method_name: str,
    event_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """Processor to add correlation ID to log entries.

    Args:
        logger: The wrapped logger
        method_name: The name of the log method
        event_dict: The event dictionary

    Returns:
        Modified event dictionary with trace_id
    """
    event_dict["trace_id"] = get_correlation_id()
    return event_dict


def add_service_name(service_name: str) -> Processor:
    """Factory for processor that adds service name.

    Args:
        service_name: Name of the service

    Returns:
        A structlog processor
    """

    def processor(
        logger: logging.Logger,
        method_name: str,
        event_dict: Dict[str, Any],
    ) -> Dict[str, Any]:
        event_dict["service"] = service_name
        return event_dict

    return processor


def add_timestamp(
    logger: logging.Logger,
    method_name: str,
    event_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """Processor to add ISO8601 timestamp.

    Args:
        logger: The wrapped logger
        method_name: The name of the log method
        event_dict: The event dictionary

    Returns:
        Modified event dictionary with timestamp
    """
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return event_dict


def add_request_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """Processor to add request context to log entries.

    Args:
        logger: The wrapped logger
        method_name: The name of the log method
        event_dict: The event dictionary

    Returns:
        Modified event dictionary with request context
    """
    ctx = request_context.get()
    if ctx:
        event_dict.update(ctx)
    return event_dict


def drop_color_message_key(
    logger: logging.Logger,
    method_name: str,
    event_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """Remove color_message key added by uvicorn.

    Args:
        logger: The wrapped logger
        method_name: The name of the log method
        event_dict: The event dictionary

    Returns:
        Modified event dictionary without color_message
    """
    event_dict.pop("color_message", None)
    return event_dict


def rename_event_key(
    logger: logging.Logger,
    method_name: str,
    event_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """Rename 'event' key to 'message' for consistency.

    Args:
        logger: The wrapped logger
        method_name: The name of the log method
        event_dict: The event dictionary

    Returns:
        Modified event dictionary with renamed key
    """
    if "event" in event_dict:
        event_dict["message"] = event_dict.pop("event")
    return event_dict


def configure_logging(
    service_name: str,
    log_level: str = "INFO",
    json_output: bool = True,
) -> None:
    """Configure structured logging for a service.

    This should be called once at service startup.

    Args:
        service_name: Name of the service (e.g., "trendscope-api")
        log_level: Minimum log level to capture (DEBUG, INFO, WARNING, ERROR)
        json_output: If True, output JSON; if False, output human-readable
    """
    # Common processors for all logging
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_timestamp,
        add_correlation_id,
        add_request_context,
        add_service_name(service_name),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        drop_color_message_key,
    ]

    if json_output:
        # JSON output for production
        shared_processors.extend([
            structlog.processors.format_exc_info,
            rename_event_key,
            structlog.processors.JSONRenderer(),
        ])
    else:
        # Human-readable output for development
        shared_processors.append(
            structlog.dev.ConsoleRenderer(colors=True)
        )

    # Configure structlog
    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level)
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.getLevelName(log_level))

    # Set log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Get a configured structlog logger.

    Args:
        name: Logger name, typically __name__

    Returns:
        A structlog BoundLogger instance
    """
    return structlog.get_logger(name)


# Example log output:
# {
#   "timestamp": "2026-02-17T12:34:56.789Z",
#   "level": "INFO",
#   "message": "trend_detected",
#   "service": "detection",
#   "trace_id": "abc12345",
#   "trend_id": "uuid",
#   "trend_name": "Viral Sound",
#   "velocity_score": 89,
#   "niche": "beauty"
# }
