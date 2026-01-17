'use client';

/**
 * Dashboard Layout
 *
 * Layout for authenticated dashboard pages with navigation.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/stores/auth-store';
import { useClientStore, useActiveProfile } from '@/stores/client-store';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { user, isLoading: authLoading, signOut } = useAuthStore();
  const { fetchProfiles } = useClientStore();
  const activeProfile = useActiveProfile();

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  // Fetch profiles on mount
  useEffect(() => {
    if (user) {
      fetchProfiles();
    }
  }, [user, fetchProfiles]);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Left side */}
            <div className="flex">
              <Link
                href="/"
                className="flex items-center px-2 text-xl font-bold text-gray-900"
              >
                Vantage
              </Link>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <Link
                  href="/clients"
                  className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 border-b-2 border-transparent hover:border-gray-300"
                >
                  Clients
                </Link>
                <Link
                  href="/search"
                  className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 border-b-2 border-transparent hover:border-gray-300 hover:text-gray-700"
                >
                  Search
                </Link>
                <Link
                  href="/leads"
                  className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 border-b-2 border-transparent hover:border-gray-300 hover:text-gray-700"
                >
                  Leads
                </Link>
                <Link
                  href="/analytics"
                  className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 border-b-2 border-transparent hover:border-gray-300 hover:text-gray-700"
                >
                  Analytics
                </Link>
              </div>
            </div>

            {/* Right side */}
            <div className="flex items-center space-x-4">
              {/* Active Profile Indicator */}
              {activeProfile && (
                <Link
                  href="/clients"
                  className="flex items-center px-3 py-1.5 text-sm bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100"
                >
                  <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                  {activeProfile.company_name}
                </Link>
              )}

              {/* User Menu */}
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">{user.email}</span>
                <button
                  onClick={() => signOut()}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Sign out
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">{children}</div>
      </main>
    </div>
  );
}
