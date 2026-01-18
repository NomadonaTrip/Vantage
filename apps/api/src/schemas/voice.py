"""Voice schemas for STT and TTS."""

from enum import Enum

from pydantic import BaseModel, Field


class AudioFormat(str, Enum):
    """Supported audio formats for transcription."""

    WEBM = "webm"
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"


class TranscriptionRequest(BaseModel):
    """Request for audio transcription."""

    language: str | None = Field(
        default=None,
        description="Language code (e.g., 'en', 'es'). Auto-detect if not specified.",
    )


class TranscriptionResponse(BaseModel):
    """Response from audio transcription."""

    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score of transcription"
    )
    duration_seconds: float = Field(..., ge=0.0, description="Duration of audio in seconds")
    language: str = Field(..., description="Detected or specified language code")


class SynthesisRequest(BaseModel):
    """Request for text-to-speech synthesis."""

    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    voice_id: str = Field(
        default="en_US-lessac-medium",
        description="Voice model identifier",
    )
    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speech rate multiplier",
    )


class SynthesisResponse(BaseModel):
    """Metadata response from synthesis (audio is streamed separately)."""

    text_length: int = Field(..., description="Length of synthesized text")
    voice_id: str = Field(..., description="Voice model used")
    estimated_duration_seconds: float = Field(
        ..., description="Estimated audio duration"
    )


class VoiceError(BaseModel):
    """Error response for voice operations."""

    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
