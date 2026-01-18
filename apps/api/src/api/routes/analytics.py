"""Analytics routes."""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from src.api.middleware.auth import CurrentUser
from src.core.supabase import get_supabase_client
from src.repositories.client_profile import ClientProfileRepository
from src.schemas.analytics import (
    AnalyticsQueryParams,
    ProfileAnalyticsResponse,
    TimeGranularity,
    UserAnalyticsResponse,
)
from src.schemas.lead import LeadSource
from src.services.analytics import AnalyticsService
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_service(
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> AnalyticsService:
    """Get analytics service instance."""
    return AnalyticsService(supabase)


def get_profile_repository(
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> ClientProfileRepository:
    """Get client profile repository instance."""
    return ClientProfileRepository(supabase)


@router.get("/profile", response_model=ProfileAnalyticsResponse)
async def get_profile_analytics(
    user: CurrentUser,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    profile_repo: Annotated[ClientProfileRepository, Depends(get_profile_repository)],
    start_date: date | None = Query(default=None, description="Start date (ISO format)"),
    end_date: date | None = Query(default=None, description="End date (ISO format)"),
    include_time_series: bool = Query(default=False, description="Include time series data"),
    granularity: TimeGranularity = Query(
        default=TimeGranularity.WEEKLY, description="Time series granularity"
    ),
    sources: list[LeadSource] | None = Query(default=None, description="Filter by sources"),
) -> ProfileAnalyticsResponse:
    """
    Get analytics for the user's active client profile.

    Returns metrics including:
    - Lead outcome distribution (status, accuracy)
    - Per-source breakdown
    - Intent score correlations
    - Search metrics
    - Optional time series data

    Query Parameters:
    - start_date: Start of analysis period (default: 30 days ago)
    - end_date: End of analysis period (default: today)
    - include_time_series: Include time-based trends
    - granularity: daily, weekly, or monthly aggregation
    - sources: Filter to specific lead sources
    """
    logger.info("get_profile_analytics_request", user_id=user.id)

    try:
        # Get active profile
        active_profile = await profile_repo.get_active(user.id)
        if not active_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active client profile. Please select a profile first.",
            )

        # Build query params
        params = AnalyticsQueryParams(
            start_date=start_date,
            end_date=end_date,
            include_time_series=include_time_series,
            time_granularity=granularity,
            sources=sources,
        )

        # Compute analytics
        analytics = await analytics_service.get_profile_analytics(
            profile_id=active_profile.id,
            params=params,
        )

        logger.info(
            "profile_analytics_computed",
            user_id=user.id,
            profile_id=active_profile.id,
            total_leads=analytics.outcome_metrics.total_leads,
        )

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_profile_analytics_failed", user_id=user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute profile analytics",
        ) from e


@router.get("/user", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    user: CurrentUser,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    start_date: date | None = Query(default=None, description="Start date (ISO format)"),
    end_date: date | None = Query(default=None, description="End date (ISO format)"),
    sources: list[LeadSource] | None = Query(default=None, description="Filter by sources"),
) -> UserAnalyticsResponse:
    """
    Get aggregated analytics across all user's client profiles.

    Returns:
    - Aggregated lead metrics across all profiles
    - Aggregated search metrics
    - Per-source breakdown
    - Summary for each profile

    Query Parameters:
    - start_date: Start of analysis period (default: 30 days ago)
    - end_date: End of analysis period (default: today)
    - sources: Filter to specific lead sources
    """
    logger.info("get_user_analytics_request", user_id=user.id)

    try:
        # Build query params
        params = AnalyticsQueryParams(
            start_date=start_date,
            end_date=end_date,
            sources=sources,
        )

        # Compute analytics
        analytics = await analytics_service.get_user_analytics(
            user_id=user.id,
            params=params,
        )

        logger.info(
            "user_analytics_computed",
            user_id=user.id,
            profile_count=analytics.profile_count,
            total_leads=analytics.outcome_metrics.total_leads,
        )

        return analytics

    except Exception as e:
        logger.exception("get_user_analytics_failed", user_id=user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute user analytics",
        ) from e


@router.get("/profile/{profile_id}", response_model=ProfileAnalyticsResponse)
async def get_specific_profile_analytics(
    profile_id: str,
    user: CurrentUser,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    profile_repo: Annotated[ClientProfileRepository, Depends(get_profile_repository)],
    start_date: date | None = Query(default=None, description="Start date (ISO format)"),
    end_date: date | None = Query(default=None, description="End date (ISO format)"),
    include_time_series: bool = Query(default=False, description="Include time series data"),
    granularity: TimeGranularity = Query(
        default=TimeGranularity.WEEKLY, description="Time series granularity"
    ),
    sources: list[LeadSource] | None = Query(default=None, description="Filter by sources"),
) -> ProfileAnalyticsResponse:
    """
    Get analytics for a specific client profile.

    Requires ownership of the profile.
    """
    logger.info(
        "get_specific_profile_analytics_request",
        user_id=user.id,
        profile_id=profile_id,
    )

    try:
        # Verify ownership
        profile = await profile_repo.get_by_id(profile_id, user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        # Build query params
        params = AnalyticsQueryParams(
            start_date=start_date,
            end_date=end_date,
            include_time_series=include_time_series,
            time_granularity=granularity,
            sources=sources,
        )

        # Compute analytics
        analytics = await analytics_service.get_profile_analytics(
            profile_id=profile_id,
            params=params,
        )

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "get_specific_profile_analytics_failed",
            profile_id=profile_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute profile analytics",
        ) from e
