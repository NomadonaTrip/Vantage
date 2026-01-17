'use client';

/**
 * Dashboard Home Page
 *
 * Main dashboard landing page after login.
 */

import { useEffect } from 'react';
import Link from 'next/link';
import { useActiveProfile, useProfiles } from '@/stores/client-store';
import { logger } from '@/lib/logger';

export default function DashboardPage() {
  const activeProfile = useActiveProfile();
  const profiles = useProfiles();

  useEffect(() => {
    logger.info({ event: 'page_view', page: 'dashboard' });
  }, []);

  return (
    <div>
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Welcome to Vantage. Start generating high-quality leads.
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-8">
        {/* Active Profile Card */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
            Active Profile
          </h3>
          {activeProfile ? (
            <div>
              <p className="text-lg font-semibold text-gray-900">
                {activeProfile.company_name}
              </p>
              <p className="text-sm text-gray-500">{activeProfile.industry}</p>
              <Link
                href={`/clients/${activeProfile.id}`}
                className="mt-4 inline-block text-sm text-blue-600 hover:text-blue-700"
              >
                View Profile →
              </Link>
            </div>
          ) : (
            <div>
              <p className="text-gray-500 mb-4">No active profile selected.</p>
              <Link
                href="/clients"
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                Select a Profile →
              </Link>
            </div>
          )}
        </div>

        {/* Start Search Card */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
            Lead Generation
          </h3>
          {activeProfile ? (
            <div>
              <p className="text-gray-600 mb-4">
                Start finding leads for {activeProfile.company_name}.
              </p>
              <Link
                href="/search"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
              >
                Start Search
              </Link>
            </div>
          ) : (
            <div>
              <p className="text-gray-500 mb-4">
                Select a client profile to start searching for leads.
              </p>
            </div>
          )}
        </div>

        {/* Profiles Summary */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
            Client Profiles
          </h3>
          <p className="text-3xl font-bold text-gray-900 mb-2">
            {profiles.length}
          </p>
          <p className="text-sm text-gray-500 mb-4">
            {profiles.length === 1 ? 'profile' : 'profiles'} configured
          </p>
          <Link
            href="/clients"
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            Manage Profiles →
          </Link>
        </div>
      </div>

      {/* Getting Started (if no profiles) */}
      {profiles.length === 0 && (
        <div className="bg-blue-50 rounded-lg p-6 text-center">
          <h3 className="text-lg font-medium text-blue-900 mb-2">
            Get Started
          </h3>
          <p className="text-blue-700 mb-4">
            Create your first client profile to start generating leads.
          </p>
          <Link
            href="/clients/new"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            Create Client Profile
          </Link>
        </div>
      )}
    </div>
  );
}
