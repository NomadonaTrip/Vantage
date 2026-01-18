'use client';

/**
 * Search Store
 *
 * Zustand store for managing search state with polling support.
 */

import { create } from 'zustand';
import { logger } from '@/lib/logger';

// Types
export type SearchStatus = 'idle' | 'searching' | 'completed' | 'cancelled' | 'error';

export type CompanySize = 'solo' | 'small' | 'medium' | 'enterprise';

export interface ManualOverride {
  mode: 'supplement' | 'replace';
  keywords?: string;
  location?: string;
  companySize?: CompanySize;
  budgetMin?: number;
  budgetMax?: number;
  industry?: string;
}

export interface SourceStatus {
  name: string;
  status: 'pending' | 'querying' | 'success' | 'failed';
  leadsFound: number;
}

export interface IntentScoreBreakdown {
  source_hierarchy: number;
  keywords: number;
  company_size: number;
  timing_recency: number;
  budget_signals: number;
  industry_multipliers: number;
}

export interface Lead {
  id: string;
  name: string;
  company: string;
  email: string | null;
  phone: string | null;
  intent_score: number;
  score_breakdown: IntentScoreBreakdown | null;
  source: string;
  source_url: string | null;
  created_at: string;
}

export interface SearchResult {
  id: string;
  client_profile_id: string;
  status: SearchStatus;
  progress: number;
  quality_level: number;
  sources: SourceStatus[];
  leads: Lead[];
  leads_found: number;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
}

interface SearchState {
  // Current search
  currentSearch: SearchResult | null;
  status: SearchStatus;
  progress: number;
  sources: SourceStatus[];
  leads: Lead[];
  error: string | null;

  // Search parameters
  qualityLevel: number;
  manualOverride: ManualOverride | null;

  // Polling
  pollingInterval: NodeJS.Timeout | null;

  // Past searches
  searchHistory: SearchResult[];
}

interface SearchActions {
  // Search operations
  startSearch: (clientProfileId: string) => Promise<void>;
  cancelSearch: () => Promise<void>;
  pollSearchStatus: (searchId: string) => Promise<void>;

  // State setters
  setQualityLevel: (level: number) => void;
  setManualOverride: (override: ManualOverride | null) => void;
  setError: (error: string | null) => void;

  // Polling control
  startPolling: (searchId: string) => void;
  stopPolling: () => void;

  // History
  fetchSearchHistory: (clientProfileId: string) => Promise<void>;

  // Reset
  reset: () => void;
}

type SearchStore = SearchState & SearchActions;

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

const initialState: SearchState = {
  currentSearch: null,
  status: 'idle',
  progress: 0,
  sources: [],
  leads: [],
  error: null,
  qualityLevel: 0.7,
  manualOverride: null,
  pollingInterval: null,
  searchHistory: [],
};

