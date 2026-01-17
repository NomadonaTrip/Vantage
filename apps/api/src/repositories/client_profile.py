"""Client profile repository for database operations."""

from datetime import datetime
from uuid import uuid4

from supabase import Client

from src.schemas.client_profile import (
    ClientProfile,
    ClientProfileCreate,
    ClientProfileUpdate,
    ScoringWeights,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ClientProfileRepository:
    """Repository for client profile CRUD operations."""

    def __init__(self, supabase: Client) -> None:
        """
        Initialize repository.

        Args:
            supabase: Supabase client instance.
        """
        self.supabase = supabase
        self.table = "client_profiles"

    async def list_by_user(self, user_id: str) -> list[ClientProfile]:
        """
        List all client profiles for a user.

        Args:
            user_id: User's UUID.

        Returns:
            List of client profiles.
        """
        logger.info("listing_client_profiles", user_id=user_id)

        response = (
            self.supabase.table(self.table)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        profiles = []
        for row in response.data:
            profiles.append(self._row_to_profile(row))

        logger.info("client_profiles_listed", user_id=user_id, count=len(profiles))
        return profiles

    async def get_by_id(self, profile_id: str, user_id: str) -> ClientProfile | None:
        """
        Get a client profile by ID.

        Args:
            profile_id: Profile UUID.
            user_id: User's UUID (for authorization).

        Returns:
            Client profile or None if not found.
        """
        logger.info("getting_client_profile", profile_id=profile_id, user_id=user_id)

        response = (
            self.supabase.table(self.table)
            .select("*")
            .eq("id", profile_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not response.data:
            logger.warning("client_profile_not_found", profile_id=profile_id)
            return None

        return self._row_to_profile(response.data)

    async def create(self, user_id: str, data: ClientProfileCreate) -> ClientProfile:
        """
        Create a new client profile.

        Args:
            user_id: User's UUID.
            data: Profile creation data.

        Returns:
            Created client profile.
        """
        profile_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        logger.info("creating_client_profile", profile_id=profile_id, user_id=user_id)

        # Check if user has any profiles - first one is automatically active
        existing = (
            self.supabase.table(self.table)
            .select("id")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        is_first_profile = len(existing.data) == 0

        insert_data = {
            "id": profile_id,
            "user_id": user_id,
            "company_name": data.company_name,
            "industry": data.industry,
            "ideal_customer_profile": data.ideal_customer_profile,
            "services": data.services,
            "additional_context": data.additional_context,
            "scoring_weight_overrides": (
                data.scoring_weight_overrides.model_dump()
                if data.scoring_weight_overrides
                else None
            ),
            "is_active": is_first_profile,
            "created_at": now,
            "updated_at": now,
        }

        response = self.supabase.table(self.table).insert(insert_data).execute()

        logger.info(
            "client_profile_created",
            profile_id=profile_id,
            user_id=user_id,
            is_active=is_first_profile,
        )

        return self._row_to_profile(response.data[0])

    async def update(
        self, profile_id: str, user_id: str, data: ClientProfileUpdate
    ) -> ClientProfile | None:
        """
        Update a client profile.

        Args:
            profile_id: Profile UUID.
            user_id: User's UUID (for authorization).
            data: Update data.

        Returns:
            Updated profile or None if not found.
        """
        logger.info("updating_client_profile", profile_id=profile_id, user_id=user_id)

        # Build update dict with only provided fields
        update_data: dict = {"updated_at": datetime.utcnow().isoformat()}

        if data.company_name is not None:
            update_data["company_name"] = data.company_name
        if data.industry is not None:
            update_data["industry"] = data.industry
        if data.ideal_customer_profile is not None:
            update_data["ideal_customer_profile"] = data.ideal_customer_profile
        if data.services is not None:
            update_data["services"] = data.services
        if data.additional_context is not None:
            update_data["additional_context"] = data.additional_context
        if data.scoring_weight_overrides is not None:
            update_data["scoring_weight_overrides"] = data.scoring_weight_overrides.model_dump()

        response = (
            self.supabase.table(self.table)
            .update(update_data)
            .eq("id", profile_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            logger.warning("client_profile_update_failed", profile_id=profile_id)
            return None

        logger.info("client_profile_updated", profile_id=profile_id)
        return self._row_to_profile(response.data[0])

    async def delete(self, profile_id: str, user_id: str) -> bool:
        """
        Delete a client profile.

        Args:
            profile_id: Profile UUID.
            user_id: User's UUID (for authorization).

        Returns:
            True if deleted, False if not found.
        """
        logger.info("deleting_client_profile", profile_id=profile_id, user_id=user_id)

        # Check if profile exists and belongs to user
        existing = await self.get_by_id(profile_id, user_id)
        if not existing:
            return False

        # If deleting the active profile, activate another one
        if existing.is_active:
            # Find another profile to activate
            other_profiles = await self.list_by_user(user_id)
            for profile in other_profiles:
                if profile.id != profile_id:
                    await self.set_active(profile.id, user_id)
                    break

        # Delete the profile (cascades to leads, searches via FK)
        self.supabase.table(self.table).delete().eq("id", profile_id).eq(
            "user_id", user_id
        ).execute()

        logger.info("client_profile_deleted", profile_id=profile_id)
        return True

    async def set_active(self, profile_id: str, user_id: str) -> ClientProfile | None:
        """
        Set a client profile as the active profile.

        Args:
            profile_id: Profile UUID to activate.
            user_id: User's UUID.

        Returns:
            Activated profile or None if not found.
        """
        logger.info("setting_active_profile", profile_id=profile_id, user_id=user_id)

        # Deactivate all other profiles for this user
        self.supabase.table(self.table).update({"is_active": False}).eq(
            "user_id", user_id
        ).execute()

        # Activate the specified profile
        response = (
            self.supabase.table(self.table)
            .update({"is_active": True, "updated_at": datetime.utcnow().isoformat()})
            .eq("id", profile_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            logger.warning("set_active_profile_failed", profile_id=profile_id)
            return None

        logger.info("active_profile_set", profile_id=profile_id)
        return self._row_to_profile(response.data[0])

    async def get_active(self, user_id: str) -> ClientProfile | None:
        """
        Get the active client profile for a user.

        Args:
            user_id: User's UUID.

        Returns:
            Active client profile or None.
        """
        response = (
            self.supabase.table(self.table)
            .select("*")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .single()
            .execute()
        )

        if not response.data:
            return None

        return self._row_to_profile(response.data)

    def _row_to_profile(self, row: dict) -> ClientProfile:
        """Convert database row to ClientProfile model."""
        scoring_weights = None
        if row.get("scoring_weight_overrides"):
            scoring_weights = ScoringWeights(**row["scoring_weight_overrides"])

        return ClientProfile(
            id=row["id"],
            user_id=row["user_id"],
            company_name=row["company_name"],
            industry=row["industry"],
            ideal_customer_profile=row.get("ideal_customer_profile", "")
            or row.get("ideal_client_description", ""),
            services=row.get("services", []) or [],
            additional_context=row.get("additional_context"),
            scoring_weight_overrides=scoring_weights,
            is_active=row.get("is_active", False),
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            if isinstance(row["created_at"], str)
            else row["created_at"],
            updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00"))
            if isinstance(row["updated_at"], str)
            else row["updated_at"],
        )
