"""Conversation repository for database operations."""

import uuid
from datetime import datetime
from typing import Any

from supabase import Client

from src.schemas.conversation import (
    Conversation,
    ConversationMessage,
    ConversationStatus,
    ExtractedProfile,
    MessageRole,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ConversationRepository:
    """Repository for conversation CRUD operations."""

    def __init__(self, supabase: Client) -> None:
        """Initialize repository with Supabase client."""
        self.supabase = supabase
        self.table = "conversations"

    async def create(self, initial_message: ConversationMessage | None = None) -> Conversation:
        """
        Create a new conversation.

        Args:
            initial_message: Optional initial assistant message.

        Returns:
            Created conversation.
        """
        conversation_id = str(uuid.uuid4())
        messages = [initial_message.model_dump(mode="json")] if initial_message else []

        data = {
            "id": conversation_id,
            "user_id": None,
            "client_profile_id": None,
            "messages": messages,
            "status": ConversationStatus.IN_PROGRESS.value,
            "extracted_profile": None,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
        }

        try:
            result = self.supabase.table(self.table).insert(data).execute()
            logger.info("conversation_created", conversation_id=conversation_id)
            return self._to_conversation(result.data[0])
        except Exception as e:
            logger.exception("conversation_create_failed", error=str(e))
            raise

    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        """
        Get conversation by ID.

        Args:
            conversation_id: Conversation UUID.

        Returns:
            Conversation if found, None otherwise.
        """
        try:
            result = (
                self.supabase.table(self.table)
                .select("*")
                .eq("id", conversation_id)
                .execute()
            )

            if not result.data:
                return None

            return self._to_conversation(result.data[0])
        except Exception as e:
            logger.exception("conversation_get_failed", conversation_id=conversation_id, error=str(e))
            raise

    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
    ) -> Conversation:
        """
        Add a message to the conversation.

        Args:
            conversation_id: Conversation UUID.
            message: Message to add.

        Returns:
            Updated conversation.
        """
        try:
            # Get current messages
            conversation = await self.get_by_id(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")

            # Append new message
            messages = [m.model_dump(mode="json") for m in conversation.messages]
            messages.append(message.model_dump(mode="json"))

            # Update in database
            result = (
                self.supabase.table(self.table)
                .update({"messages": messages})
                .eq("id", conversation_id)
                .execute()
            )

            logger.info(
                "message_added",
                conversation_id=conversation_id,
                role=message.role.value,
            )
            return self._to_conversation(result.data[0])
        except Exception as e:
            logger.exception("message_add_failed", conversation_id=conversation_id, error=str(e))
            raise

    async def update_status(
        self,
        conversation_id: str,
        status: ConversationStatus,
        extracted_profile: ExtractedProfile | None = None,
    ) -> Conversation:
        """
        Update conversation status and optionally set extracted profile.

        Args:
            conversation_id: Conversation UUID.
            status: New status.
            extracted_profile: Extracted profile data (if completing).

        Returns:
            Updated conversation.
        """
        try:
            update_data: dict[str, Any] = {"status": status.value}

            if status == ConversationStatus.COMPLETED:
                update_data["completed_at"] = datetime.utcnow().isoformat()

            if extracted_profile:
                update_data["extracted_profile"] = extracted_profile.model_dump(mode="json")

            result = (
                self.supabase.table(self.table)
                .update(update_data)
                .eq("id", conversation_id)
                .execute()
            )

            logger.info("conversation_status_updated", conversation_id=conversation_id, status=status.value)
            return self._to_conversation(result.data[0])
        except Exception as e:
            logger.exception("status_update_failed", conversation_id=conversation_id, error=str(e))
            raise

    async def list_by_profile(
        self,
        client_profile_id: str,
        user_id: str,
    ) -> list[Conversation]:
        """
        List all conversations for a client profile.

        Args:
            client_profile_id: Client profile UUID.
            user_id: User UUID (for authorization).

        Returns:
            List of conversations.
        """
        try:
            result = (
                self.supabase.table(self.table)
                .select("*")
                .eq("client_profile_id", client_profile_id)
                .eq("user_id", user_id)
                .order("started_at", desc=True)
                .execute()
            )

            conversations = [self._to_conversation(row) for row in result.data]
            logger.info(
                "conversations_listed",
                client_profile_id=client_profile_id,
                count=len(conversations),
            )
            return conversations
        except Exception as e:
            logger.exception(
                "conversations_list_failed",
                client_profile_id=client_profile_id,
                error=str(e),
            )
            raise

    async def list_by_user(self, user_id: str) -> list[Conversation]:
        """
        List all conversations for a user.

        Args:
            user_id: User UUID.

        Returns:
            List of conversations.
        """
        try:
            result = (
                self.supabase.table(self.table)
                .select("*")
                .eq("user_id", user_id)
                .order("started_at", desc=True)
                .execute()
            )

            conversations = [self._to_conversation(row) for row in result.data]
            logger.info("conversations_listed_by_user", user_id=user_id, count=len(conversations))
            return conversations
        except Exception as e:
            logger.exception("conversations_list_by_user_failed", user_id=user_id, error=str(e))
            raise

    async def link_to_user(
        self,
        conversation_id: str,
        user_id: str,
        client_profile_id: str,
    ) -> Conversation:
        """
        Link conversation to user and client profile after registration.

        Args:
            conversation_id: Conversation UUID.
            user_id: User UUID.
            client_profile_id: Client profile UUID.

        Returns:
            Updated conversation.
        """
        try:
            result = (
                self.supabase.table(self.table)
                .update({
                    "user_id": user_id,
                    "client_profile_id": client_profile_id,
                    "status": ConversationStatus.CONVERTED.value,
                })
                .eq("id", conversation_id)
                .execute()
            )

            logger.info(
                "conversation_linked",
                conversation_id=conversation_id,
                user_id=user_id,
                client_profile_id=client_profile_id,
            )
            return self._to_conversation(result.data[0])
        except Exception as e:
            logger.exception("conversation_link_failed", conversation_id=conversation_id, error=str(e))
            raise

    def _to_conversation(self, data: dict[str, Any]) -> Conversation:
        """Convert database row to Conversation model."""
        messages = [
            ConversationMessage(
                role=MessageRole(m["role"]),
                content=m["content"],
                timestamp=datetime.fromisoformat(m["timestamp"]),
                voice_input=m.get("voice_input", False),
            )
            for m in data.get("messages", [])
        ]

        extracted_profile = None
        if data.get("extracted_profile"):
            extracted_profile = ExtractedProfile(**data["extracted_profile"])

        return Conversation(
            id=data["id"],
            user_id=data.get("user_id"),
            client_profile_id=data.get("client_profile_id"),
            messages=messages,
            status=ConversationStatus(data["status"]),
            extracted_profile=extracted_profile,
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )
