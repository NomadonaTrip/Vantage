"""Voice API routes for STT and TTS."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from src.api.dependencies import get_current_user
from src.schemas.voice import (
    AudioFormat,
    SynthesisRequest,
    TranscriptionResponse,
    VoiceError,
)
from src.api.middleware.rate_limit import rate_limit_voice
from src.services.voice import VoiceService, VoiceServiceError, get_voice_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

# Maximum audio file size (10MB)
MAX_AUDIO_SIZE = 10 * 1024 * 1024


def get_audio_format_from_content_type(content_type: str | None, filename: str | None) -> str:
    """Determine audio format from content type or filename.

    Args:
        content_type: MIME content type
        filename: Original filename

    Returns:
        Audio format string

    Raises:
        HTTPException: If format cannot be determined or is unsupported
    """
    # Try content type first
    content_type_map = {
        "audio/webm": "webm",
        "audio/wav": "wav",
        "audio/wave": "wav",
        "audio/x-wav": "wav",
        "audio/mp3": "mp3",
        "audio/mpeg": "mp3",
        "audio/ogg": "ogg",
        "audio/flac": "flac",
    }

    if content_type and content_type.lower() in content_type_map:
        return content_type_map[content_type.lower()]

    # Try filename extension
    if filename:
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        supported_formats = ["webm", "wav", "mp3", "ogg", "flac"]
        if ext in supported_formats:
            return ext

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unable to determine audio format. Supported formats: webm, wav, mp3, ogg, flac",
    )


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    responses={
        400: {"model": VoiceError, "description": "Invalid audio format or data"},
        401: {"description": "Unauthorized"},
        413: {"description": "Audio file too large"},
        429: {"description": "Rate limit exceeded"},
        500: {"model": VoiceError, "description": "Transcription failed"},
    },
)
async def transcribe_audio(
    current_user: Annotated[dict, Depends(get_current_user)],
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    language: str | None = Form(default=None, description="Language code (auto-detect if not specified)"),
    voice_service: VoiceService = Depends(get_voice_service),
) -> TranscriptionResponse:
    """Transcribe audio to text using Whisper.

    Accepts audio files in webm, wav, mp3, ogg, or flac format.
    Audio is processed in memory and NOT persisted (privacy compliant).
    """
    # Check rate limit (10 requests per minute)
    user_id = current_user.get("id", "unknown")
    rate_limit_voice(user_id)

    # Check file size
    audio_data = await audio.read()
    if len(audio_data) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file too large. Maximum size: {MAX_AUDIO_SIZE // (1024 * 1024)}MB",
        )

    if not audio_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio file",
        )

    # Determine format
    audio_format = get_audio_format_from_content_type(audio.content_type, audio.filename)

    logger.info(
        f"Transcribing audio for user {current_user.get('id', 'unknown')}: "
        f"{len(audio_data)} bytes, format={audio_format}"
    )

    try:
        result = await voice_service.transcribe(
            audio_data=audio_data,
            audio_format=audio_format,
            language=language,
        )
        return result
    except VoiceServiceError as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/synthesize",
    responses={
        400: {"model": VoiceError, "description": "Invalid synthesis request"},
        401: {"description": "Unauthorized"},
        429: {"description": "Rate limit exceeded"},
        500: {"model": VoiceError, "description": "Synthesis failed"},
    },
)
async def synthesize_speech(
    request: SynthesisRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    voice_service: VoiceService = Depends(get_voice_service),
) -> StreamingResponse:
    """Synthesize text to speech using Piper.

    Returns streaming audio in WAV format.
    Audio is generated on-the-fly and NOT persisted (privacy compliant).
    """
    # Check rate limit (10 requests per minute)
    user_id = current_user.get("id", "unknown")
    rate_limit_voice(user_id)

    logger.info(
        f"Synthesizing speech for user {current_user.get('id', 'unknown')}: "
        f"{len(request.text)} chars, voice={request.voice_id}"
    )

    try:
        async def audio_stream():
            async for chunk in voice_service.synthesize_stream(request):
                yield chunk

        return StreamingResponse(
            audio_stream(),
            media_type="audio/wav",
            headers={
                "Content-Disposition": 'attachment; filename="speech.wav"',
                "X-Voice-Id": request.voice_id,
            },
        )
    except VoiceServiceError as e:
        logger.error(f"Synthesis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