export const useSearchStore = create<SearchStore>()((set, get) => ({
  ...initialState,

  startSearch: async (clientProfileId: string) => {
    const { qualityLevel, manualOverride, stopPolling, startPolling } = get();

    // Stop any existing polling
    stopPolling();

    set({
      status: 'searching',
      progress: 0,
      sources: [],
      leads: [],
      error: null,
      currentSearch: null,
    });

    logger.info({
      event: 'search_start',
      clientProfileId,
      qualityLevel,
      hasManualOverride: !!manualOverride,
    });

    try {
      const response = await fetchWithAuth(`${API_URL}/v1/searches`, {
        method: 'POST',
        body: JSON.stringify({
          client_profile_id: clientProfileId,
          quality_level: qualityLevel,
          manual_override: manualOverride,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to start search');
      }

      const search: SearchResult = await response.json();

      set({
        currentSearch: search,
        status: search.status,
        progress: search.progress,
        sources: search.sources || [],
        leads: search.leads || [],
      });

      logger.info({ event: 'search_started', searchId: search.id });

      // Start polling for updates
      if (search.status === 'searching') {
        startPolling(search.id);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to start search';
      logger.error({ event: 'search_start_error', error: message });
      set({
        status: 'error',
        error: message,
      });
    }
  },

  cancelSearch: async () => {
    const { currentSearch, stopPolling } = get();

    if (!currentSearch) {
      logger.warn({ event: 'cancel_search_no_active' });
      return;
    }

    stopPolling();

    logger.info({ event: 'search_cancel', searchId: currentSearch.id });

    try {
      const response = await fetchWithAuth(
        `${API_URL}/v1/searches/${currentSearch.id}/cancel`,
        { method: 'POST' }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to cancel search');
      }

      const search: SearchResult = await response.json();

      set({
        currentSearch: search,
        status: 'cancelled',
        progress: search.progress,
        sources: search.sources || [],
        leads: search.leads || [],
      });

      logger.info({
        event: 'search_cancelled',
        searchId: search.id,
        leadsFound: search.leads?.length || 0,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to cancel search';
      logger.error({ event: 'search_cancel_error', error: message });
      set({ error: message });
    }
  },

  pollSearchStatus: async (searchId: string) => {
    try {
      const response = await fetchWithAuth(`${API_URL}/v1/searches/${searchId}`);

      if (!response.ok) {
        throw new Error('Failed to fetch search status');
      }

      const search: SearchResult = await response.json();

      set({
        currentSearch: search,
        status: search.status,
        progress: search.progress,
        sources: search.sources || [],
        leads: search.leads || [],
        error: search.error_message,
      });

      // Stop polling if search is complete
      if (search.status !== 'searching') {
        get().stopPolling();
        logger.info({
          event: 'search_complete',
          searchId: search.id,
          status: search.status,
          leadsFound: search.leads?.length || 0,
        });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to poll search status';
      logger.error({ event: 'search_poll_error', searchId, error: message });
      // Don't stop polling on transient errors, but log them
    }
  },

  setQualityLevel: (level: number) => {
    const clampedLevel = Math.max(0, Math.min(1, level));
    set({ qualityLevel: clampedLevel });
  },

  setManualOverride: (override: ManualOverride | null) => {
    set({ manualOverride: override });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  startPolling: (searchId: string) => {
    const { stopPolling, pollSearchStatus } = get();

    // Clear any existing interval
    stopPolling();

    // Poll every 1.5 seconds
    const interval = setInterval(() => {
      pollSearchStatus(searchId);
    }, 1500);

    set({ pollingInterval: interval });
    logger.info({ event: 'polling_started', searchId });
  },

  stopPolling: () => {
    const { pollingInterval } = get();
    if (pollingInterval) {
      clearInterval(pollingInterval);
      set({ pollingInterval: null });
      logger.info({ event: 'polling_stopped' });
    }
  },

  fetchSearchHistory: async (clientProfileId: string) => {
    logger.info({ event: 'fetch_search_history', clientProfileId });

    try {
      const response = await fetchWithAuth(
        `${API_URL}/v1/searches?client_profile_id=${clientProfileId}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch search history');
      }

      const data = await response.json();
      set({ searchHistory: data.searches || [] });

      logger.info({
        event: 'search_history_fetched',
        count: data.searches?.length || 0,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch search history';
      logger.error({ event: 'search_history_error', error: message });
    }
  },

  reset: () => {
    const { stopPolling } = get();
    stopPolling();
    set(initialState);
    logger.info({ event: 'search_store_reset' });
  },
}));

// Selector hooks
export const useSearchStatus = () => useSearchStore((state) => state.status);
export const useSearchProgress = () => useSearchStore((state) => state.progress);
export const useSearchSources = () => useSearchStore((state) => state.sources);
export const useSearchLeads = () => useSearchStore((state) => state.leads);
export const useSearchError = () => useSearchStore((state) => state.error);
export const useQualityLevel = () => useSearchStore((state) => state.qualityLevel);
export const useManualOverride = () => useSearchStore((state) => state.manualOverride);
