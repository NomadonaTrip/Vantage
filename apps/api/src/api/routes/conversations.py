"""Conversation routes for onboarding flow."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from src.api.middleware.auth import CurrentUser, OptionalUser
from src.core.supabase import get_supabase_admin_client, get_supabase_client
from src.schemas.conversation import (
    Conversation,
    ConversationMessageCreate,
    ConversationResponse,
    ConversationStatus,
    ConvertResponse,
    MessageResponse,
)
from src.services.conversation_agent import ConversationAgent
from src.services.llm_service import LLMService
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


def get_conversation_agent(
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> ConversationAgent:
    """Get conversation agent instance."""
    return ConversationAgent(supabase, LLMService())


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def start_conversation(
    agent: Annotated[ConversationAgent, Depends(get_conversation_agent)],
) -> ConversationResponse:
    """
    Start a new onboarding conversation.

    No authentication required - allows anonymous users to begin onboarding.
    """
    logger.info("start_conversation_request")

    try:
        conversation = await agent.start_conversation()

        return ConversationResponse(
            id=conversation.id,
            status=conversation.status,
            messages=conversation.messages,
            started_at=conversation.started_at,
            completed_at=conversation.completed_at,
        )
    except Exception as e:
        logger.exception("start_conversation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start conversation",
        ) from e


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    request: ConversationMessageCreate,
    agent: Annotated[ConversationAgent, Depends(get_conversation_agent)],
) -> MessageResponse:
    """
    Send a message to an active conversation.

    No authentication required during onboarding.
    Returns the agent's response and conversation status.
    """
    logger.info("send_message_request", conversation_id=conversation_id)

    try:
        conversation, response_msg, is_complete = await agent.process_message(
            conversation_id=conversation_id,
            user_message=request.content,
            voice_input=request.voice_input,
        )

        return MessageResponse(
            id=str(uuid4()),  # Message ID
            content=response_msg.content,
            role=response_msg.role,
            timestamp=response_msg.timestamp,
            conversation_status=conversation.status,
            conversation_complete=is_complete,
            extracted_profile=conversation.extracted_profile if is_complete else None,
        )

    except ValueError as e:
        logger.warning("send_message_invalid", conversation_id=conversation_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("send_message_failed", conversation_id=conversation_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message",
        ) from e


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    supabase: Annotated[Client, Depends(get_supabase_client)],
    _user: OptionalUser,
) -> ConversationResponse:
    """
    Get conversation by ID.

    Can be accessed without authentication for in-progress conversations.
    """
    logger.info("get_conversation_request", conversation_id=conversation_id)

    try:
        from src.repositories.conversation import ConversationRepository

        repo = ConversationRepository(supabase)
        conversation = await repo.get_by_id(conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        return ConversationResponse(
            id=conversation.id,
            status=conversation.status,
            messages=conversation.messages,
            started_at=conversation.started_at,
            completed_at=conversation.completed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_conversation_failed", conversation_id=conversation_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation",
        ) from e


@router.post("/{conversation_id}/convert", response_model=ConvertResponse)
async def convert_conversation(
    conversation_id: str,
    user: CurrentUser,
    supabase: Annotated[Client, Depends(get_supabase_admin_client)],
) -> ConvertResponse:
    """
    Convert a completed conversation to a client profile.

    Requires authentication. Creates a client profile from the extracted data
    and links it to the authenticated user.
    """
    logger.info("convert_conversation_request", conversation_id=conversation_id, user_id=user.id)

    try:
        from src.repositories.conversation import ConversationRepository

        repo = ConversationRepository(supabase)
        conversation = await repo.get_by_id(conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        if conversation.status not in [ConversationStatus.COMPLETED, ConversationStatus.IN_PROGRESS]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Conversation cannot be converted (status: {conversation.status.value})",
            )

        if not conversation.extracted_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation has no extracted profile",
            )

        # Create client profile
        profile_id = str(uuid4())
        profile_data = {
            "id": profile_id,
            "user_id": user.id,
            "company_name": conversation.extracted_profile.company_name or "Unknown",
            "industry": conversation.extracted_profile.industry or "Unknown",
            "ideal_client_description": conversation.extracted_profile.ideal_customer_profile,
            "keywords": [],  # Will be populated later
            "negative_keywords": [],
            "quality_threshold": 70,
            "is_active": True,
        }

        # Insert profile
        supabase.table("client_profiles").insert(profile_data).execute()

        # Link conversation to user and profile
        await repo.link_to_user(conversation_id, user.id, profile_id)

        logger.info(
            "conversation_converted",
            conversation_id=conversation_id,
            user_id=user.id,
            profile_id=profile_id,
        )

        return ConvertResponse(
            client_profile_id=profile_id,
            user_id=user.id,
            company_name=conversation.extracted_profile.company_name,
            industry=conversation.extracted_profile.industry,
            ideal_customer_profile=conversation.extracted_profile.ideal_customer_profile,
            services=conversation.extracted_profile.services,
            additional_context=conversation.extracted_profile.additional_context,
            conversation_status=ConversationStatus.CONVERTED,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("convert_conversation_failed", conversation_id=conversation_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert conversation",
        ) from e
