'use client';

/**
 * Search Results Component
 *
 * Displays search results with CSV export functionality.
 */

import { Lead, SearchStatus } from '@/stores/search-store';
import { LeadCard } from './lead-card';

interface SearchResultsProps {
  leads: Lead[];
  status: SearchStatus;
  error: string | null;
  onRetry?: () => void;
}

const exportToCSV = (leads: Lead[]) => {
  const headers = ['Name', 'Company', 'Email', 'Phone', 'Intent Score', 'Source', 'Source URL'];
  const rows = leads.map((lead) => [
    lead.name,
    lead.company,
    lead.email || '',
    lead.phone || '',
    Math.round(lead.intent_score * 100).toString() + '%',
    lead.source,
    lead.source_url || '',
  ]);

  const csvContent = [
    headers.join(','),
    ...rows.map((row) =>
      row.map((cell) => `"${cell.replace(/"/g, '""')}"`).join(',')
    ),
  ].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute(
    'download',
    `leads-${new Date().toISOString().split('T')[0]}.csv`
  );
  link.style.visibility = 'hidden';

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export function SearchResults({ leads, status, error, onRetry }: SearchResultsProps) {
  const sortedLeads = [...leads].sort((a, b) => b.intent_score - a.intent_score);

  // Error State
  if (status === 'error') {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-center py-8">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
            <svg
              className="h-6 w-6 text-red-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900">Search Failed</h3>
          <p className="mt-2 text-sm text-gray-500">{error || 'An error occurred during the search.'}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
            >
              <svg
                className="-ml-1 mr-2 h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Try Again
            </button>
          )}
        </div>
      </div>
    );
  }

  // Empty State
  if (sortedLeads.length === 0 && (status === 'completed' || status === 'cancelled')) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-center py-8">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-gray-100">
            <svg
              className="h-6 w-6 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No Leads Found</h3>
          <p className="mt-2 text-sm text-gray-500">
            Try adjusting your search parameters or client profile to find more leads.
          </p>
        </div>
      </div>
    );
  }

  // Idle State
  if (status === 'idle') {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            {status === 'searching' ? 'Results (updating...)' : 'Search Results'}
          </h2>
          <p className="text-sm text-gray-500">
            {sortedLeads.length} {sortedLeads.length === 1 ? 'lead' : 'leads'} found
            {status === 'cancelled' && ' (search was cancelled)'}
          </p>
        </div>

        {/* Export Button */}
        {sortedLeads.length > 0 && (
          <button
            onClick={() => exportToCSV(sortedLeads)}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <svg
              className="-ml-0.5 mr-1.5 h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
            Export CSV
          </button>
        )}
      </div>

      {/* Results Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sortedLeads.map((lead) => (
          <LeadCard key={lead.id} lead={lead} />
        ))}
      </div>
    </div>
  );
}
