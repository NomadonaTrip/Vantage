"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface UseAudioRecorderOptions {
  onDataAvailable?: (blob: Blob) => void;
  onError?: (error: Error) => void;
  maxDuration?: number; // Maximum recording duration in seconds
  silenceTimeout?: number; // Stop recording after this many ms of silence
}

interface UseAudioRecorderReturn {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  audioBlob: Blob | null;
  hasPermission: boolean | null;
  error: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
  pauseRecording: () => void;
  resumeRecording: () => void;
  clearRecording: () => void;
}

export function useAudioRecorder(
  options: UseAudioRecorderOptions = {}
): UseAudioRecorderReturn {
  const {
    onDataAvailable,
    onError,
    maxDuration = 60, // Default 60 seconds max
    silenceTimeout = 3000, // Default 3 seconds of silence
  } = options;

  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [duration, setDuration] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  // Check permission on mount
  useEffect(() => {
    async function checkPermission() {
      try {
        const result = await navigator.permissions.query({
          name: "microphone" as PermissionName,
        });
        setHasPermission(result.state === "granted");
        result.onchange = () => {
          setHasPermission(result.state === "granted");
        };
      } catch {
        // Permission API not supported, will check on first use
        setHasPermission(null);
      }
    }
    checkPermission();
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      chunksRef.current = [];

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100,
        },
      });

      streamRef.current = stream;
      setHasPermission(true);

      // Determine best supported MIME type
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "audio/mp4";

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000,
      });

      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        setAudioBlob(blob);
        onDataAvailable?.(blob);

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.onerror = (event) => {
        const err = new Error("Recording failed");
        setError(err.message);
        onError?.(err);
      };

      // Start recording with 100ms time slices
      mediaRecorder.start(100);
      startTimeRef.current = Date.now();
      setIsRecording(true);
      setIsPaused(false);
      setDuration(0);

      // Start duration timer
      timerRef.current = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
        setDuration(elapsed);

        // Check max duration
        if (elapsed >= maxDuration) {
          stopRecording();
        }
      }, 100);
    } catch (err) {
      const error =
        err instanceof Error ? err : new Error("Failed to start recording");

      if (error.name === "NotAllowedError") {
        setError("Microphone access denied. Please enable microphone permission.");
        setHasPermission(false);
      } else if (error.name === "NotFoundError") {
        setError("No microphone found. Please connect a microphone.");
      } else {
        setError(error.message);
      }

      onError?.(error);
    }
  }, [maxDuration, onDataAvailable, onError]);

  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      if (mediaRecorderRef.current && isRecording) {
        const recorder = mediaRecorderRef.current;

        // Set up one-time handler to resolve with blob
        const originalOnStop = recorder.onstop;
        recorder.onstop = (event) => {
          if (originalOnStop) {
            originalOnStop.call(recorder, event);
          }

          // Return the blob that was just created
          setTimeout(() => {
            resolve(audioBlob);
          }, 0);
        };

        recorder.stop();
        setIsRecording(false);
        setIsPaused(false);
      } else {
        resolve(null);
      }
    });
  }, [isRecording, audioBlob]);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording && !isPaused) {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  }, [isRecording, isPaused]);

  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording && isPaused) {
      mediaRecorderRef.current.resume();
      setIsPaused(false);

      // Resume timer
      const pausedDuration = duration;
      startTimeRef.current = Date.now() - pausedDuration * 1000;
      timerRef.current = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
        setDuration(elapsed);

        if (elapsed >= maxDuration) {
          stopRecording();
        }
      }, 100);
    }
  }, [isRecording, isPaused, duration, maxDuration, stopRecording]);

  const clearRecording = useCallback(() => {
    setAudioBlob(null);
    setDuration(0);
    chunksRef.current = [];
  }, []);

  return {
    isRecording,
    isPaused,
    duration,
    audioBlob,
    hasPermission,
    error,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    clearRecording,
  };
}
