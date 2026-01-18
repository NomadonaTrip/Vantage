"""Tests for voice services (STT and TTS)."""

import io
import struct
import wave
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.schemas.voice import AudioFormat, SynthesisRequest, TranscriptionResponse
from src.services.voice.piper import PiperTTS, PiperTTSError
from src.services.voice.service import VoiceService, VoiceServiceError
from src.services.voice.whisper import WhisperSTT, WhisperSTTError


def create_mock_wav_audio(duration_seconds: float = 1.0, sample_rate: int = 22050) -> bytes:
    """Create mock WAV audio bytes for testing."""
    num_samples = int(sample_rate * duration_seconds)
    audio_buffer = io.BytesIO()

    with wave.open(audio_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        # Write silent samples
        wav_file.writeframes(b"\x00\x00" * num_samples)

    return audio_buffer.getvalue()


class TestWhisperSTT:
    """Tests for Whisper STT service."""

    def test_validate_format_enum(self):
        """Test format validation with AudioFormat enum."""
        whisper = WhisperSTT()
        assert whisper._validate_format(AudioFormat.WAV) == "wav"
        assert whisper._validate_format(AudioFormat.WEBM) == "webm"
        assert whisper._validate_format(AudioFormat.MP3) == "mp3"

    def test_validate_format_string(self):
        """Test format validation with string."""
        whisper = WhisperSTT()
        assert whisper._validate_format("wav") == "wav"
        assert whisper._validate_format("WAV") == "wav"
        assert whisper._validate_format(".mp3") == "mp3"

    def test_validate_format_invalid(self):
        """Test format validation rejects invalid formats."""
        whisper = WhisperSTT()
        with pytest.raises(WhisperSTTError, match="Unsupported audio format"):
            whisper._validate_format("invalid")

    @pytest.mark.asyncio
    async def test_transcribe_empty_audio(self):
        """Test transcription rejects empty audio."""
        whisper = WhisperSTT()
        with pytest.raises(WhisperSTTError, match="Empty audio data"):
            await whisper.transcribe(b"", "wav")

    @pytest.mark.asyncio
    async def test_transcribe_invalid_format(self):
        """Test transcription rejects invalid format."""
        whisper = WhisperSTT()
        audio = create_mock_wav_audio()
        with pytest.raises(WhisperSTTError, match="Unsupported audio format"):
            await whisper.transcribe(audio, "xyz")

    @pytest.mark.asyncio
    async def test_transcribe_with_mock_model(self):
        """Test transcription with mocked Whisper model."""
        whisper = WhisperSTT()

        # Mock the model
        mock_segment = MagicMock()
        mock_segment.text = "Hello world"
        mock_segment.avg_logprob = -0.2  # ~82% confidence

        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.duration = 1.5

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)

        with patch.object(whisper, "_get_model", return_value=mock_model):
            audio = create_mock_wav_audio()
            result = await whisper.transcribe(audio, "wav")

        assert result.text == "Hello world"
        assert result.language == "en"
        assert result.duration_seconds == 1.5
        assert 0 < result.confidence <= 1.0


class TestPiperTTS:
    """Tests for Piper TTS service."""

    def test_estimate_duration(self):
        """Test duration estimation."""
        piper = PiperTTS()
        # ~2.5 words/second
        duration = piper._estimate_duration("Hello world how are you", speed=1.0)
        assert 1.5 < duration < 2.5  # 5 words / 2.5 WPS = 2 seconds

    def test_estimate_duration_with_speed(self):
        """Test duration estimation with speed multiplier."""
        piper = PiperTTS()
        base_duration = piper._estimate_duration("Hello world")
        fast_duration = piper._estimate_duration("Hello world", speed=2.0)
        assert fast_duration < base_duration

    @pytest.mark.asyncio
    async def test_synthesize_empty_text(self):
        """Test synthesis rejects empty text."""
        piper = PiperTTS()
        with pytest.raises(PiperTTSError, match="Empty text"):
            await piper.synthesize("")

    @pytest.mark.asyncio
    async def test_synthesize_mock_audio(self):
        """Test synthesis returns mock audio when Piper unavailable."""
        piper = PiperTTS()
        piper._piper_available = False  # Force mock mode

        audio = await piper.synthesize("Hello world")

        # Should return valid WAV audio
        assert len(audio) > 0
        # Check WAV header
        assert audio[:4] == b"RIFF"

    def test_generate_mock_audio(self):
        """Test mock audio generation."""
        piper = PiperTTS()
        audio = piper._generate_mock_audio("Test text")

        # Should be valid WAV
        assert audio[:4] == b"RIFF"

        # Parse and verify WAV properties
        audio_buffer = io.BytesIO(audio)
        with wave.open(audio_buffer, "rb") as wav_file:
            assert wav_file.getnchannels() == 1
            assert wav_file.getsampwidth() == 2
            assert wav_file.getframerate() == piper.sample_rate


class TestVoiceService:
    """Tests for unified VoiceService."""

    @pytest.mark.asyncio
    async def test_transcribe_delegates_to_whisper(self):
        """Test transcribe method calls Whisper."""
        service = VoiceService()

        mock_response = TranscriptionResponse(
            text="Hello",
            confidence=0.95,
            duration_seconds=1.0,
            language="en",
        )

        with patch.object(
            service, "whisper", MagicMock(transcribe=AsyncMock(return_value=mock_response))
        ):
            result = await service.transcribe(b"audio", "wav")

        assert result.text == "Hello"
        assert result.confidence == 0.95

    @pytest.mark.asyncio
    async def test_synthesize_delegates_to_piper(self):
        """Test synthesize method calls Piper."""
        service = VoiceService()

        mock_audio = create_mock_wav_audio()

        with patch.object(
            service, "piper", MagicMock(
                synthesize=AsyncMock(return_value=mock_audio),
                _estimate_duration=MagicMock(return_value=1.5),
            )
        ):
            request = SynthesisRequest(text="Hello world")
            audio, metadata = await service.synthesize(request)

        assert len(audio) > 0
        assert metadata.text_length == len(request.text)

    @pytest.mark.asyncio
    async def test_transcribe_error_handling(self):
        """Test transcribe wraps Whisper errors."""
        service = VoiceService()

        mock_whisper = MagicMock()
        mock_whisper.transcribe = AsyncMock(
            side_effect=WhisperSTTError("Model failed")
        )

        with patch.object(service, "_whisper", mock_whisper):
            service._whisper = mock_whisper
            with pytest.raises(VoiceServiceError, match="Model failed"):
                await service.transcribe(b"audio", "wav")

    @pytest.mark.asyncio
    async def test_synthesize_error_handling(self):
        """Test synthesize wraps Piper errors."""
        service = VoiceService()

        mock_piper = MagicMock()
        mock_piper.synthesize = AsyncMock(
            side_effect=PiperTTSError("Voice not found")
        )

        with patch.object(service, "_piper", mock_piper):
            service._piper = mock_piper
            request = SynthesisRequest(text="Hello")
            with pytest.raises(VoiceServiceError, match="Voice not found"):
                await service.synthesize(request)

    @pytest.mark.asyncio
    async def test_synthesize_stream(self):
        """Test streaming synthesis."""
        service = VoiceService()

        async def mock_stream(*args, **kwargs):
            yield b"chunk1"
            yield b"chunk2"

        with patch.object(
            service, "piper", MagicMock(synthesize_stream=mock_stream)
        ):
            request = SynthesisRequest(text="Hello world")
            chunks = [chunk async for chunk in service.synthesize_stream(request)]

        assert len(chunks) == 2
        assert chunks[0] == b"chunk1"
