"""Conversation schemas for onboarding flow."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of the message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    """Status of the conversation."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    CONVERTED = "converted"


class ConversationMessage(BaseModel):
    """Individual message in a conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    voice_input: bool = False


class ConversationMessageCreate(BaseModel):
    """Request to create a new message."""

    content: str = Field(..., min_length=1, max_length=5000)
    voice_input: bool = False


class ConversationCreate(BaseModel):
    """Request to create a new conversation."""

    # No fields required - conversation starts empty
    pass


class ExtractedProfile(BaseModel):
    """Profile extracted from conversation."""

    company_name: str | None = None
    industry: str | None = None
    ideal_customer_profile: str | None = None
    services: list[str] = Field(default_factory=list)
    additional_context: str | None = None


class Conversation(BaseModel):
    """Full conversation model."""

    id: str
    user_id: str | None = None
    client_profile_id: str | None = None
    messages: list[ConversationMessage] = Field(default_factory=list)
    status: ConversationStatus = ConversationStatus.IN_PROGRESS
    extracted_profile: ExtractedProfile | None = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ConversationResponse(BaseModel):
    """Response for conversation operations."""

    id: str
    status: ConversationStatus
    messages: list[ConversationMessage]
    started_at: datetime
    completed_at: datetime | None = None


class MessageResponse(BaseModel):
    """Response after sending a message."""

    id: str
    content: str
    role: MessageRole
    timestamp: datetime
    conversation_status: ConversationStatus
    conversation_complete: bool = False
    extracted_profile: ExtractedProfile | None = None


class ConvertResponse(BaseModel):
    """Response after converting conversation to profile."""

    client_profile_id: str
    user_id: str
    company_name: str | None
    industry: str | None
    ideal_customer_profile: str | None
    services: list[str]
    additional_context: str | None
    conversation_status: ConversationStatus
