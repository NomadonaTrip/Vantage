"""
Vantage API - FastAPI Application Entry Point.

This module initializes the FastAPI application with all middleware,
routes, and integrations configured.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.logging import LoggingMiddleware
from src.api.routes import health
from src.core.sentry import init_sentry
from src.utils.logging import get_logger, setup_logging

# Initialize logging first
setup_logging()
logger = get_logger(__name__)

# Initialize Sentry error tracking
init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    logger.info("application_starting", version="0.1.0")
    yield
    logger.info("application_stopping")


# Create FastAPI application
app = FastAPI(
    title="Vantage API",
    description="Intelligent Lead Generation Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(health.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning API information."""
    return {
        "name": "Vantage API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/debug-sentry")
async def debug_sentry() -> dict[str, str]:
    """
    Test endpoint to verify Sentry integration.

    Raises:
        ZeroDivisionError: Always raised to test Sentry error capture.
    """
    logger.info("debug_sentry_triggered")
    division_by_zero = 1 / 0  # noqa: F841
    return {"message": "This should not be reached"}
