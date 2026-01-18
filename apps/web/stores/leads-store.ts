'use client';

/**
 * Leads Store
 *
 * Zustand store for managing leads with filtering, sorting, and pagination.
 */

import { create } from 'zustand';
import { logger } from '@/lib/logger';

// Types
export type LeadStatus = 'new' | 'contacted' | 'responded' | 'converted' | 'lost';

export type LeadAccuracy =
  | 'unverified'
  | 'verified'
  | 'email_bounced'
  | 'phone_invalid'
  | 'wrong_person'
  | 'company_mismatch';

export type SortField = 'intent_score' | 'status' | 'created_at' | 'company';
export type SortOrder = 'asc' | 'desc';

export interface StatusHistoryEntry {
  id: string;
  from_status: LeadStatus | null;
  to_status: LeadStatus;
  changed_by: string;
  changed_at: string;
  notes: string | null;
}

export interface Lead {
  id: string;
  search_id: string;
  client_profile_id: string;
  name: string;
  company: string;
  email: string | null;
  phone: string | null;
  intent_score: number;
  source: string;
  source_url: string | null;
  status: LeadStatus;
  accuracy: LeadAccuracy;
  status_history: StatusHistoryEntry[];
  created_at: string;
  updated_at: string;
}

export interface LeadsFilter {
  status: LeadStatus | 'all';
  source: string | 'all';
  searchQuery: string;
  dateFrom: string | null;
  dateTo: string | null;
}

interface LeadsState {
  leads: Lead[];
  totalCount: number;
  isLoading: boolean;
  error: string | null;

  // Pagination
  page: number;
  pageSize: number;

  // Filtering
  filters: LeadsFilter;

  // Sorting
  sortField: SortField;
  sortOrder: SortOrder;

  // Available sources for filter dropdown
  availableSources: string[];
}

interface LeadsActions {
  fetchLeads: (clientProfileId: string) => Promise<void>;
  updateLeadStatus: (leadId: string, status: LeadStatus, notes?: string) => Promise<void>;
  updateLeadAccuracy: (leadId: string, accuracy: LeadAccuracy) => Promise<void>;

  // Pagination
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;

  // Filtering
  setFilters: (filters: Partial<LeadsFilter>) => void;
  resetFilters: () => void;

  // Sorting
  setSort: (field: SortField, order?: SortOrder) => void;

  // Reset
  reset: () => void;
}

type LeadsStore = LeadsState & LeadsActions;

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

const fetchWithAuth = async (url: string, options: RequestInit = {}): Promise<Response> => {
  const token = getAuthToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  return fetch(url, {
    ...options,
    headers,
  });
};

const defaultFilters: LeadsFilter = {
  status: 'all',
  source: 'all',
  searchQuery: '',
  dateFrom: null,
  dateTo: null,
};

const initialState: LeadsState = {
  leads: [],
  totalCount: 0,
  isLoading: false,
  error: null,
  page: 1,
  pageSize: 20,
  filters: defaultFilters,
  sortField: 'created_at',
  sortOrder: 'desc',
  availableSources: [],
};

