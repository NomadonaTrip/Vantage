"""Health check endpoints for monitoring and container orchestration."""

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Comprehensive health check for monitoring.

    Returns:
        Health status with timestamp.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    """
    Simple liveness probe for k8s/docker.

    Returns:
        Alive status.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness() -> dict[str, str]:
    """
    Readiness probe - can we serve traffic?

    Returns:
        Ready status.
    """
    return {"status": "ready"}
