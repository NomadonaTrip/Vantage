'use client';

/**
 * Client Detail Component
 *
 * Displays detailed information about a single client profile.
 */

import { ClientProfile } from '@/stores/client-store';

interface ClientDetailProps {
  profile: ClientProfile;
  onEdit?: () => void;
  onDelete?: () => void;
  onActivate?: () => void;
}

export function ClientDetail({
  profile,
  onEdit,
  onDelete,
  onActivate,
}: ClientDetailProps) {
  return (
    <div className="bg-white shadow rounded-lg">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {profile.company_name}
            </h2>
            <p className="mt-1 text-sm text-gray-500">{profile.industry}</p>
          </div>
          <div className="flex items-center gap-3">
            {profile.is_active ? (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                Active Profile
              </span>
            ) : (
              onActivate && (
                <button
                  onClick={onActivate}
                  className="inline-flex items-center px-3 py-1.5 border border-blue-600 text-sm font-medium rounded-md text-blue-600 bg-white hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Set as Active
                </button>
              )
            )}
            {onEdit && (
              <button
                onClick={onEdit}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Edit
              </button>
            )}
            {onDelete && (
              <button
                onClick={onDelete}
                className="inline-flex items-center px-3 py-1.5 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Delete
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 py-5 space-y-6">
        {/* Ideal Customer Profile */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
            Ideal Customer Profile
          </h3>
          <p className="mt-2 text-gray-900 whitespace-pre-wrap">
            {profile.ideal_customer_profile}
          </p>
        </div>

        {/* Services */}
        {profile.services.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
              Services Offered
            </h3>
            <div className="mt-2 flex flex-wrap gap-2">
              {profile.services.map((service, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800"
                >
                  {service}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Additional Context */}
        {profile.additional_context && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
              Additional Context
            </h3>
            <p className="mt-2 text-gray-900 whitespace-pre-wrap">
              {profile.additional_context}
            </p>
          </div>
        )}

        {/* Metadata */}
        <div className="pt-4 border-t border-gray-200">
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-gray-500">Created</dt>
              <dd className="text-gray-900">
                {new Date(profile.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">Last Updated</dt>
              <dd className="text-gray-900">
                {new Date(profile.updated_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
