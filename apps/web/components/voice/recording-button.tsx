"use client";

import { useEffect, useRef } from "react";

interface RecordingButtonProps {
  isRecording: boolean;
  isTranscribing: boolean;
  duration: number;
  hasPermission: boolean | null;
  error: string | null;
  onStartRecording: () => void;
  onStopRecording: () => void;
  disabled?: boolean;
  className?: string;
}

export function RecordingButton({
  isRecording,
  isTranscribing,
  duration,
  hasPermission,
  error,
  onStartRecording,
  onStopRecording,
  disabled = false,
  className = "",
}: RecordingButtonProps) {
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Format duration as MM:SS
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Handle click
  const handleClick = () => {
    if (disabled || isTranscribing) return;

    if (isRecording) {
      onStopRecording();
    } else {
      onStartRecording();
    }
  };

  // Button state
  const isDisabled = disabled || isTranscribing || hasPermission === false;

  return (
    <div className={`flex flex-col items-center gap-2 ${className}`}>
      <button
        ref={buttonRef}
        onClick={handleClick}
        disabled={isDisabled}
        className={`
          relative w-12 h-12 rounded-full
          flex items-center justify-center
          transition-all duration-200
          focus:outline-none focus:ring-2 focus:ring-offset-2
          ${
            isRecording
              ? "bg-red-500 hover:bg-red-600 focus:ring-red-500"
              : isTranscribing
              ? "bg-yellow-500 cursor-wait"
              : isDisabled
              ? "bg-gray-300 dark:bg-gray-600 cursor-not-allowed"
              : "bg-blue-500 hover:bg-blue-600 focus:ring-blue-500"
          }
        `}
        title={
          isRecording
            ? "Stop recording"
            : isTranscribing
            ? "Transcribing..."
            : hasPermission === false
            ? "Microphone permission denied"
            : "Start recording"
        }
        aria-label={
          isRecording
            ? "Stop recording"
            : isTranscribing
            ? "Transcribing audio"
            : "Start recording"
        }
      >
        {/* Recording animation */}
        {isRecording && (
          <span className="absolute inset-0 rounded-full bg-red-400 animate-ping opacity-30" />
        )}

        {/* Icon */}
        {isTranscribing ? (
          // Loading spinner
          <svg
            className="w-6 h-6 text-white animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        ) : isRecording ? (
          // Stop icon (square)
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="w-5 h-5 text-white"
          >
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
        ) : (
          // Microphone icon
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-5 h-5 text-white"
          >
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="22" />
          </svg>
        )}
      </button>

      {/* Status text */}
      <div className="text-center">
        {isRecording && (
          <div className="flex items-center gap-2 text-red-500">
            <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium">{formatDuration(duration)}</span>
          </div>
        )}

        {isTranscribing && (
          <span className="text-sm text-yellow-600 dark:text-yellow-400">
            Transcribing...
          </span>
        )}

        {error && (
          <span className="text-xs text-red-500 max-w-[150px] line-clamp-2">
            {error}
          </span>
        )}

        {!isRecording && !isTranscribing && !error && hasPermission === false && (
          <span className="text-xs text-red-500">
            Microphone access denied
          </span>
        )}
      </div>
    </div>
  );
}
