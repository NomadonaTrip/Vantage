'use client';

/**
 * Client Form Component
 *
 * Form for creating and editing client profiles.
 */

import { useState, FormEvent } from 'react';
import {
  ClientProfile,
  ClientProfileCreate,
  ClientProfileUpdate,
} from '@/stores/client-store';

interface ClientFormProps {
  profile?: ClientProfile;
  onSubmit: (data: ClientProfileCreate | ClientProfileUpdate) => Promise<void>;
  onCancel?: () => void;
  isLoading?: boolean;
}

export function ClientForm({
  profile,
  onSubmit,
  onCancel,
  isLoading = false,
}: ClientFormProps) {
  const [companyName, setCompanyName] = useState(profile?.company_name || '');
  const [industry, setIndustry] = useState(profile?.industry || '');
  const [icp, setIcp] = useState(profile?.ideal_customer_profile || '');
  const [servicesText, setServicesText] = useState(
    profile?.services?.join(', ') || ''
  );
  const [additionalContext, setAdditionalContext] = useState(
    profile?.additional_context || ''
  );
  const [error, setError] = useState<string | null>(null);

  const isEditing = !!profile;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!companyName.trim()) {
      setError('Company name is required');
      return;
    }
    if (!industry.trim()) {
      setError('Industry is required');
      return;
    }
    if (!icp.trim()) {
      setError('Ideal customer profile is required');
      return;
    }

    // Parse services
    const services = servicesText
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    const data: ClientProfileCreate | ClientProfileUpdate = {
      company_name: companyName.trim(),
      industry: industry.trim(),
      ideal_customer_profile: icp.trim(),
      services,
      additional_context: additionalContext.trim() || null,
    };

    try {
      await onSubmit(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Company Name */}
      <div>
        <label
          htmlFor="company_name"
          className="block text-sm font-medium text-gray-700"
        >
          Company Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="company_name"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          placeholder="Acme Corp"
          required
        />
      </div>

      {/* Industry */}
      <div>
        <label
          htmlFor="industry"
          className="block text-sm font-medium text-gray-700"
        >
          Industry <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="industry"
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          placeholder="Software Development"
          required
        />
      </div>

      {/* Ideal Customer Profile */}
      <div>
        <label
          htmlFor="icp"
          className="block text-sm font-medium text-gray-700"
        >
          Ideal Customer Profile <span className="text-red-500">*</span>
        </label>
        <textarea
          id="icp"
          rows={4}
          value={icp}
          onChange={(e) => setIcp(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          placeholder="Describe your ideal customer: their industry, company size, pain points, budget range, etc."
          required
        />
        <p className="mt-1 text-xs text-gray-500">
          Be specific about who you want to work with. This helps find better leads.
        </p>
      </div>

      {/* Services */}
      <div>
        <label
          htmlFor="services"
          className="block text-sm font-medium text-gray-700"
        >
          Services Offered
        </label>
        <input
          type="text"
          id="services"
          value={servicesText}
          onChange={(e) => setServicesText(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          placeholder="Web Development, Mobile Apps, Cloud Migration"
        />
        <p className="mt-1 text-xs text-gray-500">
          Comma-separated list of services you offer.
        </p>
      </div>

      {/* Additional Context */}
      <div>
        <label
          htmlFor="additional_context"
          className="block text-sm font-medium text-gray-700"
        >
          Additional Context
        </label>
        <textarea
          id="additional_context"
          rows={3}
          value={additionalContext}
          onChange={(e) => setAdditionalContext(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          placeholder="Any other information that might help find better leads..."
        />
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading
            ? 'Saving...'
            : isEditing
            ? 'Update Profile'
            : 'Create Profile'}
        </button>
      </div>
    </form>
  );
}
