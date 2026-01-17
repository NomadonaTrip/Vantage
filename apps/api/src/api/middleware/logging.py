"""
Request/response logging middleware for FastAPI.

Logs HTTP requests with method, path, status code, and duration.
"""

import time
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.utils.logging import bind_contextvars, clear_contextvars, get_logger

logger = get_logger(__name__)

# Headers that should not be logged
SENSITIVE_HEADERS = frozenset({
    "authorization",
    "cookie",
    "x-api-key",
    "x-auth-token",
    "x-csrf-token",
    "set-cookie",
})

# Paths that should have minimal logging (health checks, etc.)
QUIET_PATHS = frozenset({
    "/health",
    "/health/live",
    "/health/ready",
    "/favicon.ico",
})


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs request/response information."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the logging middleware."""
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        """Process request and log metrics."""
        # Generate request ID for correlation
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())

        # Bind request context for all logs in this request
        bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        # Skip detailed logging for quiet paths
        is_quiet = request.url.path in QUIET_PATHS

        start_time = time.perf_counter()

        try:
            # Log incoming request (skip for quiet paths)
            if not is_quiet:
                logger.info(
                    "request_started",
                    query_string=str(request.query_params) if request.query_params else None,
                    client_host=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )

            # Process the request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Add request ID to response headers
            response.headers["x-request-id"] = request_id

            # Log completed request
            log_func = logger.info if response.status_code < 400 else logger.warning
            if not is_quiet or response.status_code >= 400:
                log_func(
                    "request_completed",
                    status_code=response.status_code,
                    duration_ms=round(duration_ms, 2),
                )

            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "request_failed",
                duration_ms=round(duration_ms, 2),
                error=str(exc),
            )
            raise

        finally:
            clear_contextvars()


def get_safe_headers(request: Request) -> dict[str, str]:
    """
    Get request headers with sensitive values filtered.

    Args:
        request: The FastAPI request object.

    Returns:
        Dictionary of header names to values with sensitive headers filtered.
    """
    return {
        key: "[FILTERED]" if key.lower() in SENSITIVE_HEADERS else value
        for key, value in request.headers.items()
    }
