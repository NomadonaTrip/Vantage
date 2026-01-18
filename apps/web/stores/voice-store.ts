"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface VoiceState {
  // Persisted state
  voiceEnabled: boolean;

  // Transient state
  isRecording: boolean;
  isTranscribing: boolean;
  isPlaying: boolean;
  recordingDuration: number;
  error: string | null;

  // Actions
  setVoiceEnabled: (enabled: boolean) => void;
  toggleVoiceEnabled: () => void;
  setIsRecording: (recording: boolean) => void;
  setIsTranscribing: (transcribing: boolean) => void;
  setIsPlaying: (playing: boolean) => void;
  setRecordingDuration: (duration: number) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useVoiceStore = create<VoiceState>()(
  persist(
    (set) => ({
      // Initial state
      voiceEnabled: false,
      isRecording: false,
      isTranscribing: false,
      isPlaying: false,
      recordingDuration: 0,
      error: null,

      // Actions
      setVoiceEnabled: (enabled) => set({ voiceEnabled: enabled }),
      toggleVoiceEnabled: () =>
        set((state) => ({ voiceEnabled: !state.voiceEnabled })),
      setIsRecording: (recording) => set({ isRecording: recording }),
      setIsTranscribing: (transcribing) => set({ isTranscribing: transcribing }),
      setIsPlaying: (playing) => set({ isPlaying: playing }),
      setRecordingDuration: (duration) => set({ recordingDuration: duration }),
      setError: (error) => set({ error }),
      clearError: () => set({ error: null }),
    }),
    {
      name: "vantage-voice-settings",
      // Only persist voiceEnabled preference
      partialize: (state) => ({ voiceEnabled: state.voiceEnabled }),
    }
  )
);
