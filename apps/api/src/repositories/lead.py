"""Lead repository for database operations."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from supabase import Client

from src.schemas.lead import (
    CompanySize,
    Lead,
    LeadAccuracy,
    LeadCreate,
    LeadSource,
    LeadStatus,
    LeadStatusHistory,
    LeadUpdate,
    ScoreBreakdown,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class LeadRepository:
    """Repository for lead CRUD operations."""

    def __init__(self, supabase: Client) -> None:
        """Initialize repository with Supabase client."""
        self.supabase = supabase
        self.table = "leads"
        self.history_table = "lead_status_history"

    async def list_by_profile(
        self,
        client_profile_id: str,
        page: int = 1,
        page_size: int = 20,
        status: LeadStatus | None = None,
        source: LeadSource | None = None,
        min_score: float | None = None,
        sort_by: str = "intent_score",
        sort_desc: bool = True,
    ) -> tuple[list[Lead], int]:
        """
        List leads for a client profile with filtering and pagination.

        Args:
            client_profile_id: Profile UUID.
            page: Page number (1-indexed).
            page_size: Results per page.
            status: Filter by status.
            source: Filter by source.
            min_score: Filter by minimum intent score.
            sort_by: Field to sort by.
            sort_desc: Sort descending if True.

        Returns:
            Tuple of (leads list, total count).
        """
        logger.info(
            "listing_leads",
            client_profile_id=client_profile_id,
            page=page,
            page_size=page_size,
        )

        try:
            # Build query
            query = self.supabase.table(self.table).select("*", count="exact")
            query = query.eq("client_profile_id", client_profile_id)

            if status:
                query = query.eq("status", status.value)
            if source:
                query = query.eq("source", source.value)
            if min_score is not None:
                query = query.gte("intent_score", min_score)

            # Apply sorting
            query = query.order(sort_by, desc=sort_desc)

            # Apply pagination
            offset = (page - 1) * page_size
            query = query.range(offset, offset + page_size - 1)

            result = query.execute()
            total = result.count or 0

            leads = [self._to_lead(row) for row in result.data]

            logger.info(
                "leads_listed",
                client_profile_id=client_profile_id,
                count=len(leads),
                total=total,
            )
            return leads, total

        except Exception as e:
            logger.exception("leads_list_failed", client_profile_id=client_profile_id, error=str(e))
            raise

    async def get_by_id(self, lead_id: str, client_profile_id: str) -> Lead | None:
        """
        Get lead by ID with profile authorization.

        Args:
            lead_id: Lead UUID.
            client_profile_id: Profile UUID for authorization.

        Returns:
            Lead if found, None otherwise.
        """
        try:
            result = (
                self.supabase.table(self.table)
                .select("*")
                .eq("id", lead_id)
                .eq("client_profile_id", client_profile_id)
                .execute()
            )

            if not result.data:
                return None

            return self._to_lead(result.data[0])

        except Exception as e:
            logger.exception("lead_get_failed", lead_id=lead_id, error=str(e))
            raise

    async def create(self, data: LeadCreate) -> Lead:
        """
        Create a new lead.

        Args:
            data: Lead creation data.

        Returns:
            Created lead.
        """
        lead_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        logger.info(
            "creating_lead",
            lead_id=lead_id,
            client_profile_id=data.client_profile_id,
            source=data.source.value,
        )

        try:
            insert_data = {
                "id": lead_id,
                "client_profile_id": data.client_profile_id,
                "search_id": data.search_id,
                "name": data.name,
                "email": data.email,
                "phone": data.phone,
                "company": data.company,
                "company_size": data.company_size.value,
                "intent_score": data.intent_score,
                "score_breakdown": data.score_breakdown.model_dump(),
                "source": data.source.value,
                "source_url": data.source_url,
                "status": LeadStatus.NEW.value,
                "accuracy": None,
                "raw_data": data.raw_data,
                "created_at": now,
                "updated_at": now,
            }

            result = self.supabase.table(self.table).insert(insert_data).execute()

            logger.info("lead_created", lead_id=lead_id)
            return self._to_lead(result.data[0])

        except Exception as e:
            logger.exception("lead_create_failed", error=str(e))
            raise

    async def create_batch(self, leads: list[LeadCreate]) -> list[Lead]:
        """
        Create multiple leads in a batch.

        Args:
            leads: List of lead creation data.

        Returns:
            List of created leads.
        """
        if not leads:
            return []

        logger.info("creating_leads_batch", count=len(leads))

        try:
            now = datetime.utcnow().isoformat()
            insert_data = []

            for data in leads:
                lead_id = str(uuid4())
                insert_data.append({
                    "id": lead_id,
                    "client_profile_id": data.client_profile_id,
                    "search_id": data.search_id,
                    "name": data.name,
                    "email": data.email,
                    "phone": data.phone,
                    "company": data.company,
                    "company_size": data.company_size.value,
                    "intent_score": data.intent_score,
                    "score_breakdown": data.score_breakdown.model_dump(),
                    "source": data.source.value,
                    "source_url": data.source_url,
                    "status": LeadStatus.NEW.value,
                    "accuracy": None,
                    "raw_data": data.raw_data,
                    "created_at": now,
                    "updated_at": now,
                })

            result = self.supabase.table(self.table).insert(insert_data).execute()

            created_leads = [self._to_lead(row) for row in result.data]
            logger.info("leads_batch_created", count=len(created_leads))
            return created_leads

        except Exception as e:
            logger.exception("leads_batch_create_failed", error=str(e))
            raise

    async def update(
        self,
        lead_id: str,
        client_profile_id: str,
        data: LeadUpdate,
    ) -> Lead | None:
        """
        Update a lead.

        Args:
            lead_id: Lead UUID.
            client_profile_id: Profile UUID for authorization.
            data: Update data.

        Returns:
            Updated lead or None if not found.
        """
        logger.info("updating_lead", lead_id=lead_id)

        try:
            # Get current lead for status history
            current = await self.get_by_id(lead_id, client_profile_id)
            if not current:
                return None

            update_data: dict[str, Any] = {"updated_at": datetime.utcnow().isoformat()}

            if data.status is not None and data.status != current.status:
                update_data["status"] = data.status.value
                # Record status history
                await self._record_status_change(
                    lead_id, current.status, data.status, data.notes
                )

            if data.accuracy is not None:
                update_data["accuracy"] = data.accuracy.value
            if data.email is not None:
                update_data["email"] = data.email
            if data.phone is not None:
                update_data["phone"] = data.phone

            result = (
                self.supabase.table(self.table)
                .update(update_data)
                .eq("id", lead_id)
                .eq("client_profile_id", client_profile_id)
                .execute()
            )

            if not result.data:
                return None

            logger.info("lead_updated", lead_id=lead_id)
            return self._to_lead(result.data[0])

        except Exception as e:
            logger.exception("lead_update_failed", lead_id=lead_id, error=str(e))
            raise

    async def delete(self, lead_id: str, client_profile_id: str) -> bool:
        """
        Delete a lead.

        Args:
            lead_id: Lead UUID.
            client_profile_id: Profile UUID for authorization.

        Returns:
            True if deleted, False if not found.
        """
        logger.info("deleting_lead", lead_id=lead_id)

        try:
            # Check exists
            current = await self.get_by_id(lead_id, client_profile_id)
            if not current:
                return False

            # Delete status history first
            self.supabase.table(self.history_table).delete().eq("lead_id", lead_id).execute()

            # Delete lead
            self.supabase.table(self.table).delete().eq("id", lead_id).eq(
                "client_profile_id", client_profile_id
            ).execute()

            logger.info("lead_deleted", lead_id=lead_id)
            return True

        except Exception as e:
            logger.exception("lead_delete_failed", lead_id=lead_id, error=str(e))
            raise

    async def get_status_history(self, lead_id: str) -> list[LeadStatusHistory]:
        """Get status change history for a lead."""
        try:
            result = (
                self.supabase.table(self.history_table)
                .select("*")
                .eq("lead_id", lead_id)
                .order("changed_at", desc=True)
                .execute()
            )

            return [
                LeadStatusHistory(
                    id=row["id"],
                    lead_id=row["lead_id"],
                    previous_status=LeadStatus(row["previous_status"]) if row.get("previous_status") else None,
                    new_status=LeadStatus(row["new_status"]),
                    changed_at=datetime.fromisoformat(row["changed_at"].replace("Z", "+00:00")),
                    notes=row.get("notes"),
                )
                for row in result.data
            ]

        except Exception as e:
            logger.exception("status_history_get_failed", lead_id=lead_id, error=str(e))
            raise

    async def _record_status_change(
        self,
        lead_id: str,
        previous_status: LeadStatus,
        new_status: LeadStatus,
        notes: str | None,
    ) -> None:
        """Record a status change in history."""
        try:
            self.supabase.table(self.history_table).insert({
                "id": str(uuid4()),
                "lead_id": lead_id,
                "previous_status": previous_status.value,
                "new_status": new_status.value,
                "changed_at": datetime.utcnow().isoformat(),
                "notes": notes,
            }).execute()
        except Exception as e:
            logger.warning("status_history_record_failed", lead_id=lead_id, error=str(e))

    def _to_lead(self, data: dict[str, Any]) -> Lead:
        """Convert database row to Lead model."""
        score_breakdown = ScoreBreakdown()
        if data.get("score_breakdown"):
            score_breakdown = ScoreBreakdown(**data["score_breakdown"])

        return Lead(
            id=data["id"],
            client_profile_id=data["client_profile_id"],
            search_id=data["search_id"],
            name=data["name"],
            email=data.get("email"),
            phone=data.get("phone"),
            company=data["company"],
            company_size=CompanySize(data.get("company_size", "unknown")),
            intent_score=data.get("intent_score", 0),
            score_breakdown=score_breakdown,
            source=LeadSource(data["source"]),
            source_url=data.get("source_url"),
            status=LeadStatus(data.get("status", "new")),
            accuracy=LeadAccuracy(data["accuracy"]) if data.get("accuracy") else None,
            raw_data=data.get("raw_data"),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
        )
