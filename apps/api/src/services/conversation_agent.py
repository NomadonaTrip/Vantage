"""Conversation Agent for onboarding dialogue orchestration."""

import json
from datetime import datetime

from supabase import Client

from src.repositories.conversation import ConversationRepository
from src.schemas.conversation import (
    Conversation,
    ConversationMessage,
    ConversationStatus,
    ExtractedProfile,
    MessageRole,
)
from src.services.llm_service import LLMService
from src.utils.logging import get_logger

logger = get_logger(__name__)

# System prompt for the onboarding conversation
ONBOARDING_SYSTEM_PROMPT = """You are a friendly assistant helping a user set up their lead generation profile for Vantage.

Your goal is to gather the following information through natural conversation:
1. Company name
2. Industry
3. Ideal customer profile (who they want to work with)
4. Services they offer
5. Any additional context about their business

Guidelines:
- Be conversational and friendly
- Ask one or two questions at a time
- Acknowledge their responses before asking more
- If they give vague answers, ask clarifying questions
- When you have enough information, ask "Is there anything else you'd like me to know?"
- Keep responses concise (2-3 sentences max)

Do NOT:
- Mention that you're an AI or assistant
- Provide technical details about how the system works
- Ask all questions at once
- Be overly formal"""

# Prompt for profile extraction
EXTRACTION_SYSTEM_PROMPT = """Based on the conversation history, extract the following information in JSON format:
{
  "company_name": "extracted company name or null",
  "industry": "extracted industry or null",
  "ideal_customer_profile": "description of their ideal customer or null",
  "services": ["list", "of", "services"],
  "additional_context": "any other relevant information or null"
}

Only include information explicitly mentioned. Use null for missing fields.
Return ONLY the JSON object, no other text."""


class ConversationAgent:
    """Agent for managing onboarding conversations with LLM."""

    def __init__(self, supabase: Client, llm_service: LLMService | None = None) -> None:
        """
        Initialize conversation agent.

        Args:
            supabase: Supabase client for database operations.
            llm_service: LLM service for generating responses.
        """
        self.repository = ConversationRepository(supabase)
        self.llm = llm_service or LLMService()

    async def start_conversation(self) -> Conversation:
        """
        Start a new onboarding conversation.

        Returns:
            New conversation with initial greeting.
        """
        logger.info("starting_conversation")

        # Generate initial greeting
        messages = [
            {"role": "system", "content": ONBOARDING_SYSTEM_PROMPT},
            {"role": "user", "content": "Start the conversation with a brief greeting and ask about their company."},
        ]

        greeting = await self.llm.generate(messages)

        # Create conversation with greeting
        initial_message = ConversationMessage(
            role=MessageRole.ASSISTANT,
            content=greeting,
            timestamp=datetime.utcnow(),
        )

        conversation = await self.repository.create(initial_message)
        logger.info("conversation_started", conversation_id=conversation.id)

        return conversation

    async def process_message(
        self,
        conversation_id: str,
        user_message: str,
        voice_input: bool = False,
    ) -> tuple[Conversation, ConversationMessage, bool]:
        """
        Process a user message and generate agent response.

        Args:
            conversation_id: Conversation UUID.
            user_message: User's message content.
            voice_input: Whether the message was spoken.

        Returns:
            Tuple of (updated conversation, agent response message, is_complete flag).
        """
        logger.info("processing_message", conversation_id=conversation_id)

        # Get conversation
        conversation = await self.repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if conversation.status != ConversationStatus.IN_PROGRESS:
            raise ValueError(f"Conversation {conversation_id} is not in progress")

        # Add user message
        user_msg = ConversationMessage(
            role=MessageRole.USER,
            content=user_message,
            timestamp=datetime.utcnow(),
            voice_input=voice_input,
        )
        conversation = await self.repository.add_message(conversation_id, user_msg)

        # Build message history for LLM
        llm_messages = [{"role": "system", "content": ONBOARDING_SYSTEM_PROMPT}]
        for msg in conversation.messages:
            llm_messages.append({
                "role": msg.role.value,
                "content": msg.content,
            })

        # Generate response
        response_text = await self.llm.generate(llm_messages)

        # Check if conversation should complete
        is_complete = self._should_conclude(user_message, response_text)

        # Add agent response
        agent_msg = ConversationMessage(
            role=MessageRole.ASSISTANT,
            content=response_text,
            timestamp=datetime.utcnow(),
        )
        conversation = await self.repository.add_message(conversation_id, agent_msg)

        # If complete, extract profile
        if is_complete:
            extracted = await self.extract_profile(conversation_id)
            conversation = await self.repository.update_status(
                conversation_id,
                ConversationStatus.COMPLETED,
                extracted,
            )

        logger.info(
            "message_processed",
            conversation_id=conversation_id,
            is_complete=is_complete,
        )

        return conversation, agent_msg, is_complete

    async def extract_profile(self, conversation_id: str) -> ExtractedProfile:
        """
        Extract profile information from conversation history.

        Args:
            conversation_id: Conversation UUID.

        Returns:
            Extracted profile data.
        """
        logger.info("extracting_profile", conversation_id=conversation_id)

        conversation = await self.repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Build conversation text for extraction
        conversation_text = "\n".join(
            f"{msg.role.value}: {msg.content}" for msg in conversation.messages
        )

        # Ask LLM to extract profile
        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Conversation:\n{conversation_text}"},
        ]

        response = await self.llm.generate(messages)

        # Parse JSON response
        try:
            # Handle markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            data = json.loads(response.strip())
            profile = ExtractedProfile(
                company_name=data.get("company_name"),
                industry=data.get("industry"),
                ideal_customer_profile=data.get("ideal_customer_profile"),
                services=data.get("services", []),
                additional_context=data.get("additional_context"),
            )
            logger.info("profile_extracted", conversation_id=conversation_id, profile=profile.model_dump())
            return profile

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(
                "profile_extraction_failed",
                conversation_id=conversation_id,
                error=str(e),
                response=response,
            )
            # Return empty profile on parse failure
            return ExtractedProfile()

    def _should_conclude(self, user_message: str, agent_response: str) -> bool:
        """
        Determine if the conversation should conclude.

        Args:
            user_message: Latest user message.
            agent_response: Agent's response.

        Returns:
            True if conversation should end.
        """
        user_lower = user_message.lower()
        response_lower = agent_response.lower()

        # Check if user indicates they're done
        done_phrases = [
            "no, that's all",
            "no that's all",
            "nothing else",
            "that's everything",
            "that is everything",
            "no more",
            "i'm done",
            "im done",
            "that's it",
            "thats it",
        ]

        if any(phrase in user_lower for phrase in done_phrases):
            return True

        # Check if agent indicates completion
        completion_phrases = [
            "create an account",
            "sign up",
            "register",
            "save your profile",
        ]

        if any(phrase in response_lower for phrase in completion_phrases):
            return True

        return False
