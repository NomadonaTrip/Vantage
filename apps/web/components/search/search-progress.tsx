'use client';

/**
 * Search Progress Component
 *
 * Displays search progress with source status and cancel button.
 */

import { SourceStatus, SearchStatus } from '@/stores/search-store';

interface SearchProgressProps {
  status: SearchStatus;
  progress: number;
  sources: SourceStatus[];
  leadsFound: number;
  onCancel: () => void;
}

const getSourceStatusIcon = (status: SourceStatus['status']) => {
  switch (status) {
    case 'pending':
      return (
        <span className="h-2 w-2 rounded-full bg-gray-300" />
      );
    case 'querying':
      return (
        <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
      );
    case 'success':
      return (
        <svg className="h-4 w-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
      );
    case 'failed':
      return (
        <svg className="h-4 w-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      );
  }
};

const getSourceStatusColor = (status: SourceStatus['status']) => {
  switch (status) {
    case 'pending':
      return 'text-gray-500';
    case 'querying':
      return 'text-blue-600';
    case 'success':
      return 'text-green-600';
    case 'failed':
      return 'text-red-600';
  }
};

export function SearchProgress({
  status,
  progress,
  sources,
  leadsFound,
  onCancel,
}: SearchProgressProps) {
  const progressPercentage = Math.round(progress * 100);
  const isSearching = status === 'searching';

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
      {/* Header with progress */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            {isSearching ? 'Searching...' : 'Search Progress'}
          </h2>
          <p className="text-sm text-gray-500">
            {leadsFound} {leadsFound === 1 ? 'lead' : 'leads'} found
          </p>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold text-blue-600">{progressPercentage}%</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-3 rounded-full transition-all duration-500 ${
            isSearching ? 'bg-blue-600' : status === 'completed' ? 'bg-green-600' : 'bg-yellow-500'
          }`}
          style={{ width: `${progressPercentage}%` }}
        />
      </div>

      {/* Sources List */}
      {sources.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-700">Sources</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {sources.map((source, index) => (
              <div
                key={index}
                className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-md"
              >
                <div className="flex-shrink-0">
                  {getSourceStatusIcon(source.status)}
                </div>
                <div className="min-w-0 flex-1">
                  <p className={`text-sm truncate ${getSourceStatusColor(source.status)}`}>
                    {source.name}
                  </p>
                  {source.status === 'success' && source.leadsFound > 0 && (
                    <p className="text-xs text-gray-400">
                      {source.leadsFound} leads
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cancel Button */}
      {isSearching && (
        <div className="pt-2">
          <button
            onClick={onCancel}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg
              className="-ml-1 mr-2 h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
            Cancel Search
          </button>
          <p className="mt-1 text-xs text-gray-500">
            Cancelling will return partial results found so far.
          </p>
        </div>
      )}
    </div>
  );
}
