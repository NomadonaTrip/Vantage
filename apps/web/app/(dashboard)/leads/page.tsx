'use client';

/**
 * Leads Page
 *
 * Lead management page with filtering, sorting, and status updates.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useClientStore, useActiveProfile } from '@/stores/client-store';
import {
  useLeadsStore,
  useLeads,
  useLeadsTotalCount,
  useLeadsLoading,
  useLeadsError,
  useLeadsPage,
  useLeadsPageSize,
  useLeadsFilters,
  useLeadsSort,
  useAvailableSources,
  SortField,
} from '@/stores/leads-store';
import { LeadsTable, LeadsFilters } from '@/components/leads';
import { logger } from '@/lib/logger';

export default function LeadsPage() {
  const router = useRouter();
  const activeProfile = useActiveProfile();
  const { fetchProfiles } = useClientStore();

  // Leads store state
  const leads = useLeads();
  const totalCount = useLeadsTotalCount();
  const isLoading = useLeadsLoading();
  const error = useLeadsError();
  const page = useLeadsPage();
  const pageSize = useLeadsPageSize();
  const filters = useLeadsFilters();
  const sort = useLeadsSort();
  const availableSources = useAvailableSources();

  // Leads store actions
  const {
    fetchLeads,
    updateLeadStatus,
    updateLeadAccuracy,
    setPage,
    setFilters,
    resetFilters,
    setSort,
  } = useLeadsStore();

  // Fetch profiles on mount
  useEffect(() => {
    fetchProfiles();
    logger.info({ event: 'page_view', page: 'leads' });
  }, [fetchProfiles]);

  // Fetch leads when profile or params change
  useEffect(() => {
    if (activeProfile) {
      fetchLeads(activeProfile.id);
    }
  }, [activeProfile, fetchLeads, page, pageSize, filters, sort.field, sort.order]);

  const handleSort = (field: SortField) => {
    setSort(field);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    // Scroll to top of table
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Leads</h1>
          {activeProfile ? (
            <p className="mt-1 text-sm text-gray-500">
              Managing leads for <span className="font-medium">{activeProfile.company_name}</span>
            </p>
          ) : (
            <p className="mt-1 text-sm text-yellow-600">
              Select a client profile to view leads
            </p>
          )}
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-gray-900">{totalCount}</p>
          <p className="text-sm text-gray-500">Total Leads</p>
        </div>
      </div>

      {/* No Profile Warning */}
      {!activeProfile && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            No active client profile selected.{' '}
            <button
              onClick={() => router.push('/clients')}
              className="font-medium underline hover:text-yellow-900"
            >
              Select a client profile
            </button>{' '}
            to view and manage leads.
          </p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Filters */}
      {activeProfile && (
        <LeadsFilters
          filters={filters}
          availableSources={availableSources}
          onChange={setFilters}
          onReset={resetFilters}
        />
      )}

      {/* Leads Table */}
      {activeProfile && (
        <LeadsTable
          leads={leads}
          totalCount={totalCount}
          isLoading={isLoading}
          sortField={sort.field}
          sortOrder={sort.order}
          page={page}
          pageSize={pageSize}
          onSort={handleSort}
          onPageChange={handlePageChange}
          onStatusChange={updateLeadStatus}
          onAccuracyChange={updateLeadAccuracy}
        />
      )}
    </div>
  );
}
