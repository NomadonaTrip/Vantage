"""Client profile routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from src.api.middleware.auth import CurrentUser
from src.core.supabase import get_supabase_client
from src.repositories.client_profile import ClientProfileRepository
from src.schemas.client_profile import (
    ClientProfileCreate,
    ClientProfileListResponse,
    ClientProfileResponse,
    ClientProfileUpdate,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/client-profiles", tags=["Client Profiles"])


def get_client_profile_repository(
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> ClientProfileRepository:
    """Get client profile repository instance."""
    return ClientProfileRepository(supabase)


@router.get("", response_model=ClientProfileListResponse)
async def list_client_profiles(
    user: CurrentUser,
    repo: Annotated[ClientProfileRepository, Depends(get_client_profile_repository)],
) -> ClientProfileListResponse:
    """
    List all client profiles for the authenticated user.

    Returns profiles ordered by creation date (newest first).
    """
    logger.info("list_client_profiles_request", user_id=user.id)

    try:
        profiles = await repo.list_by_user(user.id)

        return ClientProfileListResponse(
            profiles=[
                ClientProfileResponse(
                    id=p.id,
                    user_id=p.user_id,
                    company_name=p.company_name,
                    industry=p.industry,
                    ideal_customer_profile=p.ideal_customer_profile,
                    services=p.services,
                    additional_context=p.additional_context,
                    scoring_weight_overrides=p.scoring_weight_overrides,
                    is_active=p.is_active,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
                for p in profiles
            ],
            total=len(profiles),
        )
    except Exception as e:
        logger.exception("list_client_profiles_failed", user_id=user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list client profiles",
        ) from e


@router.post("", response_model=ClientProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_client_profile(
    request: ClientProfileCreate,
    user: CurrentUser,
    repo: Annotated[ClientProfileRepository, Depends(get_client_profile_repository)],
) -> ClientProfileResponse:
    """
    Create a new client profile.

    The first profile created for a user is automatically set as active.
    """
    logger.info("create_client_profile_request", user_id=user.id)

    try:
        profile = await repo.create(user.id, request)

        return ClientProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            company_name=profile.company_name,
            industry=profile.industry,
            ideal_customer_profile=profile.ideal_customer_profile,
            services=profile.services,
            additional_context=profile.additional_context,
            scoring_weight_overrides=profile.scoring_weight_overrides,
            is_active=profile.is_active,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
    except Exception as e:
        logger.exception("create_client_profile_failed", user_id=user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create client profile",
        ) from e


@router.get("/{profile_id}", response_model=ClientProfileResponse)
async def get_client_profile(
    profile_id: str,
    user: CurrentUser,
    repo: Annotated[ClientProfileRepository, Depends(get_client_profile_repository)],
) -> ClientProfileResponse:
    """
    Get a specific client profile by ID.

    Only returns the profile if it belongs to the authenticated user.
    """
    logger.info("get_client_profile_request", profile_id=profile_id, user_id=user.id)

    try:
        profile = await repo.get_by_id(profile_id, user.id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client profile not found",
            )

        return ClientProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            company_name=profile.company_name,
            industry=profile.industry,
            ideal_customer_profile=profile.ideal_customer_profile,
            services=profile.services,
            additional_context=profile.additional_context,
            scoring_weight_overrides=profile.scoring_weight_overrides,
            is_active=profile.is_active,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_client_profile_failed", profile_id=profile_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get client profile",
        ) from e


@router.patch("/{profile_id}", response_model=ClientProfileResponse)
async def update_client_profile(
    profile_id: str,
    request: ClientProfileUpdate,
    user: CurrentUser,
    repo: Annotated[ClientProfileRepository, Depends(get_client_profile_repository)],
) -> ClientProfileResponse:
    """
    Update a client profile.

    Only updates the fields provided in the request.
    """
    logger.info("update_client_profile_request", profile_id=profile_id, user_id=user.id)

    try:
        profile = await repo.update(profile_id, user.id, request)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client profile not found",
            )

        return ClientProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            company_name=profile.company_name,
            industry=profile.industry,
            ideal_customer_profile=profile.ideal_customer_profile,
            services=profile.services,
            additional_context=profile.additional_context,
            scoring_weight_overrides=profile.scoring_weight_overrides,
            is_active=profile.is_active,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("update_client_profile_failed", profile_id=profile_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update client profile",
        ) from e


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client_profile(
    profile_id: str,
    user: CurrentUser,
    repo: Annotated[ClientProfileRepository, Depends(get_client_profile_repository)],
) -> None:
    """
    Delete a client profile.

    This also deletes all associated leads and searches.
    If deleting the active profile, another profile will be activated.
    """
    logger.info("delete_client_profile_request", profile_id=profile_id, user_id=user.id)

    try:
        deleted = await repo.delete(profile_id, user.id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client profile not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("delete_client_profile_failed", profile_id=profile_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete client profile",
        ) from e


@router.post("/{profile_id}/activate", response_model=ClientProfileResponse)
async def activate_client_profile(
    profile_id: str,
    user: CurrentUser,
    repo: Annotated[ClientProfileRepository, Depends(get_client_profile_repository)],
) -> ClientProfileResponse:
    """
    Set a client profile as the active profile.

    Only one profile can be active at a time per user.
    """
    logger.info("activate_client_profile_request", profile_id=profile_id, user_id=user.id)

    try:
        profile = await repo.set_active(profile_id, user.id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client profile not found",
            )

        return ClientProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            company_name=profile.company_name,
            industry=profile.industry,
            ideal_customer_profile=profile.ideal_customer_profile,
            services=profile.services,
            additional_context=profile.additional_context,
            scoring_weight_overrides=profile.scoring_weight_overrides,
            is_active=profile.is_active,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("activate_client_profile_failed", profile_id=profile_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate client profile",
        ) from e


@router.get("/active", response_model=ClientProfileResponse | None)
async def get_active_client_profile(
    user: CurrentUser,
    repo: Annotated[ClientProfileRepository, Depends(get_client_profile_repository)],
) -> ClientProfileResponse | None:
    """
    Get the currently active client profile for the user.

    Returns null if no profile is active.
    """
    logger.info("get_active_client_profile_request", user_id=user.id)

    try:
        profile = await repo.get_active(user.id)

        if not profile:
            return None

        return ClientProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            company_name=profile.company_name,
            industry=profile.industry,
            ideal_customer_profile=profile.ideal_customer_profile,
            services=profile.services,
            additional_context=profile.additional_context,
            scoring_weight_overrides=profile.scoring_weight_overrides,
            is_active=profile.is_active,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
    except Exception as e:
        logger.exception("get_active_client_profile_failed", user_id=user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active client profile",
        ) from e
