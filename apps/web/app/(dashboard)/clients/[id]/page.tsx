'use client';

/**
 * Client Detail Page
 *
 * View and edit a client profile.
 */

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  useClientStore,
  useClientLoading,
  ClientProfile,
  ClientProfileUpdate,
} from '@/stores/client-store';
import { ClientDetail } from '@/components/client/client-detail';
import { ClientForm } from '@/components/client/client-form';
import { ConversationHistory } from '@/components/client/conversation-history';
import { logger } from '@/lib/logger';

interface PageProps {
  params: { id: string };
}

export default function ClientDetailPage({ params }: PageProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isEditMode = searchParams.get('edit') === 'true';

  const { getProfile, updateProfile, deleteProfile, setActiveProfile } =
    useClientStore();
  const isLoading = useClientLoading();

  const [profile, setProfile] = useState<ClientProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  useEffect(() => {
    logger.info({ event: 'page_view', page: 'clients/detail', profileId: params.id });

    const loadProfile = async () => {
      setLoading(true);
      const fetchedProfile = await getProfile(params.id);

      if (fetchedProfile) {
        setProfile(fetchedProfile);
      } else {
        setError('Client profile not found');
      }
      setLoading(false);
    };

    loadProfile();
  }, [params.id, getProfile]);

  const handleEdit = () => {
    router.push(`/clients/${params.id}?edit=true`);
  };

  const handleCancelEdit = () => {
    router.push(`/clients/${params.id}`);
  };

  const handleUpdate = async (data: ClientProfileUpdate) => {
    logger.info({ event: 'update_client_submit', profileId: params.id });

    const updated = await updateProfile(params.id, data);

    if (updated) {
      setProfile(updated);
      router.push(`/clients/${params.id}`);
      logger.info({ event: 'update_client_success', profileId: params.id });
    }
  };

  const handleDelete = () => {
    setDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    logger.info({ event: 'delete_client_confirm', profileId: params.id });

    const deleted = await deleteProfile(params.id);

    if (deleted) {
      router.push('/clients');
      logger.info({ event: 'delete_client_success', profileId: params.id });
    }
    setDeleteConfirm(false);
  };

  const handleActivate = async () => {
    if (!profile) return;

    logger.info({ event: 'activate_client_submit', profileId: params.id });

    const activated = await setActiveProfile(params.id);

    if (activated) {
      setProfile(activated);
      logger.info({ event: 'activate_client_success', profileId: params.id });
    }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="bg-white shadow rounded-lg p-6">
            <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="h-24 bg-gray-200 rounded mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="max-w-3xl mx-auto text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          {error || 'Profile not found'}
        </h2>
        <p className="text-gray-500 mb-4">
          The client profile you&apos;re looking for doesn&apos;t exist or you don&apos;t have
          access to it.
        </p>
        <Link
          href="/clients"
          className="text-blue-600 hover:text-blue-700 font-medium"
        >
          Back to Clients
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Breadcrumb */}
      <nav className="mb-6">
        <ol className="flex items-center space-x-2 text-sm text-gray-500">
          <li>
            <Link href="/clients" className="hover:text-gray-700">
              Clients
            </Link>
          </li>
          <li>/</li>
          <li className="text-gray-900">{profile.company_name}</li>
          {isEditMode && (
            <>
              <li>/</li>
              <li className="text-gray-900">Edit</li>
            </>
          )}
        </ol>
      </nav>

      {/* Content */}
      {isEditMode ? (
        <div>
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900">Edit Profile</h1>
            <p className="mt-1 text-sm text-gray-500">
              Update your client profile information.
            </p>
          </div>
          <div className="bg-white shadow rounded-lg p-6">
            <ClientForm
              profile={profile}
              onSubmit={handleUpdate}
              onCancel={handleCancelEdit}
              isLoading={isLoading}
            />
          </div>
        </div>
      ) : (
        <div className="space-y-8">
          <ClientDetail
            profile={profile}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onActivate={handleActivate}
          />

          {/* Conversation History */}
          <div className="bg-white shadow rounded-lg p-6">
            <ConversationHistory profileId={params.id} />
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Delete Client Profile
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Are you sure you want to delete &quot;{profile.company_name}&quot;? This
              will also delete all associated leads and search history. This
              action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteConfirm(false)}
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
