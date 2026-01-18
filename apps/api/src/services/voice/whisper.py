"""Whisper STT (Speech-to-Text) integration using faster-whisper."""

import io
import logging
import tempfile
from pathlib import Path

from src.schemas.voice import AudioFormat, TranscriptionResponse

logger = logging.getLogger(__name__)


class WhisperSTTError(Exception):
    """Error during Whisper transcription."""

    pass


class WhisperSTT:
    """Speech-to-Text service using faster-whisper."""

    SUPPORTED_FORMATS = {
        AudioFormat.WEBM: "webm",
        AudioFormat.WAV: "wav",
        AudioFormat.MP3: "mp3",
        AudioFormat.OGG: "ogg",
        AudioFormat.FLAC: "flac",
    }

    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: str = "auto",
    ):
        """Initialize Whisper STT.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v3)
            device: Device to use (auto, cpu, cuda)
            compute_type: Compute type (auto, int8, float16, float32)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _get_model(self):
        """Lazy load the Whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel

                logger.info(
                    f"Loading Whisper model: {self.model_size} "
                    f"(device={self.device}, compute_type={self.compute_type})"
                )
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                )
                logger.info("Whisper model loaded successfully")
            except ImportError:
                raise WhisperSTTError(
                    "faster-whisper not installed. "
                    "Install with: uv pip install faster-whisper"
                )
            except Exception as e:
                raise WhisperSTTError(f"Failed to load Whisper model: {e}")
        return self._model

    def _validate_format(self, audio_format: str | AudioFormat) -> str:
        """Validate and normalize audio format.

        Args:
            audio_format: Audio format string or enum

        Returns:
            Normalized format string

        Raises:
            WhisperSTTError: If format not supported
        """
        if isinstance(audio_format, AudioFormat):
            return self.SUPPORTED_FORMATS[audio_format]

        format_lower = audio_format.lower().strip(".")
        valid_formats = list(self.SUPPORTED_FORMATS.values())

        if format_lower not in valid_formats:
            raise WhisperSTTError(
                f"Unsupported audio format: {audio_format}. "
                f"Supported formats: {valid_formats}"
            )
        return format_lower

    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str | AudioFormat,
        language: str | None = None,
    ) -> TranscriptionResponse:
        """Transcribe audio to text.

        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (webm, wav, mp3, etc.)
            language: Language code (e.g., 'en', 'es'). Auto-detect if None.

        Returns:
            TranscriptionResponse with text, confidence, duration, and language

        Raises:
            WhisperSTTError: If transcription fails
        """
        if not audio_data:
            raise WhisperSTTError("Empty audio data provided")

        # Validate format
        normalized_format = self._validate_format(audio_format)

        # Get model (lazy loaded)
        model = self._get_model()

        # Write audio to temp file (faster-whisper requires file path)
        # Note: Audio is deleted after processing (FR61 privacy requirement)
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=f".{normalized_format}",
                delete=False,
            ) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name

            # Transcribe
            logger.debug(f"Transcribing audio: {len(audio_data)} bytes, format={normalized_format}")

            segments, info = model.transcribe(
                temp_path,
                language=language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                ),
            )

            # Collect segments and calculate confidence
            text_parts = []
            total_confidence = 0.0
            segment_count = 0

            for segment in segments:
                text_parts.append(segment.text.strip())
                # Average log probability -> confidence approximation
                if segment.avg_logprob is not None:
                    # Convert log probability to confidence (0-1 range)
                    import math
                    confidence = math.exp(segment.avg_logprob)
                    total_confidence += confidence
                    segment_count += 1

            full_text = " ".join(text_parts).strip()

            # Calculate average confidence
            avg_confidence = (
                total_confidence / segment_count if segment_count > 0 else 0.8
            )
            # Clamp to valid range
            avg_confidence = max(0.0, min(1.0, avg_confidence))

            detected_language = info.language if info.language else "en"

            logger.debug(
                f"Transcription complete: {len(full_text)} chars, "
                f"confidence={avg_confidence:.2f}, language={detected_language}"
            )

            return TranscriptionResponse(
                text=full_text,
                confidence=round(avg_confidence, 3),
                duration_seconds=round(info.duration, 2),
                language=detected_language,
            )

        except WhisperSTTError:
            raise
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise WhisperSTTError(f"Transcription failed: {e}")
        finally:
            # Clean up temp file (FR61 - no audio persistence)
            if temp_file:
                try:
                    Path(temp_path).unlink(missing_ok=True)
                except Exception:
                    pass


# Singleton instance
_whisper_instance: WhisperSTT | None = None


def get_whisper_stt(
    model_size: str = "base",
    device: str = "auto",
    compute_type: str = "auto",
) -> WhisperSTT:
    """Get or create WhisperSTT instance.

    Args:
        model_size: Whisper model size
        device: Device to use
        compute_type: Compute type

    Returns:
        WhisperSTT instance
    """
    global _whisper_instance
    if _whisper_instance is None:
        _whisper_instance = WhisperSTT(
            model_size=model_size,
            device=device,
            compute_type=compute_type,
        )
    return _whisper_instance
