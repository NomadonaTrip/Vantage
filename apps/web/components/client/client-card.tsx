'use client';

/**
 * Client Card Component
 *
 * Displays a single client profile in a card format.
 */

import { ClientProfile } from '@/stores/client-store';

interface ClientCardProps {
  profile: ClientProfile;
  onSelect?: (profile: ClientProfile) => void;
  onEdit?: (profile: ClientProfile) => void;
  onDelete?: (profile: ClientProfile) => void;
  onActivate?: (profile: ClientProfile) => void;
}

export function ClientCard({
  profile,
  onSelect,
  onEdit,
  onDelete,
  onActivate,
}: ClientCardProps) {
  return (
    <div
      className={`bg-white rounded-lg shadow-md p-6 border-2 transition-all ${
        profile.is_active
          ? 'border-blue-500 ring-2 ring-blue-100'
          : 'border-transparent hover:border-gray-200'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div
          className={onSelect ? 'cursor-pointer' : ''}
          onClick={() => onSelect?.(profile)}
        >
          <h3 className="text-lg font-semibold text-gray-900">
            {profile.company_name}
          </h3>
          <p className="text-sm text-gray-500">{profile.industry}</p>
        </div>
        {profile.is_active && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            Active
          </span>
        )}
      </div>

      {/* ICP Summary */}
      <p className="text-sm text-gray-600 mb-4 line-clamp-2">
        {profile.ideal_customer_profile}
      </p>

      {/* Services */}
      {profile.services.length > 0 && (
        <div className="mb-4">
          <div className="flex flex-wrap gap-1">
            {profile.services.slice(0, 3).map((service, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700"
              >
                {service}
              </span>
            ))}
            {profile.services.length > 3 && (
              <span className="text-xs text-gray-500">
                +{profile.services.length - 3} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t">
        <div className="flex gap-2">
          {onEdit && (
            <button
              onClick={() => onEdit(profile)}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Edit
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(profile)}
              className="text-sm text-red-600 hover:text-red-800"
            >
              Delete
            </button>
          )}
        </div>
        {!profile.is_active && onActivate && (
          <button
            onClick={() => onActivate(profile)}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Set Active
          </button>
        )}
      </div>
    </div>
  );
}
