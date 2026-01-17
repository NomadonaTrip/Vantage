'use client';

/**
 * Client Profile Store
 *
 * Zustand store for managing client profiles.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { logger } from '@/lib/logger';

export interface ScoringWeights {
  source_hierarchy: number;
  keywords: number;
  company_size: number;
  timing_recency: number;
  budget_signals: number;
  industry_multipliers: number;
}

export interface ClientProfile {
  id: string;
  user_id: string;
  company_name: string;
  industry: string;
  ideal_customer_profile: string;
  services: string[];
  additional_context: string | null;
  scoring_weight_overrides: ScoringWeights | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClientProfileCreate {
  company_name: string;
  industry: string;
  ideal_customer_profile: string;
  services: string[];
  additional_context?: string | null;
  scoring_weight_overrides?: ScoringWeights | null;
}

export interface ClientProfileUpdate {
  company_name?: string;
  industry?: string;
  ideal_customer_profile?: string;
  services?: string[];
  additional_context?: string | null;
  scoring_weight_overrides?: ScoringWeights | null;
}

interface ClientState {
  profiles: ClientProfile[];
  activeProfile: ClientProfile | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchProfiles: () => Promise<void>;
  getProfile: (id: string) => Promise<ClientProfile | null>;
  createProfile: (data: ClientProfileCreate) => Promise<ClientProfile | null>;
  updateProfile: (id: string, data: ClientProfileUpdate) => Promise<ClientProfile | null>;
  deleteProfile: (id: string) => Promise<boolean>;
  setActiveProfile: (id: string) => Promise<ClientProfile | null>;
  setError: (error: string | null) => void;
  reset: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  // Get token from auth store or localStorage
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

export const useClientStore = create<ClientState>()(
  persist(
    (set, get) => ({
      profiles: [],
      activeProfile: null,
      isLoading: false,
      error: null,

      fetchProfiles: async () => {
        set({ isLoading: true, error: null });
        logger.info({ event: 'fetch_profiles_start' });

        try {
          const response = await fetchWithAuth(`${API_URL}/v1/client-profiles`);

          if (!response.ok) {
            throw new Error('Failed to fetch profiles');
          }

          const data = await response.json();
          const profiles = data.profiles || [];
          const activeProfile = profiles.find((p: ClientProfile) => p.is_active) || null;

          set({
            profiles,
            activeProfile,
            isLoading: false,
          });

          logger.info({ event: 'fetch_profiles_success', count: profiles.length });
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Failed to fetch profiles';
          logger.error({ event: 'fetch_profiles_error', error: message });
          set({ error: message, isLoading: false });
        }
      },

      getProfile: async (id: string) => {
        logger.info({ event: 'get_profile_start', profileId: id });

        try {
          const response = await fetchWithAuth(`${API_URL}/v1/client-profiles/${id}`);

          if (!response.ok) {
            if (response.status === 404) {
              return null;
            }
            throw new Error('Failed to get profile');
          }

          const profile = await response.json();
          logger.info({ event: 'get_profile_success', profileId: id });
          return profile;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Failed to get profile';
          logger.error({ event: 'get_profile_error', profileId: id, error: message });
          set({ error: message });
          return null;
        }
      },

      createProfile: async (data: ClientProfileCreate) => {
        set({ isLoading: true, error: null });
        logger.info({ event: 'create_profile_start', company: data.company_name });

        try {
          const response = await fetchWithAuth(`${API_URL}/v1/client-profiles`, {
            method: 'POST',
            body: JSON.stringify(data),
          });

          if (!response.ok) {
            throw new Error('Failed to create profile');
          }

          const profile = await response.json();

          // Update state
          const { profiles } = get();
          const newProfiles = [profile, ...profiles];
          const activeProfile = profile.is_active ? profile : get().activeProfile;

          set({
            profiles: newProfiles,
            activeProfile,
            isLoading: false,
          });

          logger.info({ event: 'create_profile_success', profileId: profile.id });
          return profile;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Failed to create profile';
          logger.error({ event: 'create_profile_error', error: message });
          set({ error: message, isLoading: false });
          return null;
        }
      },

      updateProfile: async (id: string, data: ClientProfileUpdate) => {
        set({ isLoading: true, error: null });
        logger.info({ event: 'update_profile_start', profileId: id });

        try {
          const response = await fetchWithAuth(`${API_URL}/v1/client-profiles/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });

          if (!response.ok) {
            if (response.status === 404) {
              throw new Error('Profile not found');
            }
            throw new Error('Failed to update profile');
          }

          const updatedProfile = await response.json();

          // Update state
          const { profiles, activeProfile } = get();
          const newProfiles = profiles.map((p) =>
            p.id === id ? updatedProfile : p
          );
          const newActiveProfile =
            activeProfile?.id === id ? updatedProfile : activeProfile;

          set({
            profiles: newProfiles,
            activeProfile: newActiveProfile,
            isLoading: false,
          });

          logger.info({ event: 'update_profile_success', profileId: id });
          return updatedProfile;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Failed to update profile';
          logger.error({ event: 'update_profile_error', profileId: id, error: message });
          set({ error: message, isLoading: false });
          return null;
        }
      },

      deleteProfile: async (id: string) => {
        set({ isLoading: true, error: null });
        logger.info({ event: 'delete_profile_start', profileId: id });

        try {
          const response = await fetchWithAuth(`${API_URL}/v1/client-profiles/${id}`, {
            method: 'DELETE',
          });

          if (!response.ok) {
            if (response.status === 404) {
              throw new Error('Profile not found');
            }
            throw new Error('Failed to delete profile');
          }

          // Update state
          const { profiles, activeProfile } = get();
          const newProfiles = profiles.filter((p) => p.id !== id);
          const newActiveProfile =
            activeProfile?.id === id
              ? newProfiles.find((p) => p.is_active) || null
              : activeProfile;

          set({
            profiles: newProfiles,
            activeProfile: newActiveProfile,
            isLoading: false,
          });

          logger.info({ event: 'delete_profile_success', profileId: id });
          return true;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Failed to delete profile';
          logger.error({ event: 'delete_profile_error', profileId: id, error: message });
          set({ error: message, isLoading: false });
          return false;
        }
      },

      setActiveProfile: async (id: string) => {
        set({ isLoading: true, error: null });
        logger.info({ event: 'set_active_profile_start', profileId: id });

        try {
          const response = await fetchWithAuth(
            `${API_URL}/v1/client-profiles/${id}/activate`,
            { method: 'POST' }
          );

          if (!response.ok) {
            if (response.status === 404) {
              throw new Error('Profile not found');
            }
            throw new Error('Failed to activate profile');
          }

          const activatedProfile = await response.json();

          // Update state - set all profiles to inactive except the activated one
          const { profiles } = get();
          const newProfiles = profiles.map((p) => ({
            ...p,
            is_active: p.id === id,
          }));

          set({
            profiles: newProfiles,
            activeProfile: activatedProfile,
            isLoading: false,
          });

          logger.info({ event: 'set_active_profile_success', profileId: id });
          return activatedProfile;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Failed to activate profile';
          logger.error({ event: 'set_active_profile_error', profileId: id, error: message });
          set({ error: message, isLoading: false });
          return null;
        }
      },

      setError: (error: string | null) => set({ error }),

      reset: () => {
        logger.info({ event: 'client_store_reset' });
        set({
          profiles: [],
          activeProfile: null,
          isLoading: false,
          error: null,
        });
      },
    }),
    {
      name: 'client-storage',
      partialize: (state) => ({
        activeProfile: state.activeProfile,
      }),
    }
  )
);

// Selector hooks for common patterns
export const useProfiles = () => useClientStore((state) => state.profiles);
export const useActiveProfile = () => useClientStore((state) => state.activeProfile);
export const useClientLoading = () => useClientStore((state) => state.isLoading);
export const useClientError = () => useClientStore((state) => state.error);
