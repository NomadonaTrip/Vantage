"""Search routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from src.api.middleware.auth import CurrentUser
from src.core.supabase import get_supabase_client
from src.repositories.client_profile import ClientProfileRepository
from src.repositories.search import SearchRepository
from src.schemas.search import (
    Search,
    SearchCreate,
    SearchListResponse,
    SearchResponse,
    SearchStatus,
    SearchType,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/searches", tags=["Searches"])


def get_search_repository(
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> SearchRepository:
    """Get search repository instance."""
    return SearchRepository(supabase)


def get_profile_repository(
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> ClientProfileRepository:
    """Get client profile repository instance."""
    return ClientProfileRepository(supabase)


def _to_response(search: Search) -> SearchResponse:
    """Convert Search model to SearchResponse."""
    return SearchResponse(
        id=search.id,
        client_profile_id=search.client_profile_id,
        search_type=search.search_type,
        manual_params=search.manual_params,
        quality_setting=search.quality_setting,
        status=search.status,
        sources_queried=search.sources_queried,
        sources_successful=search.sources_successful,
        sources_failed=search.sources_failed,
        lead_count=search.lead_count,
        started_at=search.started_at,
        completed_at=search.completed_at,
        error_message=search.error_message,
    )


@router.get("", response_model=SearchListResponse)
async def list_searches(
    user: CurrentUser,
    search_repo: Annotated[SearchRepository, Depends(get_search_repository)],
    profile_repo: Annotated[ClientProfileRepository, Depends(get_profile_repository)],
    status_filter: SearchStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
) -> SearchListResponse:
    """
    List searches for the user's active client profile.

    Returns recent searches ordered by start time descending.
    """
    logger.info("list_searches_request", user_id=user.id)

    try:
        # Get active profile
        active_profile = await profile_repo.get_active(user.id)
        if not active_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active client profile. Please select a profile first.",
            )

        searches = await search_repo.list_by_profile(
            client_profile_id=active_profile.id,
            status=status_filter,
            limit=limit,
        )

        return SearchListResponse(
            searches=[_to_response(s) for s in searches],
            total=len(searches),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("list_searches_failed", user_id=user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list searches",
        ) from e


@router.post("", response_model=SearchResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_search(
    user: CurrentUser,
    search_repo: Annotated[SearchRepository, Depends(get_search_repository)],
    profile_repo: Annotated[ClientProfileRepository, Depends(get_profile_repository)],
    search_type: SearchType = SearchType.AUTONOMOUS,
    quality_setting: float = Query(default=0.7, ge=0, le=1),
) -> SearchResponse:
    """
    Create a new search for the active client profile.

    Returns 202 Accepted as search execution happens asynchronously.
    The search orchestration service will pick up the search and execute it.
    """
    logger.info("create_search_request", user_id=user.id, search_type=search_type.value)

    try:
        # Get active profile
        active_profile = await profile_repo.get_active(user.id)
        if not active_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active client profile. Please select a profile first.",
            )

        # Check for existing in-progress search
        existing = await search_repo.list_by_profile(
            client_profile_id=active_profile.id,
            status=SearchStatus.IN_PROGRESS,
            limit=1,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A search is already in progress for this profile.",
            )

        search = await search_repo.create(
            SearchCreate(
                client_profile_id=active_profile.id,
                search_type=search_type,
                quality_setting=quality_setting,
            )
        )

        logger.info("search_created", search_id=search.id, user_id=user.id)
        return _to_response(search)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("create_search_failed", user_id=user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create search",
        ) from e


@router.get("/{search_id}", response_model=SearchResponse)
async def get_search(
    search_id: str,
    user: CurrentUser,
    search_repo: Annotated[SearchRepository, Depends(get_search_repository)],
    profile_repo: Annotated[ClientProfileRepository, Depends(get_profile_repository)],
) -> SearchResponse:
    """
    Get search status and results.

    Returns detailed information about a specific search.
    """
    logger.info("get_search_request", search_id=search_id, user_id=user.id)

    try:
        # Get active profile
        active_profile = await profile_repo.get_active(user.id)
        if not active_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active client profile.",
            )

        search = await search_repo.get_by_id(search_id, active_profile.id)
        if not search:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Search not found",
            )

        return _to_response(search)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_search_failed", search_id=search_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get search",
        ) from e


@router.post("/{search_id}/cancel", response_model=SearchResponse)
async def cancel_search(
    search_id: str,
    user: CurrentUser,
    search_repo: Annotated[SearchRepository, Depends(get_search_repository)],
    profile_repo: Annotated[ClientProfileRepository, Depends(get_profile_repository)],
) -> SearchResponse:
    """
    Cancel an in-progress search.

    Only searches with status PENDING or IN_PROGRESS can be cancelled.
    """
    logger.info("cancel_search_request", search_id=search_id, user_id=user.id)

    try:
        # Get active profile
        active_profile = await profile_repo.get_active(user.id)
        if not active_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active client profile.",
            )

        # Get search and verify ownership
        search = await search_repo.get_by_id(search_id, active_profile.id)
        if not search:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Search not found",
            )

        # Check if cancellable
        if search.status not in [SearchStatus.PENDING, SearchStatus.IN_PROGRESS]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel search with status '{search.status.value}'",
            )

        cancelled = await search_repo.cancel(search_id)
        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel search",
            )

        logger.info("search_cancelled", search_id=search_id, user_id=user.id)
        return _to_response(cancelled)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("cancel_search_failed", search_id=search_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel search",
        ) from e
