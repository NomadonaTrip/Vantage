'use client';

/**
 * Leads Table Component
 *
 * Sortable, paginated table displaying leads.
 */

import { Lead, LeadStatus, LeadAccuracy, SortField, SortOrder } from '@/stores/leads-store';
import { LeadRow } from './lead-row';

interface LeadsTableProps {
  leads: Lead[];
  totalCount: number;
  isLoading: boolean;
  sortField: SortField;
  sortOrder: SortOrder;
  page: number;
  pageSize: number;
  onSort: (field: SortField) => void;
  onPageChange: (page: number) => void;
  onStatusChange: (leadId: string, status: LeadStatus) => void;
  onAccuracyChange: (leadId: string, accuracy: LeadAccuracy) => void;
}

const columns: { key: SortField | 'contact' | 'accuracy'; label: string; sortable: boolean }[] = [
  { key: 'company', label: 'Name / Company', sortable: true },
  { key: 'contact', label: 'Contact', sortable: false },
  { key: 'intent_score', label: 'Score', sortable: true },
  { key: 'company', label: 'Source', sortable: false },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'accuracy', label: 'Accuracy', sortable: false },
  { key: 'created_at', label: 'Created', sortable: true },
];

export function LeadsTable({
  leads,
  totalCount,
  isLoading,
  sortField,
  sortOrder,
  page,
  pageSize,
  onSort,
  onPageChange,
  onStatusChange,
  onAccuracyChange,
}: LeadsTableProps) {
  const totalPages = Math.ceil(totalCount / pageSize);
  const startIndex = (page - 1) * pageSize + 1;
  const endIndex = Math.min(page * pageSize, totalCount);

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return (
        <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      );
    }
    if (sortOrder === 'asc') {
      return (
        <svg className="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
        </svg>
      );
    }
    return (
      <svg className="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    );
  };

  // Loading state
  if (isLoading && leads.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-sm text-gray-500">Loading leads...</p>
      </div>
    );
  }

  // Empty state
  if (!isLoading && leads.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8 text-center">
        <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-gray-100">
          <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
        <h3 className="mt-4 text-lg font-medium text-gray-900">No Leads Found</h3>
        <p className="mt-2 text-sm text-gray-500">
          Run a search to generate leads, or adjust your filters.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  scope="col"
                  className={`px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                    col.sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                  }`}
                  onClick={() => col.sortable && onSort(col.key as SortField)}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {col.sortable && getSortIcon(col.key as SortField)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {leads.map((lead) => (
              <LeadRow
                key={lead.id}
                lead={lead}
                onStatusChange={onStatusChange}
                onAccuracyChange={onAccuracyChange}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalCount > 0 && (
        <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Showing <span className="font-medium">{startIndex}</span> to{' '}
            <span className="font-medium">{endIndex}</span> of{' '}
            <span className="font-medium">{totalCount}</span> leads
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
