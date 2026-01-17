'use client';

/**
 * Onboarding Page
 *
 * Pre-authentication conversational onboarding flow.
 */

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { ChatInterface } from '@/components/chat/chat-interface';
import {
  useConversationStore,
  useConversationStatus,
  useExtractedProfile,
} from '@/stores/conversation-store';
import { logger } from '@/lib/logger';

export default function OnboardingPage() {
  const router = useRouter();
  const status = useConversationStatus();
  const extractedProfile = useExtractedProfile();
  const { reset } = useConversationStore();

  // Log page view
  useEffect(() => {
    logger.info({ event: 'page_view', page: 'onboarding' });

    // Cleanup on unmount
    return () => {
      // Don't reset if navigating to register
    };
  }, []);

  const handleComplete = () => {
    logger.info({
      event: 'onboarding_complete',
      hasProfile: !!extractedProfile,
    });
  };

  const handleCreateAccount = () => {
    logger.info({ event: 'onboarding_register_click' });
    // Store conversation ID in session storage for conversion after registration
    const conversationId = useConversationStore.getState().conversationId;
    if (conversationId) {
      sessionStorage.setItem('pending_conversation_id', conversationId);
    }
    router.push('/register');
  };

  const handleStartOver = () => {
    logger.info({ event: 'onboarding_restart' });
    reset();
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">Vantage</h1>
          <a
            href="/login"
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            Already have an account? Sign in
          </a>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-4">
        <div className="h-[calc(100vh-200px)] min-h-[500px]">
          <ChatInterface onComplete={handleComplete} />
        </div>

        {/* Completion actions */}
        {status === 'completed' && (
          <div className="mt-4 bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Your profile is ready!
            </h3>
            {extractedProfile && (
              <div className="mb-4 text-sm text-gray-600">
                <p>
                  <strong>Company:</strong> {extractedProfile.company_name || 'Not provided'}
                </p>
                <p>
                  <strong>Industry:</strong> {extractedProfile.industry || 'Not provided'}
                </p>
                {extractedProfile.ideal_customer_profile && (
                  <p>
                    <strong>Ideal Customer:</strong> {extractedProfile.ideal_customer_profile}
                  </p>
                )}
              </div>
            )}
            <p className="text-gray-600 mb-4">
              Create an account to save your profile and start finding leads.
            </p>
            <div className="flex gap-4">
              <button
                onClick={handleCreateAccount}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Create Account
              </button>
              <button
                onClick={handleStartOver}
                className="px-4 py-2 text-gray-600 hover:text-gray-900"
              >
                Start Over
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
