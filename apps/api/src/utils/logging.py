"""
Structured logging configuration using structlog.

Provides JSON logging for production and colored console output for development.
"""

import logging
import os
import sys
from typing import Any

import structlog
from structlog.types import Processor


def setup_logging(log_level: str | None = None) -> None:
    """
    Configure structlog for the application.

    Args:
        log_level: Log level (debug, info, warning, error). Defaults to LOG_LEVEL env var.
    """
    level = (log_level or os.getenv("LOG_LEVEL", "info")).upper()
    numeric_level = getattr(logging, level, logging.INFO)

    # Determine if running in production (JSON) or development (console)
    is_production = os.getenv("ENVIRONMENT", "development") == "production"

    # Shared processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if is_production:
        # Production: JSON output
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Colored console output
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    # Set log levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name. Defaults to caller's module name.

    Returns:
        Configured structlog logger.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("search_completed", search_id="abc123", lead_count=42)
    """
    return structlog.get_logger(name)


def bind_contextvars(**kwargs: Any) -> None:
    """
    Bind context variables that will be included in all subsequent log entries.

    Useful for adding request-scoped context like user_id, request_id.

    Args:
        **kwargs: Key-value pairs to bind to the logging context.

    Example:
        >>> bind_contextvars(request_id="req-123", user_id="user-456")
        >>> logger.info("processing")  # Will include request_id and user_id
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_contextvars() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()
