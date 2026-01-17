'use client';

/**
 * Authentication Provider Component.
 *
 * Initializes Supabase auth listeners and syncs auth state with Zustand store.
 */

import { useEffect, useCallback } from 'react';
import { createClient } from '@/lib/supabase/client';
import { useAuthStore } from '@/stores/auth-store';
import { logger } from '@/lib/logger';

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const { setUser, setSession, setLoading, clearAuth } = useAuthStore();

  const initializeAuth = useCallback(async () => {
    const supabase = createClient();

    try {
      // Get initial session
      const {
        data: { session },
        error,
      } = await supabase.auth.getSession();

      if (error) {
        logger.warn({ event: 'auth_init_error', error: error.message });
        clearAuth();
        return;
      }

      if (session) {
        logger.info({ event: 'auth_init_session_found', userId: session.user.id });
        setSession(session);
        setUser(session.user);
      } else {
        logger.info({ event: 'auth_init_no_session' });
        clearAuth();
      }
    } catch (err) {
      logger.warn({ event: 'auth_init_exception', error: String(err) });
      clearAuth();
    } finally {
      setLoading(false);
    }
  }, [setUser, setSession, setLoading, clearAuth]);

  useEffect(() => {
    const supabase = createClient();

    // Initialize auth state
    initializeAuth();

    // Listen for auth state changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      logger.info({ event: 'auth_state_change', authEvent: event, userId: session?.user?.id });

      switch (event) {
        case 'SIGNED_IN':
          if (session) {
            setSession(session);
            setUser(session.user);
          }
          break;

        case 'SIGNED_OUT':
          clearAuth();
          break;

        case 'TOKEN_REFRESHED':
          if (session) {
            setSession(session);
          }
          break;

        case 'USER_UPDATED':
          if (session?.user) {
            setUser(session.user);
          }
          break;

        default:
          // Handle other events if needed
          break;
      }
    });

    // Cleanup subscription on unmount
    return () => {
      subscription.unsubscribe();
    };
  }, [initializeAuth, setUser, setSession, clearAuth]);

  return <>{children}</>;
}
