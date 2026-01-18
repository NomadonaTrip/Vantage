"use client";

/**
 * Voice-enabled Chat Input Component
 *
 * Extends chat input with voice recording and transcription capabilities.
 * Integrates with voice store for mode persistence and API for transcription.
 */

import { useState, FormEvent, KeyboardEvent, useCallback } from "react";

import { RecordingButton } from "@/components/voice/recording-button";
import { VoiceToggle } from "@/components/voice/voice-toggle";
import { useAudioRecorder } from "@/hooks/use-audio-recorder";
import { transcribeAudio, VoiceApiError } from "@/lib/voice-api";
import { useAuthStore } from "@/stores/auth-store";
import { useVoiceStore } from "@/stores/voice-store";

interface VoiceChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  showVoiceToggle?: boolean;
}

export function VoiceChatInput({
  onSend,
  disabled = false,
  placeholder = "Type a message...",
  showVoiceToggle = true,
}: VoiceChatInputProps) {
  const [message, setMessage] = useState("");
  const [transcribeError, setTranscribeError] = useState<string | null>(null);

  const { session } = useAuthStore();
  const {
    voiceEnabled,
    isTranscribing,
    setIsTranscribing,
    setError: setVoiceError,
  } = useVoiceStore();

  const {
    isRecording,
    duration,
    hasPermission,
    error: recorderError,
    startRecording,
    stopRecording,
    clearRecording,
  } = useAudioRecorder({
    maxDuration: 60, // 1 minute max
    onError: (err) => {
      setTranscribeError(err.message);
    },
  });

  // Handle form submission
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage("");
      setTranscribeError(null);
    }
  };

  // Handle Enter key
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Handle recording start
  const handleStartRecording = useCallback(async () => {
    setTranscribeError(null);
    await startRecording();
  }, [startRecording]);

  // Handle recording stop and transcription
  const handleStopRecording = useCallback(async () => {
    const blob = await stopRecording();

    if (!blob || !session?.access_token) {
      return;
    }

    // Transcribe the audio
    setIsTranscribing(true);
    setTranscribeError(null);

    try {
      const result = await transcribeAudio(blob, session.access_token);

      // Populate input with transcribed text
      if (result.text) {
        setMessage((prev) => {
          // Append to existing text with space if needed
          if (prev.trim()) {
            return prev.trim() + " " + result.text;
          }
          return result.text;
        });
      }

      clearRecording();
    } catch (error) {
      const message =
        error instanceof VoiceApiError
          ? error.detail || error.message
          : "Transcription failed";
      setTranscribeError(message);
      setVoiceError(message);
    } finally {
      setIsTranscribing(false);
    }
  }, [
    stopRecording,
    session?.access_token,
    setIsTranscribing,
    setVoiceError,
    clearRecording,
  ]);

  const isInputDisabled = disabled || isRecording || isTranscribing;
  const showRecordingButton = voiceEnabled && session?.access_token;

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-200 dark:border-gray-700 p-4">
      {/* Voice toggle header */}
      {showVoiceToggle && (
        <div className="flex items-center justify-end mb-2">
          <VoiceToggle showLabel={false} className="scale-90" />
        </div>
      )}

      <div className="flex items-end gap-2">
        {/* Recording button (when voice enabled) */}
        {showRecordingButton && (
          <RecordingButton
            isRecording={isRecording}
            isTranscribing={isTranscribing}
            duration={duration}
            hasPermission={hasPermission}
            error={recorderError || transcribeError}
            onStartRecording={handleStartRecording}
            onStopRecording={handleStopRecording}
            disabled={disabled}
            className="flex-shrink-0"
          />
        )}

        {/* Text input */}
        <div className="flex-1">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isRecording
                ? "Recording..."
                : isTranscribing
                ? "Transcribing..."
                : placeholder
            }
            disabled={isInputDisabled}
            rows={1}
            className="w-full resize-none rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
          />
          {/* Error message */}
          {transcribeError && (
            <p className="mt-1 text-xs text-red-500">{transcribeError}</p>
          )}
        </div>

        {/* Send button */}
        <button
          type="submit"
          disabled={isInputDisabled || !message.trim()}
          className="flex-shrink-0 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 dark:disabled:bg-gray-600 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>

      {/* Voice mode hint */}
      {voiceEnabled && !showRecordingButton && (
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          Sign in to use voice input
        </p>
      )}
    </form>
  );
}
