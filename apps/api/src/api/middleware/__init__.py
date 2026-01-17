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

__all__ = [
    "AuthenticatedUser",
    "CurrentUser",
    "OptionalUser",
    "LoggingMiddleware",
    "get_current_user",
    "get_optional_user",
    "require_role",
]
