/**
 * Message Bubble Component
 *
 * Displays a single chat message with role-based styling.
 */

import { cn } from '@/lib/utils';

interface MessageBubbleProps {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export function MessageBubble({ role, content, timestamp }: MessageBubbleProps) {
  const isUser = role === 'user';

  return (
    <div
      className={cn(
        'flex w-full',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-[80%] rounded-lg px-4 py-2',
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-900'
        )}
      >
        <p className="text-sm whitespace-pre-wrap">{content}</p>
        {timestamp && (
          <p
            className={cn(
              'text-xs mt-1',
              isUser ? 'text-blue-200' : 'text-gray-500'
            )}
          >
            {new Date(timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        )}
      </div>
    </div>
  );
}
