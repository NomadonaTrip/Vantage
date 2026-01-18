'use client';

/**
 * Conversation History Component
 *
 * Displays the conversation history for a client profile.
 */

import { useState, useEffect } from 'react';
import { logger } from '@/lib/logger';

interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  voice_input: boolean;
}

interface ExtractedProfile {
  company_name: string | null;
  industry: string | null;
  ideal_customer_profile: string | null;
  services: string[];
  additional_context: string | null;
}

interface ConversationSummary {
  id: string;
  status: string;
  message_count: number;
  extracted_profile: ExtractedProfile | null;
  started_at: string;
  completed_at: string | null;
}

interface ConversationDetail {
  id: string;
  status: string;
  messages: ConversationMessage[];
  extracted_profile: ExtractedProfile | null;
  started_at: string;
  completed_at: string | null;
}

interface ConversationHistoryProps {
  profileId: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  const authData = localStorage.getItem('auth-storage');
  if (authData) {
    try {
      const parsed = JSON.parse(authData);
      return parsed.state?.session?.access_token || null;
    } catch {
      return null;
    }
  }
  return null;
};

export function ConversationHistory({ profileId }: ConversationHistoryProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<ConversationDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch conversations
  useEffect(() => {
    const fetchConversations = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const token = getAuthToken();
        const response = await fetch(
          `${API_URL}/v1/client-profiles/${profileId}/conversations`,
          {
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch conversations');
        }

        const data = await response.json();
        setConversations(data.conversations || []);
        logger.info({
          event: 'conversations_fetched',
          profileId,
          count: data.conversations?.length || 0,
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load conversations';
        setError(message);
        logger.error({ event: 'conversations_fetch_error', profileId, error: message });
      } finally {
        setIsLoading(false);
      }
    };

    fetchConversations();
  }, [profileId]);

  // Fetch conversation detail
  const fetchConversationDetail = async (conversationId: string) => {
    try {
      const token = getAuthToken();
      const response = await fetch(
        `${API_URL}/v1/client-profiles/${profileId}/conversations/${conversationId}`,
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch conversation');
      }

      const data = await response.json();
      setSelectedConversation(data);
      logger.info({ event: 'conversation_detail_fetched', conversationId });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load conversation';
      setError(message);
      logger.error({ event: 'conversation_detail_error', conversationId, error: message });
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-4 bg-gray-200 rounded w-1/4"></div>
        <div className="space-y-2">
          <div className="h-12 bg-gray-200 rounded"></div>
          <div className="h-12 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4">
        <p className="text-sm text-red-700">{error}</p>
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <div className="text-center py-6 text-gray-500">
        <p>No conversation history found.</p>
        <p className="text-sm mt-1">
          Conversations will appear here after completing onboarding.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
        Onboarding History
      </h3>

      {/* Conversation List */}
      <div className="space-y-2">
        {conversations.map((conversation) => (
          <button
            key={conversation.id}
            onClick={() => fetchConversationDetail(conversation.id)}
            className={`w-full text-left p-4 rounded-lg border transition-colors ${
              selectedConversation?.id === conversation.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">
                  Onboarding Conversation
                </p>
                <p className="text-xs text-gray-500">
                  {formatDate(conversation.started_at)} • {conversation.message_count} messages
                </p>
              </div>
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                  conversation.status === 'converted'
                    ? 'bg-green-100 text-green-800'
                    : conversation.status === 'completed'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {conversation.status}
              </span>
            </div>
          </button>
        ))}
      </div>

      {/* Conversation Detail */}
      {selectedConversation && (
        <div className="mt-6 border-t pt-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-gray-900">
              Conversation Messages
            </h4>
            <button
              onClick={() => setSelectedConversation(null)}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Close
            </button>
          </div>

          <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
            {selectedConversation.messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  <p
                    className={`text-xs mt-1 ${
                      message.role === 'user' ? 'text-blue-200' : 'text-gray-400'
                    }`}
                  >
                    {formatDate(message.timestamp)}
                    {message.voice_input && ' • Voice'}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Extracted Profile */}
          {selectedConversation.extracted_profile && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h5 className="text-xs font-medium text-gray-500 uppercase mb-2">
                Extracted Profile
              </h5>
              <dl className="grid grid-cols-2 gap-2 text-sm">
                {selectedConversation.extracted_profile.company_name && (
                  <>
                    <dt className="text-gray-500">Company</dt>
                    <dd className="text-gray-900">
                      {selectedConversation.extracted_profile.company_name}
                    </dd>
                  </>
                )}
                {selectedConversation.extracted_profile.industry && (
                  <>
                    <dt className="text-gray-500">Industry</dt>
                    <dd className="text-gray-900">
                      {selectedConversation.extracted_profile.industry}
                    </dd>
                  </>
                )}
              </dl>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
