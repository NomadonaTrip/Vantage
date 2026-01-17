'use client';

/**
 * New Client Page
 *
 * Create a new client profile.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useClientStore, useClientLoading } from '@/stores/client-store';
import { ClientForm } from '@/components/client/client-form';
import { ClientProfileCreate } from '@/stores/client-store';
import { logger } from '@/lib/logger';

export default function NewClientPage() {
  const router = useRouter();
  const { createProfile } = useClientStore();
  const isLoading = useClientLoading();

  useEffect(() => {
    logger.info({ event: 'page_view', page: 'clients/new' });
  }, []);

  const handleSubmit = async (data: ClientProfileCreate) => {
    logger.info({ event: 'create_client_submit', company: data.company_name });

    const profile = await createProfile(data);

    if (profile) {
      logger.info({ event: 'create_client_success', profileId: profile.id });
      router.push(`/clients/${profile.id}`);
    }
  };

  const handleCancel = () => {
    router.push('/clients');
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Breadcrumb */}
      <nav className="mb-6">
        <ol className="flex items-center space-x-2 text-sm text-gray-500">
          <li>
            <Link href="/clients" className="hover:text-gray-700">
              Clients
            </Link>
          </li>
          <li>/</li>
          <li className="text-gray-900">New Profile</li>
        </ol>
      </nav>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Create Client Profile
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Set up a new business profile for lead generation.
        </p>
      </div>

      {/* Form */}
      <div className="bg-white shadow rounded-lg p-6">
        <ClientForm
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
