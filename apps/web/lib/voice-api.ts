/**
 * Voice API client for STT and TTS operations.
 * Audio is processed in real-time and NOT persisted (FR61 privacy compliance).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface TranscriptionResponse {
  text: string;
  confidence: number;
  duration_seconds: number;
  language: string;
}

export interface SynthesisRequest {
  text: string;
  voice_id?: string;
  speed?: number;
}

export class VoiceApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public detail?: string
  ) {
    super(message);
    this.name = "VoiceApiError";
  }
}

/**
 * Transcribe audio to text using Whisper.
 *
 * @param audio - Audio blob to transcribe
 * @param token - JWT authentication token
 * @param language - Optional language code (auto-detect if not specified)
 * @returns Transcription response with text, confidence, duration, and language
 * @throws VoiceApiError if transcription fails
 */
export async function transcribeAudio(
  audio: Blob,
  token: string,
  language?: string
): Promise<TranscriptionResponse> {
  const formData = new FormData();
  formData.append("audio", audio);
  if (language) {
    formData.append("language", language);
  }

  try {
    const response = await fetch(`${API_BASE}/v1/voice/transcribe`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new VoiceApiError(
        errorData.detail || `Transcription failed (${response.status})`,
        response.status,
        errorData.detail
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof VoiceApiError) {
      throw error;
    }
    throw new VoiceApiError(
      error instanceof Error ? error.message : "Transcription failed"
    );
  }
}

/**
 * Synthesize text to speech using Piper.
 *
 * @param text - Text to synthesize
 * @param token - JWT authentication token
 * @param voiceId - Optional voice model ID
 * @param speed - Optional speech rate (0.5-2.0)
 * @returns Audio blob (WAV format)
 * @throws VoiceApiError if synthesis fails
 */
export async function synthesizeText(
  text: string,
  token: string,
  voiceId?: string,
  speed?: number
): Promise<Blob> {
  const body: SynthesisRequest = {
    text,
    voice_id: voiceId || "en_US-lessac-medium",
    speed: speed || 1.0,
  };

  try {
    const response = await fetch(`${API_BASE}/v1/voice/synthesize`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new VoiceApiError(
        errorData.detail || `Synthesis failed (${response.status})`,
        response.status,
        errorData.detail
      );
    }

    return await response.blob();
  } catch (error) {
    if (error instanceof VoiceApiError) {
      throw error;
    }
    throw new VoiceApiError(
      error instanceof Error ? error.message : "Synthesis failed"
    );
  }
}

/**
 * Queue for managing audio playback of multiple messages.
 */
export class AudioPlaybackQueue {
  private queue: Blob[] = [];
  private isPlaying = false;
  private currentAudio: HTMLAudioElement | null = null;
  private onPlay?: () => void;
  private onEnded?: () => void;

  constructor(options?: { onPlay?: () => void; onEnded?: () => void }) {
    this.onPlay = options?.onPlay;
    this.onEnded = options?.onEnded;
  }

  /**
   * Add audio to the playback queue.
   */
  enqueue(audio: Blob): void {
    this.queue.push(audio);
    if (!this.isPlaying) {
      this.playNext();
    }
  }

  /**
   * Play the next audio in the queue.
   */
  private async playNext(): Promise<void> {
    if (this.queue.length === 0) {
      this.isPlaying = false;
      this.onEnded?.();
      return;
    }

    this.isPlaying = true;
    this.onPlay?.();

    const blob = this.queue.shift()!;
    const url = URL.createObjectURL(blob);

    this.currentAudio = new Audio(url);
    this.currentAudio.onended = () => {
      URL.revokeObjectURL(url);
      this.playNext();
    };
    this.currentAudio.onerror = () => {
      URL.revokeObjectURL(url);
      this.playNext();
    };

    try {
      await this.currentAudio.play();
    } catch (error) {
      console.error("Audio playback failed:", error);
      URL.revokeObjectURL(url);
      this.playNext();
    }
  }

  /**
   * Stop current playback and clear the queue.
   */
  stop(): void {
    this.queue = [];
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.src = "";
      this.currentAudio = null;
    }
    this.isPlaying = false;
    this.onEnded?.();
  }

  /**
   * Pause current playback.
   */
  pause(): void {
    this.currentAudio?.pause();
  }

  /**
   * Resume current playback.
   */
  resume(): void {
    this.currentAudio?.play();
  }

  /**
   * Check if currently playing.
   */
  get playing(): boolean {
    return this.isPlaying;
  }
}
