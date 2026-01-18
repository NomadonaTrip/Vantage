'use client';

/**
 * Status History Component
 *
 * Shows timeline of status changes for a lead.
 */

import { StatusHistoryEntry } from '@/stores/leads-store';
import { getStatusConfig } from './status-dropdown';

interface StatusHistoryProps {
  history: StatusHistoryEntry[];
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export function StatusHistory({ history }: StatusHistoryProps) {
  if (!history || history.length === 0) {
    return (
      <div className="text-sm text-gray-500 italic">
        No status changes recorded
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-gray-900">Status History</h4>
      <div className="space-y-2">
        {history.map((entry, index) => {
          const toConfig = getStatusConfig(entry.to_status);
          const fromConfig = entry.from_status ? getStatusConfig(entry.from_status) : null;

          return (
            <div
              key={entry.id || index}
              className="flex items-start gap-2 text-xs"
            >
              <div className="flex-shrink-0 w-20 text-gray-400">
                {formatDate(entry.changed_at)}
              </div>
              <div className="flex items-center gap-1">
                {fromConfig && (
                  <>
                    <span className={`px-1.5 py-0.5 rounded ${fromConfig.color}`}>
                      {fromConfig.label}
                    </span>
                    <span className="text-gray-400">→</span>
                  </>
                )}
                <span className={`px-1.5 py-0.5 rounded ${toConfig.color}`}>
                  {toConfig.label}
                </span>
              </div>
              {entry.notes && (
                <span className="text-gray-500 italic">
                  &ldquo;{entry.notes}&rdquo;
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
