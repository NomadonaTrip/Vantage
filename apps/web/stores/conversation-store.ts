/**
 * Conversation state management using Zustand.
 *
 * Manages conversation state for onboarding flow.
 * Ephemeral - not persisted to localStorage.
 */

import { create } from 'zustand';
import { logger } from '@/lib/logger';

interface ConversationMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  voice_input?: boolean;
}

interface ExtractedProfile {
  company_name: string | null;
  industry: string | null;
  ideal_customer_profile: string | null;
  services: string[];
  additional_context: string | null;
}

interface ConversationState {
  conversationId: string | null;
  messages: ConversationMessage[];
  status: 'idle' | 'in_progress' | 'completed' | 'converted';
  isLoading: boolean;
  error: string | null;
  extractedProfile: ExtractedProfile | null;
}

interface ConversationActions {
  startConversation: () => Promise<void>;
  sendMessage: (content: string, voiceInput?: boolean) => Promise<void>;
  reset: () => void;
  setError: (error: string | null) => void;
}

type ConversationStore = ConversationState & ConversationActions;

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const initialState: ConversationState = {
  conversationId: null,
  messages: [],
  status: 'idle',
  isLoading: false,
  error: null,
  extractedProfile: null,
};

export const useConversationStore = create<ConversationStore>()((set, get) => ({
  ...initialState,

  startConversation: async () => {
    set({ isLoading: true, error: null });

    try {
      logger.info({ event: 'start_conversation_request' });

      const response = await fetch(`${API_URL}/v1/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to start conversation');
      }

      const data = await response.json();

      logger.info({ event: 'conversation_started', conversationId: data.id });

      set({
        conversationId: data.id,
        messages: data.messages.map((m: any) => ({
          id: crypto.randomUUID(),
          ...m,
        })),
        status: 'in_progress',
        isLoading: false,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start conversation';
      logger.error({ event: 'start_conversation_error', error: message });
      set({ error: message, isLoading: false });
    }
  },

  sendMessage: async (content: string, voiceInput = false) => {
    const { conversationId, messages } = get();

    if (!conversationId) {
      set({ error: 'No active conversation' });
      return;
    }

    // Optimistically add user message
    const userMessage: ConversationMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
      voice_input: voiceInput,
    };

    set({
      messages: [...messages, userMessage],
      isLoading: true,
      error: null,
    });

    try {
      logger.info({ event: 'send_message_request', conversationId });

      const response = await fetch(`${API_URL}/v1/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          voice_input: voiceInput,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();

      logger.info({
        event: 'message_sent',
        conversationId,
        isComplete: data.conversation_complete,
      });

      // Add assistant response
      const assistantMessage: ConversationMessage = {
        id: data.id,
        role: data.role,
        content: data.content,
        timestamp: data.timestamp,
      };

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        status: data.conversation_complete ? 'completed' : 'in_progress',
        isLoading: false,
        extractedProfile: data.extracted_profile || null,
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to send message';
      logger.error({ event: 'send_message_error', conversationId, error: message });
      set({ error: message, isLoading: false });
    }
  },

  reset: () => {
    logger.info({ event: 'conversation_reset' });
    set(initialState);
  },

  setError: (error) => set({ error }),
}));

// Selector hooks
export const useConversationMessages = () => useConversationStore((state) => state.messages);
export const useConversationStatus = () => useConversationStore((state) => state.status);
export const useConversationLoading = () => useConversationStore((state) => state.isLoading);
export const useExtractedProfile = () => useConversationStore((state) => state.extractedProfile);
