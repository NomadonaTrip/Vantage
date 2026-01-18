"""Pydantic schemas for Vantage API."""

from src.schemas.client_profile import (
    ClientProfile,
    ClientProfileCreate,
    ClientProfileListResponse,
    ClientProfileResponse,
    ClientProfileUpdate,
    ScoringWeights,
)
from src.schemas.conversation import (
    Conversation,
    ConversationCreate,
    ConversationMessage,
    ConversationMessageCreate,
    ConversationStatus,
    ExtractedProfile,
    MessageRole,
)
from src.schemas.voice import (
    AudioFormat,
    SynthesisRequest,
    SynthesisResponse,
    TranscriptionRequest,
    TranscriptionResponse,
    VoiceError,
)

__all__ = [
    # Client Profile
    "ClientProfile",
    "ClientProfileCreate",
    "ClientProfileListResponse",
    "ClientProfileResponse",
    "ClientProfileUpdate",
    "ScoringWeights",
    # Conversation
    "Conversation",
    "ConversationCreate",
    "ConversationMessage",
    "ConversationMessageCreate",
    "ConversationStatus",
    "ExtractedProfile",
    "MessageRole",
    # Voice
    "AudioFormat",
    "SynthesisRequest",
    "SynthesisResponse",
    "TranscriptionRequest",
    "TranscriptionResponse",
    "VoiceError",
]
