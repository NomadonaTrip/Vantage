"""Piper TTS (Text-to-Speech) integration."""

import io
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


class PiperTTSError(Exception):
    """Error during Piper synthesis."""

    pass


class PiperTTS:
    """Text-to-Speech service using Piper.

    Piper is a fast, local neural TTS system.
    Audio is streamed and NOT persisted (FR61 privacy requirement).
    """

    # Default voices available in Piper
    DEFAULT_VOICES = {
        "en_US-lessac-medium": "en_US-lessac-medium",
        "en_US-amy-medium": "en_US-amy-medium",
        "en_GB-alba-medium": "en_GB-alba-medium",
    }

    # Average speaking rate (words per minute / 60 = words per second)
    # Average ~150 WPM = 2.5 words/second
    WORDS_PER_SECOND = 2.5

    def __init__(
        self,
        default_voice: str = "en_US-lessac-medium",
        sample_rate: int = 22050,
    ):
        """Initialize Piper TTS.

        Args:
            default_voice: Default voice model to use
            sample_rate: Audio sample rate (22050 Hz is Piper default)
        """
        self.default_voice = default_voice
        self.sample_rate = sample_rate
        self._piper_available: bool | None = None

    def _check_piper_available(self) -> bool:
        """Check if Piper is available."""
        if self._piper_available is None:
            try:
                result = subprocess.run(
                    ["piper", "--help"],
                    capture_output=True,
                    timeout=5,
                )
                self._piper_available = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self._piper_available = False
                logger.warning(
                    "Piper TTS not found. Install with: "
                    "pip install piper-tts or download from "
                    "https://github.com/rhasspy/piper"
                )
        return self._piper_available

    def _estimate_duration(self, text: str, speed: float = 1.0) -> float:
        """Estimate audio duration based on text length.

        Args:
            text: Text to synthesize
            speed: Speed multiplier

        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        base_duration = word_count / self.WORDS_PER_SECOND
        return base_duration / speed

    async def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        speed: float = 1.0,
    ) -> bytes:
        """Synthesize text to audio.

        Args:
            text: Text to synthesize
            voice_id: Voice model to use (default if None)
            speed: Speech rate multiplier (0.5-2.0)

        Returns:
            Audio data as WAV bytes

        Raises:
            PiperTTSError: If synthesis fails
        """
        if not text or not text.strip():
            raise PiperTTSError("Empty text provided")

        voice = voice_id or self.default_voice
        speed = max(0.5, min(2.0, speed))

        # Check if Piper is available
        if not self._check_piper_available():
            # Return mock audio for development/testing
            logger.warning("Piper not available, returning mock audio")
            return self._generate_mock_audio(text)

        try:
            # Create temp file for output (deleted immediately after reading)
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False,
            ) as temp_file:
                output_path = temp_file.name

            # Run Piper
            # piper --model <voice> --output_file <path> <<< "text"
            logger.debug(f"Synthesizing: {len(text)} chars, voice={voice}, speed={speed}")

            # Piper expects text on stdin
            result = subprocess.run(
                [
                    "piper",
                    "--model", voice,
                    "--output_file", output_path,
                    "--length_scale", str(1.0 / speed),  # Piper uses inverse for speed
                ],
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=60,  # 60 second timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr.decode("utf-8", errors="replace")
                raise PiperTTSError(f"Piper synthesis failed: {error_msg}")

            # Read output file
            output_file = Path(output_path)
            if not output_file.exists():
                raise PiperTTSError("Piper did not produce output file")

            audio_data = output_file.read_bytes()

            # Clean up immediately (FR61 - no audio persistence)
            output_file.unlink(missing_ok=True)

            logger.debug(f"Synthesis complete: {len(audio_data)} bytes")
            return audio_data

        except PiperTTSError:
            raise
        except subprocess.TimeoutExpired:
            raise PiperTTSError("Synthesis timed out")
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            raise PiperTTSError(f"Synthesis failed: {e}")

    async def synthesize_stream(
        self,
        text: str,
        voice_id: str | None = None,
        speed: float = 1.0,
        chunk_size: int = 4096,
    ) -> AsyncGenerator[bytes, None]:
        """Synthesize text and stream audio chunks.

        Args:
            text: Text to synthesize
            voice_id: Voice model to use
            speed: Speech rate multiplier
            chunk_size: Size of each chunk in bytes

        Yields:
            Audio data chunks

        Raises:
            PiperTTSError: If synthesis fails
        """
        # For now, synthesize fully then stream chunks
        # Future optimization: true streaming synthesis
        audio_data = await self.synthesize(text, voice_id, speed)

        # Stream in chunks
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]

    def _generate_mock_audio(self, text: str) -> bytes:
        """Generate mock WAV audio for testing when Piper unavailable.

        Args:
            text: Text (used for duration calculation)

        Returns:
            Silent WAV audio bytes
        """
        import struct
        import wave

        # Calculate duration based on text
        duration = self._estimate_duration(text)
        num_samples = int(self.sample_rate * duration)

        # Generate silent audio
        audio_buffer = io.BytesIO()
        with wave.open(audio_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            # Write silent samples (zeros)
            wav_file.writeframes(b"\x00\x00" * num_samples)

        return audio_buffer.getvalue()


# Singleton instance
_piper_instance: PiperTTS | None = None


def get_piper_tts(
    default_voice: str = "en_US-lessac-medium",
    sample_rate: int = 22050,
) -> PiperTTS:
    """Get or create PiperTTS instance.

    Args:
        default_voice: Default voice model
        sample_rate: Audio sample rate

    Returns:
        PiperTTS instance
    """
    global _piper_instance
    if _piper_instance is None:
        _piper_instance = PiperTTS(
            default_voice=default_voice,
            sample_rate=sample_rate,
        )
    return _piper_instance
