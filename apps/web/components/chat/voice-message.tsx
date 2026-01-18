"use client";

/**
 * Voice-enabled Message Component
 *
 * Displays chat messages with optional TTS playback for agent responses.
 * Auto-plays synthesized audio when voice mode is enabled.
 */

import { useEffect, useRef, useState } from "react";

import { AudioPlayer } from "@/components/voice/audio-player";
import { synthesizeText, VoiceApiError } from "@/lib/voice-api";
import { useAuthStore } from "@/stores/auth-store";
import { useVoiceStore } from "@/stores/voice-store";

interface VoiceMessageProps {
  content: string;
  role: "user" | "assistant";
  timestamp?: string;
  autoSpeak?: boolean;
  className?: string;
}

export function VoiceMessage({
  content,
  role,
  timestamp,
  autoSpeak = true,
  className = "",
}: VoiceMessageProps) {
  const { session } = useAuthStore();
  const { voiceEnabled, isPlaying, setIsPlaying } = useVoiceStore();

  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasSpoken = useRef(false);

  // Auto-synthesize and play agent messages when voice mode enabled
  useEffect(() => {
    const shouldSpeak =
      voiceEnabled &&
      role === "assistant" &&
      autoSpeak &&
      session?.access_token &&
      !hasSpoken.current &&
      content.length > 0;

    if (shouldSpeak) {
      hasSpoken.current = true;
      synthesizeAndPlay();
    }
  }, [voiceEnabled, role, autoSpeak, session?.access_token, content]);

  const synthesizeAndPlay = async () => {
    if (!session?.access_token || !content) return;

    setIsSynthesizing(true);
    setError(null);

    try {
      const blob = await synthesizeText(content, session.access_token);
      setAudioBlob(blob);
    } catch (err) {
      const message =
        err instanceof VoiceApiError
          ? err.detail || err.message
          : "Failed to synthesize speech";
      setError(message);
    } finally {
      setIsSynthesizing(false);
    }
  };

  const handleManualSpeak = () => {
    if (audioBlob) {
      // Already have audio, just replay
      const audio = new Audio(URL.createObjectURL(audioBlob));
      setIsPlaying(true);
      audio.onended = () => setIsPlaying(false);
      audio.play();
    } else {
      synthesizeAndPlay();
    }
  };

  const isAssistant = role === "assistant";

  return (
    <div
      className={`
        flex ${isAssistant ? "justify-start" : "justify-end"}
        ${className}
      `}
    >
      <div
        className={`
          max-w-[80%] rounded-lg px-4 py-2
          ${
            isAssistant
              ? "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white"
              : "bg-blue-600 text-white"
          }
        `}
      >
        {/* Message content */}
        <p className="whitespace-pre-wrap">{content}</p>

        {/* Footer with timestamp and voice controls */}
        <div className="flex items-center justify-between mt-2 pt-1 border-t border-gray-200 dark:border-gray-700">
          {timestamp && (
            <span className="text-xs opacity-60">{timestamp}</span>
          )}

          {/* Voice controls for assistant messages */}
          {isAssistant && voiceEnabled && session?.access_token && (
            <div className="flex items-center gap-2 ml-auto">
              {isSynthesizing ? (
                <span className="text-xs opacity-60">Synthesizing...</span>
              ) : error ? (
                <button
                  onClick={handleManualSpeak}
                  className="text-xs text-red-500 hover:text-red-600"
                  title="Click to retry"
                >
                  Retry
                </button>
              ) : audioBlob ? (
                <AudioPlayer
                  src={audioBlob}
                  autoPlay={autoSpeak && !hasSpoken.current}
                  compact
                  onPlay={() => setIsPlaying(true)}
                  onEnded={() => setIsPlaying(false)}
                />
              ) : (
                <button
                  onClick={handleManualSpeak}
                  className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
                  title="Speak this message"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="w-4 h-4"
                  >
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                    <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                  </svg>
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
