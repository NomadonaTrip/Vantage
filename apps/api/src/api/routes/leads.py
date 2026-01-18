"""Lead routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from supabase import Client

from src.api.middleware.auth import CurrentUser
from src.core.supabase import get_supabase_client
from src.repositories.client_profile import ClientProfileRepository
from src.repositories.lead import LeadRepository
from src.schemas.lead import (
    LeadAccuracy,
    LeadDetailResponse,
    LeadListResponse,
    LeadResponse,
    LeadSource,
    LeadStatus,
    LeadUpdate,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/leads", tags=["Leads"])


def get_lead_repository(
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> LeadRepository:
    """Get lead repository instance."""
    return LeadRepository(supabase)


def get_profile_repository(
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> ClientProfileRepository:
    """Get client profile repository instance."""
    return ClientProfileRepository(supabase)


@router.get("", response_model=LeadListResponse)
async def list_leads(
    user: CurrentUser,
    lead_repo: Annotated[LeadRepository, Depends(get_lead_repository)],
    profile_repo: Annotated[ClientProfileRepository, Depends(get_profile_repository)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: LeadStatus | None = None,
    source: LeadSource | None = None,
    min_score: float | None = Query(default=None, ge=0, le=100),
    sort_by: str = Query(default="intent_score", regex="^(intent_score|created_at|company|name)$"),
    sort_desc: bool = True,
) -> LeadListResponse:
    """
    List leads for the user's active client profile.

    Supports filtering by status, source, and minimum score.
    Results are paginated and sortable.
    """
    logger.info("list_leads_request", user_id=user.id)

    try:
        # Get active profile
        active_profile = await profile_repo.get_active(user.id)
        if not active_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active client profile. Please select a profile first.",
            )

        leads, total = await lead_repo.list_by_profile(
            client_profile_id=active_profile.id,
            page=page,
            page_size=page_size,
            status=status,
            source=source,
            min_score=min_score,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

        return LeadListResponse(
            leads=[
                LeadResponse(
                    id=lead.id,
                    client_profile_id=lead.client_profile_id,
                    search_id=lead.search_id,
                    name=lead.name,
                    email=lead.email,
                    phone=lead.phone,
                    company=lead.company,
                    company_size=lead.company_size,
                    intent_score=lead.intent_score,
                    score_breakdown=lead.score_breakdown,
                    source=lead.source,
                    source_url=lead.source_url,
                    status=lead.status,
                    accuracy=lead.accuracy,
                    created_at=lead.created_at,
                    updated_at=lead.updated_at,
                )
                for lead in leads
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("list_leads_failed", user_id=user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list leads",
        ) from e


@router.get("/export")
async def export_leads(
    user: CurrentUser,
    lead_repo: Annotated[LeadRepository, Depends(get_lead_repository)],
    profile_repo: Annotated[ClientProfileRepository, Depends(get_profile_repository)],
    status_filter: LeadStatus | None = Query(default=None, alias="status"),
    source: LeadSource | None = None,
    min_score: float | None = Query(default=None, ge=0, le=100),
) -> StreamingResponse:
    """
    Export leads to CSV format.

    Returns all leads matching the filters as a downloadable CSV file.
    """
    logger.info("export_leads_request", user_id=user.id)

    try:
        # Get active profile
        active_profile = await profile_repo.get_active(user.id)
        if not active_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active client profile. Please select a profile first.",
            )

        # Get all leads (no pagination for export)
        leads, _ = await lead_repo.list_by_profile(
            client_profile_id=active_profile.id,
            page=1,
            page_size=10000,  # Large limit for export
            status=status_filter,
            source=source,
            min_score=min_score,
        )

        # Generate CSV
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Name",
            "Email",
            "Phone",
            "Company",
            "Company Size",
            "Intent Score",
            "Source",
            "Status",
            "Accuracy",
            "Source URL",
            "Created At",
        ])

        # Data rows
        for lead in leads:
            writer.writerow([
                lead.name,
                lead.email or "",
                lead.phone or "",
                lead.company,
                lead.company_size.value,
                lead.intent_score,
                lead.source.value,
                lead.status.value,
                lead.accuracy.value if lead.accuracy else "",
                lead.source_url or "",
                lead.created_at.isoformat(),
            ])

        output.seek(0)
        content = output.getvalue()

        logger.info("leads_exported", user_id=user.id, count=len(leads))

        return StreamingResponse(
            iter([content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="leads_{active_profile.company_name.replace(" ", "_")}.csv"'
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("export_leads_failed", user_id=user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export leads",
        ) from e


@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def get_lead(
    lead_id: str,
    user: CurrentUser,
    lead_repo: Annotated[LeadRepository, Depends(get_lead_repository)],
    profile_repo: Annotated[ClientProfileRepository, Depends(get_profile_repository)],
) -> LeadDetailResponse:
    """
    Get detailed information about a specific lead.

    Includes status history and raw data.
    """
    logger.info("get_lead_request", lead_id=lead_id, user_id=user.id)

    try:
        # Get active profile
        active_profile = await profile_repo.get_active(user.id)
        if not active_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active client profile.",
            )

        lead = await lead_repo.get_by_id(lead_id, active_profile.id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found",
            )

        # Get status history
        status_history = await lead_repo.get_status_history(lead_id)

        return LeadDetailResponse(
            id=lead.id,
            client_profile_id=lead.client_profile_id,
            search_id=lead.search_id,
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            company=lead.company,
            company_size=lead.company_size,
            intent_score=lead.intent_score,
            score_breakdown=lead.score_breakdown,
            source=lead.source,
            source_url=lead.source_url,
            status=lead.status,
            accuracy=lead.accuracy,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
            raw_data=lead.raw_data,
            status_history=status_history,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_lead_failed", lead_id=lead_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get lead",
        ) from e


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    request: LeadUpdate,
    user: CurrentUser,
    lead_repo: Annotated[LeadRepository, Depends(get_lead_repository)],
    profile_repo: Annotated[ClientProfileRepository, Depends(get_profile_repository)],
) -> LeadResponse:
    """
    Update a lead's status, accuracy, or contact information.

    Status changes are recorded in history.
    """
    logger.info("update_lead_request", lead_id=lead_id, user_id=user.id)

    try:
        # Get active profile
        active_profile = await profile_repo.get_active(user.id)
        if not active_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active client profile.",
            )

        lead = await lead_repo.update(lead_id, active_profile.id, request)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found",
            )

        return LeadResponse(
            id=lead.id,
            client_profile_id=lead.client_profile_id,
            search_id=lead.search_id,
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            company=lead.company,
            company_size=lead.company_size,
            intent_score=lead.intent_score,
            score_breakdown=lead.score_breakdown,
            source=lead.source,
            source_url=lead.source_url,
            status=lead.status,
            accuracy=lead.accuracy,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("update_lead_failed", lead_id=lead_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update lead",
        ) from e


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: str,
    user: CurrentUser,
    lead_repo: Annotated[LeadRepository, Depends(get_lead_repository)],
    profile_repo: Annotated[ClientProfileRepository, Depends(get_profile_repository)],
) -> None:
    """
    Delete a lead.

    This also deletes the lead's status history.
    """
    logger.info("delete_lead_request", lead_id=lead_id, user_id=user.id)

    try:
        # Get active profile
        active_profile = await profile_repo.get_active(user.id)
        if not active_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active client profile.",
            )

        deleted = await lead_repo.delete(lead_id, active_profile.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("delete_lead_failed", lead_id=lead_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete lead",
        ) from e
