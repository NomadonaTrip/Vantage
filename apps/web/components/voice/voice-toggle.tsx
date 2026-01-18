"use client";

import { useVoiceStore } from "@/stores/voice-store";

interface VoiceToggleProps {
  className?: string;
  showLabel?: boolean;
}

export function VoiceToggle({ className = "", showLabel = true }: VoiceToggleProps) {
  const { voiceEnabled, toggleVoiceEnabled } = useVoiceStore();

  return (
    <button
      onClick={toggleVoiceEnabled}
      className={`
        inline-flex items-center gap-2 px-3 py-1.5 rounded-full
        transition-all duration-200
        ${
          voiceEnabled
            ? "bg-blue-500 text-white hover:bg-blue-600"
            : "bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
        }
        ${className}
      `}
      title={voiceEnabled ? "Disable voice mode" : "Enable voice mode"}
      aria-pressed={voiceEnabled}
      aria-label={voiceEnabled ? "Voice mode enabled" : "Voice mode disabled"}
    >
      {/* Microphone Icon */}
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
        {voiceEnabled ? (
          <>
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="22" />
          </>
        ) : (
          <>
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="22" />
            <line x1="2" y1="2" x2="22" y2="22" className="text-current" />
          </>
        )}
      </svg>

      {showLabel && (
        <span className="text-sm font-medium">
          {voiceEnabled ? "Voice On" : "Voice Off"}
        </span>
      )}

      {/* Active indicator dot */}
      {voiceEnabled && (
        <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
      )}
    </button>
  );
}
