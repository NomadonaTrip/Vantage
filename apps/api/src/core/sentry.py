"""
Sentry error tracking configuration for FastAPI.

Initializes Sentry with integrations for FastAPI, Celery, SQLAlchemy, and httpx.
"""

import os
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration


def _scrub_sensitive_data(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """
    Remove sensitive data from Sentry events before sending.

    Args:
        event: The Sentry event dictionary.
        hint: Additional context about the event.

    Returns:
        The scrubbed event or None to drop the event.
    """
    # Filter authorization headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        sensitive_keys = ["authorization", "cookie", "x-api-key", "x-auth-token"]
        for key in sensitive_keys:
            if key in headers:
                headers[key] = "[FILTERED]"

    # Filter sensitive data from request body
    if "request" in event and "data" in event["request"]:
        data = event["request"]["data"]
        if isinstance(data, dict):
            sensitive_fields = ["password", "token", "secret", "api_key", "credit_card"]
            for field in sensitive_fields:
                if field in data:
                    data[field] = "[FILTERED]"

    return event


def init_sentry() -> None:
    """
    Initialize Sentry error tracking.

    Reads configuration from environment variables:
    - SENTRY_DSN: The Sentry DSN for the project
    - ENVIRONMENT: The environment name (development, staging, production)
    """
    dsn = os.getenv("SENTRY_DSN")

    if not dsn:
        return  # Skip initialization if no DSN configured

    environment = os.getenv("ENVIRONMENT", "development")
    traces_sample_rate = 0.1 if environment == "production" else 1.0

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            CeleryIntegration(),
            HttpxIntegration(),
            LoggingIntegration(level=None, event_level=None),
        ],
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=traces_sample_rate,
        send_default_pii=False,
        before_send=_scrub_sensitive_data,
    )
