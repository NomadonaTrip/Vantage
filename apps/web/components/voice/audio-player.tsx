"use client";

import { useEffect, useRef, useState } from "react";

interface AudioPlayerProps {
  src: string | Blob | null;
  autoPlay?: boolean;
  onPlay?: () => void;
  onPause?: () => void;
  onEnded?: () => void;
  onError?: (error: Error) => void;
  className?: string;
  compact?: boolean;
}

export function AudioPlayer({
  src,
  autoPlay = false,
  onPlay,
  onPause,
  onEnded,
  onError,
  className = "",
  compact = false,
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Create object URL for Blob sources
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  useEffect(() => {
    if (src instanceof Blob) {
      const url = URL.createObjectURL(src);
      setAudioUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setAudioUrl(src);
    }
  }, [src]);

  // Setup audio element event listeners
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !audioUrl) return;

    const handlePlay = () => {
      setIsPlaying(true);
      onPlay?.();
    };

    const handlePause = () => {
      setIsPlaying(false);
      onPause?.();
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
      onEnded?.();
    };

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
      setError(null);
    };

    const handleError = () => {
      const err = new Error("Failed to load audio");
      setError(err.message);
      onError?.(err);
    };

    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("error", handleError);

    // Auto-play if enabled
    if (autoPlay) {
      audio.play().catch((err) => {
        console.warn("Autoplay prevented:", err);
      });
    }

    return () => {
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("error", handleError);
    };
  }, [audioUrl, autoPlay, onPlay, onPause, onEnded, onError]);

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    if (!isFinite(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Toggle play/pause
  const togglePlayPause = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play().catch((err) => {
        console.error("Play failed:", err);
      });
    }
  };

  // Seek to position
  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;

    const time = parseFloat(e.target.value);
    audio.currentTime = time;
    setCurrentTime(time);
  };

  if (!audioUrl) {
    return null;
  }

  if (error) {
    return (
      <div className={`text-red-500 text-sm ${className}`}>
        Failed to load audio
      </div>
    );
  }

  // Compact version (just play button)
  if (compact) {
    return (
      <button
        onClick={togglePlayPause}
        className={`
          w-8 h-8 rounded-full flex items-center justify-center
          bg-blue-500 hover:bg-blue-600 text-white
          transition-colors duration-200
          ${className}
        `}
        aria-label={isPlaying ? "Pause" : "Play"}
      >
        <audio ref={audioRef} src={audioUrl} preload="metadata" />
        {isPlaying ? (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <rect x="6" y="4" width="4" height="16" />
            <rect x="14" y="4" width="4" height="16" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        )}
      </button>
    );
  }

  // Full player
  return (
    <div
      className={`
        flex items-center gap-3 p-2 rounded-lg
        bg-gray-100 dark:bg-gray-800
        ${className}
      `}
    >
      <audio ref={audioRef} src={audioUrl} preload="metadata" />

      {/* Play/Pause button */}
      <button
        onClick={togglePlayPause}
        className="w-10 h-10 rounded-full flex items-center justify-center bg-blue-500 hover:bg-blue-600 text-white transition-colors"
        aria-label={isPlaying ? "Pause" : "Play"}
      >
        {isPlaying ? (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <rect x="6" y="4" width="4" height="16" />
            <rect x="14" y="4" width="4" height="16" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        )}
      </button>

      {/* Progress bar */}
      <div className="flex-1 flex items-center gap-2">
        <span className="text-xs text-gray-500 dark:text-gray-400 w-10 text-right">
          {formatTime(currentTime)}
        </span>

        <input
          type="range"
          min="0"
          max={duration || 0}
          value={currentTime}
          onChange={handleSeek}
          className="flex-1 h-1 bg-gray-300 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer"
          style={{
            background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${
              (currentTime / (duration || 1)) * 100
            }%, #D1D5DB ${(currentTime / (duration || 1)) * 100}%, #D1D5DB 100%)`,
          }}
        />

        <span className="text-xs text-gray-500 dark:text-gray-400 w-10">
          {formatTime(duration)}
        </span>
      </div>
    </div>
  );
}
