'use client';

/**
 * Client List Component
 *
 * Displays a grid of client profile cards.
 */

import { ClientProfile } from '@/stores/client-store';
import { ClientCard } from './client-card';

interface ClientListProps {
  profiles: ClientProfile[];
  isLoading?: boolean;
  onSelect?: (profile: ClientProfile) => void;
  onEdit?: (profile: ClientProfile) => void;
  onDelete?: (profile: ClientProfile) => void;
  onActivate?: (profile: ClientProfile) => void;
  onCreateNew?: () => void;
}

export function ClientList({
  profiles,
  isLoading = false,
  onSelect,
  onEdit,
  onDelete,
  onActivate,
  onCreateNew,
}: ClientListProps) {
  if (isLoading) {
    return (
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-white rounded-lg shadow-md p-6 animate-pulse"
          >
            <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-16 bg-gray-200 rounded mb-4"></div>
            <div className="h-8 bg-gray-200 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  if (profiles.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="mx-auto h-24 w-24 text-gray-400 mb-4">
          <svg
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            className="w-full h-full"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1}
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No client profiles yet
        </h3>
        <p className="text-gray-500 mb-6">
          Create your first client profile to start generating leads.
        </p>
        {onCreateNew && (
          <button
            onClick={onCreateNew}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Create Client Profile
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {profiles.map((profile) => (
        <ClientCard
          key={profile.id}
          profile={profile}
          onSelect={onSelect}
          onEdit={onEdit}
          onDelete={onDelete}
          onActivate={onActivate}
        />
      ))}
    </div>
  );
}