export const useLeadsStore = create<LeadsStore>()((set, get) => ({
  ...initialState,

  fetchLeads: async (clientProfileId: string) => {
    const { page, pageSize, filters, sortField, sortOrder } = get();

    set({ isLoading: true, error: null });
    logger.info({
      event: 'fetch_leads_start',
      clientProfileId,
      page,
      pageSize,
      filters,
      sortField,
      sortOrder,
    });

    try {
      const skip = (page - 1) * pageSize;
      const params = new URLSearchParams({
        client_profile_id: clientProfileId,
        skip: skip.toString(),
        limit: pageSize.toString(),
        sort_by: sortField,
        sort_order: sortOrder,
      });

      if (filters.status !== 'all') {
        params.append('status', filters.status);
      }
      if (filters.source !== 'all') {
        params.append('source', filters.source);
      }
      if (filters.searchQuery) {
        params.append('search', filters.searchQuery);
      }
      if (filters.dateFrom) {
        params.append('date_from', filters.dateFrom);
      }
      if (filters.dateTo) {
        params.append('date_to', filters.dateTo);
      }

      const response = await fetchWithAuth(`${API_URL}/v1/leads?${params.toString()}`);

      if (!response.ok) {
        throw new Error('Failed to fetch leads');
      }

      const data = await response.json();
      const leads = data.leads || [];
      const totalCount = data.total || leads.length;

      // Extract unique sources for filter dropdown
      const sources = [...new Set(leads.map((l: Lead) => l.source))] as string[];

      set({
        leads,
        totalCount,
        availableSources: sources,
        isLoading: false,
      });

      logger.info({
        event: 'fetch_leads_success',
        count: leads.length,
        total: totalCount,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch leads';
      logger.error({ event: 'fetch_leads_error', error: message });
      set({ error: message, isLoading: false });
    }
  },

  updateLeadStatus: async (leadId: string, status: LeadStatus, notes?: string) => {
    const { leads } = get();
    const leadIndex = leads.findIndex((l) => l.id === leadId);

    if (leadIndex === -1) {
      logger.warn({ event: 'update_status_lead_not_found', leadId });
      return;
    }

    const previousStatus = leads[leadIndex].status;

    // Optimistic update
    const updatedLeads = [...leads];
    updatedLeads[leadIndex] = { ...updatedLeads[leadIndex], status };
    set({ leads: updatedLeads });

    logger.info({
      event: 'update_lead_status',
      leadId,
      from: previousStatus,
      to: status,
    });

    try {
      const response = await fetchWithAuth(`${API_URL}/v1/leads/${leadId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status, notes }),
      });

      if (!response.ok) {
        throw new Error('Failed to update lead status');
      }

      const updatedLead = await response.json();

      // Update with server response (includes status history)
      const newLeads = [...get().leads];
      const idx = newLeads.findIndex((l) => l.id === leadId);
      if (idx !== -1) {
        newLeads[idx] = updatedLead;
        set({ leads: newLeads });
      }

      logger.info({ event: 'update_lead_status_success', leadId });
    } catch (error) {
      // Rollback optimistic update
      const rollbackLeads = [...get().leads];
      const idx = rollbackLeads.findIndex((l) => l.id === leadId);
      if (idx !== -1) {
        rollbackLeads[idx] = { ...rollbackLeads[idx], status: previousStatus };
        set({ leads: rollbackLeads });
      }

      const message = error instanceof Error ? error.message : 'Failed to update status';
      logger.error({ event: 'update_lead_status_error', leadId, error: message });
      set({ error: message });
    }
  },

  updateLeadAccuracy: async (leadId: string, accuracy: LeadAccuracy) => {
    const { leads } = get();
    const leadIndex = leads.findIndex((l) => l.id === leadId);

    if (leadIndex === -1) {
      logger.warn({ event: 'update_accuracy_lead_not_found', leadId });
      return;
    }

    const previousAccuracy = leads[leadIndex].accuracy;

    // Optimistic update
    const updatedLeads = [...leads];
    updatedLeads[leadIndex] = { ...updatedLeads[leadIndex], accuracy };
    set({ leads: updatedLeads });

    logger.info({
      event: 'update_lead_accuracy',
      leadId,
      from: previousAccuracy,
      to: accuracy,
    });

    try {
      const response = await fetchWithAuth(`${API_URL}/v1/leads/${leadId}`, {
        method: 'PATCH',
        body: JSON.stringify({ accuracy }),
      });

      if (!response.ok) {
        throw new Error('Failed to update lead accuracy');
      }

      const updatedLead = await response.json();

      const newLeads = [...get().leads];
      const idx = newLeads.findIndex((l) => l.id === leadId);
      if (idx !== -1) {
        newLeads[idx] = updatedLead;
        set({ leads: newLeads });
      }

      logger.info({ event: 'update_lead_accuracy_success', leadId });
    } catch (error) {
      // Rollback optimistic update
      const rollbackLeads = [...get().leads];
      const idx = rollbackLeads.findIndex((l) => l.id === leadId);
      if (idx !== -1) {
        rollbackLeads[idx] = { ...rollbackLeads[idx], accuracy: previousAccuracy };
        set({ leads: rollbackLeads });
      }

      const message = error instanceof Error ? error.message : 'Failed to update accuracy';
      logger.error({ event: 'update_lead_accuracy_error', leadId, error: message });
      set({ error: message });
    }
  },

  setPage: (page: number) => {
    set({ page: Math.max(1, page) });
  },

  setPageSize: (size: number) => {
    set({ pageSize: size, page: 1 });
  },

  setFilters: (newFilters: Partial<LeadsFilter>) => {
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
      page: 1, // Reset to first page when filters change
    }));
  },

  resetFilters: () => {
    set({ filters: defaultFilters, page: 1 });
  },

  setSort: (field: SortField, order?: SortOrder) => {
    const { sortField, sortOrder } = get();

    // If clicking same column, toggle order
    const newOrder = order ?? (sortField === field && sortOrder === 'desc' ? 'asc' : 'desc');

    set({ sortField: field, sortOrder: newOrder });
  },

  reset: () => {
    set(initialState);
    logger.info({ event: 'leads_store_reset' });
  },
}));

// Selector hooks
export const useLeads = () => useLeadsStore((state) => state.leads);
export const useLeadsTotalCount = () => useLeadsStore((state) => state.totalCount);
export const useLeadsLoading = () => useLeadsStore((state) => state.isLoading);
export const useLeadsError = () => useLeadsStore((state) => state.error);
export const useLeadsPage = () => useLeadsStore((state) => state.page);
export const useLeadsPageSize = () => useLeadsStore((state) => state.pageSize);
export const useLeadsFilters = () => useLeadsStore((state) => state.filters);
export const useLeadsSort = () =>
  useLeadsStore((state) => ({ field: state.sortField, order: state.sortOrder }));
export const useAvailableSources = () => useLeadsStore((state) => state.availableSources);
