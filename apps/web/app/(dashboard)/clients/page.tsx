'use client';

/**
 * Clients Page
 *
 * List and manage client profiles.
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useClientStore, useProfiles, useClientLoading } from '@/stores/client-store';
import { ClientList } from '@/components/client/client-list';
import { ClientProfile } from '@/stores/client-store';
import { logger } from '@/lib/logger';

export default function ClientsPage() {
  const router = useRouter();
  const profiles = useProfiles();
  const isLoading = useClientLoading();
  const { fetchProfiles, deleteProfile, setActiveProfile } = useClientStore();
  const [deleteConfirm, setDeleteConfirm] = useState<ClientProfile | null>(null);

  useEffect(() => {
    logger.info({ event: 'page_view', page: 'clients' });
    fetchProfiles();
  }, [fetchProfiles]);

  const handleSelect = (profile: ClientProfile) => {
    router.push(`/clients/${profile.id}`);
  };

  const handleEdit = (profile: ClientProfile) => {
    router.push(`/clients/${profile.id}?edit=true`);
  };

  const handleDelete = async (profile: ClientProfile) => {
    setDeleteConfirm(profile);
  };

  const confirmDelete = async () => {
    if (!deleteConfirm) return;

    logger.info({ event: 'client_delete', profileId: deleteConfirm.id });
    await deleteProfile(deleteConfirm.id);
    setDeleteConfirm(null);
  };

  const handleActivate = async (profile: ClientProfile) => {
    logger.info({ event: 'client_activate', profileId: profile.id });
    await setActiveProfile(profile.id);
  };

  const handleCreateNew = () => {
    router.push('/clients/new');
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Client Profiles</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your business profiles for lead generation.
          </p>
        </div>
        <Link
          href="/clients/new"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          New Client Profile
        </Link>
      </div>

      {/* Client List */}
      <ClientList
        profiles={profiles}
        isLoading={isLoading}
        onSelect={handleSelect}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onActivate={handleActivate}
        onCreateNew={handleCreateNew}
      />

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Delete Client Profile
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Are you sure you want to delete &quot;{deleteConfirm.company_name}&quot;?
              This will also delete all associated leads and search history. This
              action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
