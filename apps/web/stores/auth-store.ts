/**
 * Authentication state management using Zustand.
 *
 * Manages user session, tokens, and auth actions.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { createClient } from '@/lib/supabase/client';
import { logger } from '@/lib/logger';
import type { User, Session } from '@supabase/supabase-js';

interface AuthState {
  user: User | null;
  session: Session | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

interface AuthActions {
  setUser: (user: User | null) => void;
  setSession: (session: Session | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
  clearAuth: () => void;
}

type AuthStore = AuthState & AuthActions;

const initialState: AuthState = {
  user: null,
  session: null,
  isLoading: true,
  isAuthenticated: false,
  error: null,
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      setUser: (user) =>
        set({
          user,
          isAuthenticated: !!user,
        }),

      setSession: (session) =>
        set({
          session,
          user: session?.user ?? get().user,
          isAuthenticated: !!session,
        }),

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error }),

      login: async (email, password) => {
        const supabase = createClient();
        set({ isLoading: true, error: null });

        try {
          logger.info({ event: 'login_attempt', email });

          const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password,
          });

          if (error) {
            logger.warn({ event: 'login_failed', email, error: error.message });
            throw new Error(error.message);
          }

          if (data.session && data.user) {
            logger.info({ event: 'login_success', userId: data.user.id });
            set({
              user: data.user,
              session: data.session,
              isAuthenticated: true,
              isLoading: false,
            });
          }
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Login failed';
          set({ error: message, isLoading: false });
          throw err;
        }
      },

      register: async (email, password) => {
        const supabase = createClient();
        set({ isLoading: true, error: null });

        try {
          logger.info({ event: 'register_attempt', email });

          const { data, error } = await supabase.auth.signUp({
            email,
            password,
          });

          if (error) {
            logger.warn({ event: 'register_failed', email, error: error.message });
            throw new Error(error.message);
          }

          if (data.session && data.user) {
            logger.info({ event: 'register_success', userId: data.user.id });
            set({
              user: data.user,
              session: data.session,
              isAuthenticated: true,
              isLoading: false,
            });
          } else if (data.user) {
            // Email confirmation required
            logger.info({ event: 'register_pending_confirmation', email });
            set({ isLoading: false });
            throw new Error('Please check your email to confirm your account.');
          }
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Registration failed';
          set({ error: message, isLoading: false });
          throw err;
        }
      },

      logout: async () => {
        const supabase = createClient();
        const userId = get().user?.id;

        try {
          logger.info({ event: 'logout_attempt', userId });
          await supabase.auth.signOut();
          logger.info({ event: 'logout_success', userId });
        } catch (err) {
          logger.warn({ event: 'logout_error', userId, error: String(err) });
        } finally {
          set(initialState);
          set({ isLoading: false });
        }
      },

      refreshSession: async () => {
        const supabase = createClient();

        try {
          const { data, error } = await supabase.auth.refreshSession();

          if (error) {
            logger.warn({ event: 'session_refresh_failed', error: error.message });
            get().clearAuth();
            return;
          }

          if (data.session) {
            logger.info({ event: 'session_refresh_success', userId: data.user?.id });
            set({
              session: data.session,
              user: data.user,
              isAuthenticated: true,
            });
          }
        } catch (err) {
          logger.warn({ event: 'session_refresh_error', error: String(err) });
          get().clearAuth();
        }
      },

      clearAuth: () => {
        set({
          ...initialState,
          isLoading: false,
        });
      },
    }),
    {
      name: 'vantage-auth',
      // Only persist non-sensitive data
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Selector hooks for common patterns
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useCurrentUser = () => useAuthStore((state) => state.user);
export const useAuthLoading = () => useAuthStore((state) => state.isLoading);
export const useAuthError = () => useAuthStore((state) => state.error);
