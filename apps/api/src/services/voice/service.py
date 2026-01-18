"""Voice service combining STT and TTS functionality."""

import logging
from typing import AsyncGenerator

from src.schemas.voice import (
    SynthesisRequest,
    SynthesisResponse,
    TranscriptionResponse,
)
from src.services.voice.piper import PiperTTS, PiperTTSError, get_piper_tts
from src.services.voice.whisper import WhisperSTT, WhisperSTTError, get_whisper_stt

logger = logging.getLogger(__name__)


class VoiceServiceError(Exception):
    """Error in voice service operations."""

    pass


class VoiceService:
    """Unified voice service for STT and TTS operations.

    This service:
    - Provides speech-to-text via Whisper
    - Provides text-to-speech via Piper
    - Does NOT persist any audio data (FR61 privacy requirement)
    """

    def __init__(
        self,
        whisper_model: str = "base",
        whisper_device: str = "auto",
        piper_voice: str = "en_US-lessac-medium",
    ):
        """Initialize voice service.

        Args:
            whisper_model: Whisper model size for STT
            whisper_device: Device for Whisper (auto, cpu, cuda)
            piper_voice: Default Piper voice for TTS
        """
        self._whisper: WhisperSTT | None = None
        self._piper: PiperTTS | None = None

        self._whisper_model = whisper_model
        self._whisper_device = whisper_device
        self._piper_voice = piper_voice

    @property
    def whisper(self) -> WhisperSTT:
        """Get Whisper STT instance (lazy loaded)."""
        if self._whisper is None:
            self._whisper = get_whisper_stt(
                model_size=self._whisper_model,
                device=self._whisper_device,
            )
        return self._whisper

    @property
    def piper(self) -> PiperTTS:
        """Get Piper TTS instance (lazy loaded)."""
        if self._piper is None:
            self._piper = get_piper_tts(
                default_voice=self._piper_voice,
            )
        return self._piper

    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str | None = None,
    ) -> TranscriptionResponse:
        """Transcribe audio to text.

        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (webm, wav, mp3, etc.)
            language: Language code for transcription (auto-detect if None)

        Returns:
            TranscriptionResponse with text, confidence, duration, language

        Raises:
            VoiceServiceError: If transcription fails
        """
        try:
            logger.info(
                f"Transcribing audio: {len(audio_data)} bytes, "
                f"format={audio_format}, language={language or 'auto'}"
            )

            result = await self.whisper.transcribe(
                audio_data=audio_data,
                audio_format=audio_format,
                language=language,
            )

            logger.info(
                f"Transcription complete: '{result.text[:50]}...' "
                f"(confidence={result.confidence:.2f})"
            )
            return result

        except WhisperSTTError as e:
            logger.error(f"Transcription failed: {e}")
            raise VoiceServiceError(str(e))

    async def synthesize(
        self,
        request: SynthesisRequest,
    ) -> tuple[bytes, SynthesisResponse]:
        """Synthesize text to audio.

        Args:
            request: Synthesis request with text, voice_id, speed

        Returns:
            Tuple of (audio_bytes, metadata_response)

        Raises:
            VoiceServiceError: If synthesis fails
        """
        try:
            logger.info(
                f"Synthesizing: {len(request.text)} chars, "
                f"voice={request.voice_id}, speed={request.speed}"
            )

            audio_data = await self.piper.synthesize(
                text=request.text,
                voice_id=request.voice_id,
                speed=request.speed,
            )

            # Calculate estimated duration
            estimated_duration = self.piper._estimate_duration(
                request.text, request.speed
            )

            metadata = SynthesisResponse(
                text_length=len(request.text),
                voice_id=request.voice_id,
                estimated_duration_seconds=round(estimated_duration, 2),
            )

            logger.info(
                f"Synthesis complete: {len(audio_data)} bytes, "
                f"~{estimated_duration:.1f}s duration"
            )
            return audio_data, metadata

        except PiperTTSError as e:
            logger.error(f"Synthesis failed: {e}")
            raise VoiceServiceError(str(e))

    async def synthesize_stream(
        self,
        request: SynthesisRequest,
        chunk_size: int = 4096,
    ) -> AsyncGenerator[bytes, None]:
        """Synthesize text and stream audio chunks.

        Args:
            request: Synthesis request
            chunk_size: Size of each chunk in bytes

        Yields:
            Audio data chunks

        Raises:
            VoiceServiceError: If synthesis fails
        """
        try:
            async for chunk in self.piper.synthesize_stream(
                text=request.text,
                voice_id=request.voice_id,
                speed=request.speed,
                chunk_size=chunk_size,
            ):
                yield chunk

        except PiperTTSError as e:
            logger.error(f"Streaming synthesis failed: {e}")
            raise VoiceServiceError(str(e))


# Singleton instance
_voice_service: VoiceService | None = None


def get_voice_service(
    whisper_model: str = "base",
    whisper_device: str = "auto",
    piper_voice: str = "en_US-lessac-medium",
) -> VoiceService:
    """Get or create VoiceService instance.

    Args:
        whisper_model: Whisper model size
        whisper_device: Device for Whisper
        piper_voice: Default Piper voice

    Returns:
        VoiceService instance
    """
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService(
            whisper_model=whisper_model,
            whisper_device=whisper_device,
            piper_voice=piper_voice,
        )
    return _voice_service
