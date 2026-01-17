'use client';

/**
 * Chat Interface Component
 *
 * Main chat container with message list and input.
 */

import { useEffect } from 'react';
import { useConversationStore } from '@/stores/conversation-store';
import { MessageList } from './message-list';
import { ChatInput } from './chat-input';

interface ChatInterfaceProps {
  onComplete?: () => void;
}

export function ChatInterface({ onComplete }: ChatInterfaceProps) {
  const {
    messages,
    status,
    isLoading,
    error,
    startConversation,
    sendMessage,
    setError,
  } = useConversationStore();

  // Start conversation on mount
  useEffect(() => {
    if (status === 'idle') {
      startConversation();
    }
  }, [status, startConversation]);

  // Notify when conversation completes
  useEffect(() => {
    if (status === 'completed' && onComplete) {
      onComplete();
    }
  }, [status, onComplete]);

  const handleSend = (content: string) => {
    setError(null);
    sendMessage(content);
  };

  if (status === 'idle' && isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto" />
          <p className="mt-2 text-gray-600">Starting conversation...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-blue-600 px-4 py-3 text-white">
        <h2 className="font-semibold">Welcome to Vantage</h2>
        <p className="text-sm text-blue-100">Tell us about your business</p>
      </div>

      {/* Error display */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Messages */}
      <MessageList messages={messages} isLoading={isLoading} />

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        disabled={isLoading || status === 'completed'}
        placeholder={
          status === 'completed'
            ? 'Conversation complete! Create an account to save your profile.'
            : 'Type your message...'
        }
      />
    </div>
  );
}
