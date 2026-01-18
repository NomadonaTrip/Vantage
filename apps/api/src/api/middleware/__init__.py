"""Middleware modules for Vantage API."""

from src.api.middleware.auth import (
    AuthenticatedUser,
    CurrentUser,
    OptionalUser,
    get_current_user,
    get_optional_user,
    require_role,
)
from src.api.middleware.logging import LoggingMiddleware
from src.api.middleware.rate_limit import RateLimiter, rate_limit_voice, voice_rate_limiter

__all__ = [
    "AuthenticatedUser",
    "CurrentUser",
    "OptionalUser",
    "LoggingMiddleware",
    "get_current_user",
    "get_optional_user",
    "require_role",
    "RateLimiter",
    "rate_limit_voice",
    "voice_rate_limiter",
]
