'use client';

/**
 * Leads Filters Component
 *
 * Filter controls for the leads table.
 */

import { LeadsFilter, LeadStatus } from '@/stores/leads-store';
import { statusOptions } from './status-dropdown';

interface LeadsFiltersProps {
  filters: LeadsFilter;
  availableSources: string[];
  onChange: (filters: Partial<LeadsFilter>) => void;
  onReset: () => void;
}

export function LeadsFilters({
  filters,
  availableSources,
  onChange,
  onReset,
}: LeadsFiltersProps) {
  const hasActiveFilters =
    filters.status !== 'all' ||
    filters.source !== 'all' ||
    filters.searchQuery ||
    filters.dateFrom ||
    filters.dateTo;

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700">Filters</h3>
        {hasActiveFilters && (
          <button
            onClick={onReset}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Clear all
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {/* Search */}
        <div className="col-span-2 md:col-span-1">
          <label htmlFor="search" className="block text-xs font-medium text-gray-600 mb-1">
            Search
          </label>
          <input
            type="text"
            id="search"
            value={filters.searchQuery}
            onChange={(e) => onChange({ searchQuery: e.target.value })}
            placeholder="Name or company..."
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Status Filter */}
        <div>
          <label htmlFor="status" className="block text-xs font-medium text-gray-600 mb-1">
            Status
          </label>
          <select
            id="status"
            value={filters.status}
            onChange={(e) => onChange({ status: e.target.value as LeadStatus | 'all' })}
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">All Status</option>
            {statusOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Source Filter */}
        <div>
          <label htmlFor="source" className="block text-xs font-medium text-gray-600 mb-1">
            Source
          </label>
          <select
            id="source"
            value={filters.source}
            onChange={(e) => onChange({ source: e.target.value })}
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">All Sources</option>
            {availableSources.map((source) => (
              <option key={source} value={source}>
                {source}
              </option>
            ))}
          </select>
        </div>

        {/* Date From */}
        <div>
          <label htmlFor="dateFrom" className="block text-xs font-medium text-gray-600 mb-1">
            From Date
          </label>
          <input
            type="date"
            id="dateFrom"
            value={filters.dateFrom || ''}
            onChange={(e) => onChange({ dateFrom: e.target.value || null })}
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Date To */}
        <div>
          <label htmlFor="dateTo" className="block text-xs font-medium text-gray-600 mb-1">
            To Date
          </label>
          <input
            type="date"
            id="dateTo"
            value={filters.dateTo || ''}
            onChange={(e) => onChange({ dateTo: e.target.value || null })}
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>
    </div>
  );
}
