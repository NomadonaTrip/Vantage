"""Search repository for database operations."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from supabase import Client

from src.schemas.lead import LeadSource
from src.schemas.search import (
    ManualSearchParams,
    Search,
    SearchCreate,
    SearchStatus,
    SearchType,
    SearchUpdate,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SearchRepository:
    """Repository for search CRUD operations."""

    def __init__(self, supabase: Client) -> None:
        """Initialize repository with Supabase client."""
        self.supabase = supabase
        self.table = "searches"

    async def list_by_profile(
        self,
        client_profile_id: str,
        status: SearchStatus | None = None,
        limit: int = 20,
    ) -> list[Search]:
        """
        List searches for a client profile.

        Args:
            client_profile_id: Profile UUID.
            status: Filter by status.
            limit: Maximum results to return.

        Returns:
            List of searches.
        """
        logger.info("listing_searches", client_profile_id=client_profile_id)

        try:
            query = (
                self.supabase.table(self.table)
                .select("*")
                .eq("client_profile_id", client_profile_id)
                .order("started_at", desc=True)
                .limit(limit)
            )

            if status:
                query = query.eq("status", status.value)

            result = query.execute()

            searches = [self._to_search(row) for row in result.data]

            logger.info(
                "searches_listed",
                client_profile_id=client_profile_id,
                count=len(searches),
            )
            return searches

        except Exception as e:
            logger.exception("searches_list_failed", client_profile_id=client_profile_id, error=str(e))
            raise

    async def get_by_id(self, search_id: str, client_profile_id: str | None = None) -> Search | None:
        """
        Get search by ID.

        Args:
            search_id: Search UUID.
            client_profile_id: Optional profile UUID for authorization.

        Returns:
            Search if found, None otherwise.
        """
        try:
            query = self.supabase.table(self.table).select("*").eq("id", search_id)

            if client_profile_id:
                query = query.eq("client_profile_id", client_profile_id)

            result = query.execute()

            if not result.data:
                return None

            return self._to_search(result.data[0])

        except Exception as e:
            logger.exception("search_get_failed", search_id=search_id, error=str(e))
            raise

    async def create(self, data: SearchCreate) -> Search:
        """
        Create a new search.

        Args:
            data: Search creation data.

        Returns:
            Created search.
        """
        search_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        logger.info(
            "creating_search",
            search_id=search_id,
            client_profile_id=data.client_profile_id,
            search_type=data.search_type.value,
        )

        try:
            insert_data = {
                "id": search_id,
                "client_profile_id": data.client_profile_id,
                "search_type": data.search_type.value,
                "manual_params": data.manual_params.model_dump() if data.manual_params else None,
                "quality_setting": data.quality_setting,
                "status": SearchStatus.PENDING.value,
                "sources_queried": [],
                "sources_successful": [],
                "sources_failed": [],
                "lead_count": 0,
                "started_at": now,
                "completed_at": None,
                "error_message": None,
            }

            result = self.supabase.table(self.table).insert(insert_data).execute()

            logger.info("search_created", search_id=search_id)
            return self._to_search(result.data[0])

        except Exception as e:
            logger.exception("search_create_failed", error=str(e))
            raise

    async def update(self, search_id: str, data: SearchUpdate) -> Search | None:
        """
        Update search execution state.

        Args:
            search_id: Search UUID.
            data: Update data.

        Returns:
            Updated search or None if not found.
        """
        logger.info("updating_search", search_id=search_id)

        try:
            update_data: dict[str, Any] = {}

            if data.status is not None:
                update_data["status"] = data.status.value
            if data.sources_queried is not None:
                update_data["sources_queried"] = [s.value for s in data.sources_queried]
            if data.sources_successful is not None:
                update_data["sources_successful"] = [s.value for s in data.sources_successful]
            if data.sources_failed is not None:
                update_data["sources_failed"] = [s.value for s in data.sources_failed]
            if data.lead_count is not None:
                update_data["lead_count"] = data.lead_count
            if data.error_message is not None:
                update_data["error_message"] = data.error_message
            if data.completed_at is not None:
                update_data["completed_at"] = data.completed_at.isoformat()

            if not update_data:
                return await self.get_by_id(search_id)

            result = (
                self.supabase.table(self.table)
                .update(update_data)
                .eq("id", search_id)
                .execute()
            )

            if not result.data:
                return None

            logger.info("search_updated", search_id=search_id, status=update_data.get("status"))
            return self._to_search(result.data[0])

        except Exception as e:
            logger.exception("search_update_failed", search_id=search_id, error=str(e))
            raise

    async def add_source_result(
        self,
        search_id: str,
        source: LeadSource,
        success: bool,
        leads_found: int = 0,
    ) -> Search | None:
        """
        Add a source result to the search.

        Args:
            search_id: Search UUID.
            source: Source that completed.
            success: Whether source succeeded.
            leads_found: Number of leads found from this source.

        Returns:
            Updated search.
        """
        logger.info(
            "adding_source_result",
            search_id=search_id,
            source=source.value,
            success=success,
            leads_found=leads_found,
        )

        try:
            # Get current search
            search = await self.get_by_id(search_id)
            if not search:
                return None

            # Update arrays
            sources_queried = list(search.sources_queried)
            sources_successful = list(search.sources_successful)
            sources_failed = list(search.sources_failed)

            if source not in sources_queried:
                sources_queried.append(source)

            if success and source not in sources_successful:
                sources_successful.append(source)
            elif not success and source not in sources_failed:
                sources_failed.append(source)

            # Update lead count
            new_lead_count = search.lead_count + leads_found

            return await self.update(
                search_id,
                SearchUpdate(
                    sources_queried=[s for s in sources_queried],
                    sources_successful=[s for s in sources_successful],
                    sources_failed=[s for s in sources_failed],
                    lead_count=new_lead_count,
                ),
            )

        except Exception as e:
            logger.exception("add_source_result_failed", search_id=search_id, error=str(e))
            raise

    async def complete(
        self,
        search_id: str,
        success: bool = True,
        error_message: str | None = None,
    ) -> Search | None:
        """
        Mark search as completed or failed.

        Args:
            search_id: Search UUID.
            success: Whether search succeeded.
            error_message: Error message if failed.

        Returns:
            Updated search.
        """
        status = SearchStatus.COMPLETED if success else SearchStatus.FAILED

        return await self.update(
            search_id,
            SearchUpdate(
                status=status,
                completed_at=datetime.utcnow(),
                error_message=error_message,
            ),
        )

    async def cancel(self, search_id: str) -> Search | None:
        """
        Cancel an in-progress search.

        Args:
            search_id: Search UUID.

        Returns:
            Updated search.
        """
        logger.info("cancelling_search", search_id=search_id)

        return await self.update(
            search_id,
            SearchUpdate(
                status=SearchStatus.CANCELLED,
                completed_at=datetime.utcnow(),
            ),
        )

    def _to_search(self, data: dict[str, Any]) -> Search:
        """Convert database row to Search model."""
        manual_params = None
        if data.get("manual_params"):
            manual_params = ManualSearchParams(**data["manual_params"])

        return Search(
            id=data["id"],
            client_profile_id=data["client_profile_id"],
            search_type=SearchType(data["search_type"]),
            manual_params=manual_params,
            quality_setting=data.get("quality_setting", 0.7),
            status=SearchStatus(data["status"]),
            sources_queried=[LeadSource(s) for s in data.get("sources_queried", [])],
            sources_successful=[LeadSource(s) for s in data.get("sources_successful", [])],
            sources_failed=[LeadSource(s) for s in data.get("sources_failed", [])],
            lead_count=data.get("lead_count", 0),
            started_at=datetime.fromisoformat(data["started_at"].replace("Z", "+00:00")),
            completed_at=datetime.fromisoformat(data["completed_at"].replace("Z", "+00:00"))
            if data.get("completed_at")
            else None,
            error_message=data.get("error_message"),
        )
