'use client';

/**
 * Manual Override Component
 *
 * Collapsible panel for custom search parameters.
 */

import { useState } from 'react';
import { ManualOverride as ManualOverrideType, CompanySize } from '@/stores/search-store';

interface ManualOverrideProps {
  override: ManualOverrideType | null;
  onChange: (override: ManualOverrideType | null) => void;
  disabled?: boolean;
}

const companySizeOptions: { value: CompanySize; label: string }[] = [
  { value: 'solo', label: 'Solo (1 employee)' },
  { value: 'small', label: 'Small (2-50 employees)' },
  { value: 'medium', label: 'Medium (51-500 employees)' },
  { value: 'enterprise', label: 'Enterprise (500+ employees)' },
];

export function ManualOverride({ override, onChange, disabled = false }: ManualOverrideProps) {
  const [isExpanded, setIsExpanded] = useState(!!override);

  const defaultOverride: ManualOverrideType = {
    mode: 'supplement',
    keywords: '',
    location: '',
    companySize: undefined,
    budgetMin: undefined,
    budgetMax: undefined,
    industry: '',
  };

  const currentOverride = override || defaultOverride;

  const handleChange = (field: keyof ManualOverrideType, value: unknown) => {
    const updated = { ...currentOverride, [field]: value };

    // Check if all fields are empty/default
    const isEmpty =
      updated.mode === 'supplement' &&
      !updated.keywords &&
      !updated.location &&
      !updated.companySize &&
      !updated.budgetMin &&
      !updated.budgetMax &&
      !updated.industry;

    onChange(isEmpty ? null : updated);
  };

  const handleClear = () => {
    onChange(null);
    setIsExpanded(false);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* Toggle Header */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        disabled={disabled}
        className="w-full px-6 py-4 flex items-center justify-between text-left disabled:opacity-50"
      >
        <div className="flex items-center gap-2">
          <svg
            className={`h-5 w-5 text-gray-500 transition-transform ${
              isExpanded ? 'rotate-90' : ''
            }`}
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
              clipRule="evenodd"
            />
          </svg>
          <span className="font-medium text-gray-900">Manual Override</span>
          {override && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
              Active
            </span>
          )}
        </div>
        <span className="text-sm text-gray-500">
          {isExpanded ? 'Click to collapse' : 'Click to expand'}
        </span>
      </button>

      {/* Collapsible Content */}
      {isExpanded && (
        <div className="px-6 pb-6 space-y-4 border-t border-gray-100">
          {/* Mode Toggle */}
          <div className="pt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Override Mode
            </label>
            <div className="flex gap-4">
              <label className="inline-flex items-center">
                <input
                  type="radio"
                  name="mode"
                  value="supplement"
                  checked={currentOverride.mode === 'supplement'}
                  onChange={() => handleChange('mode', 'supplement')}
                  disabled={disabled}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Supplement (add to ICP)
                </span>
              </label>
              <label className="inline-flex items-center">
                <input
                  type="radio"
                  name="mode"
                  value="replace"
                  checked={currentOverride.mode === 'replace'}
                  onChange={() => handleChange('mode', 'replace')}
                  disabled={disabled}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Replace (use only these)
                </span>
              </label>
            </div>
          </div>

          {/* Keywords */}
          <div>
            <label
              htmlFor="keywords"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Keywords
            </label>
            <input
              type="text"
              id="keywords"
              value={currentOverride.keywords || ''}
              onChange={(e) => handleChange('keywords', e.target.value)}
              disabled={disabled}
              placeholder="e.g., AI, machine learning, automation"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
            />
          </div>

          {/* Location and Industry (2 columns) */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="location"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Location
              </label>
              <input
                type="text"
                id="location"
                value={currentOverride.location || ''}
                onChange={(e) => handleChange('location', e.target.value)}
                disabled={disabled}
                placeholder="e.g., San Francisco, CA"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              />
            </div>
            <div>
              <label
                htmlFor="industry"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Industry
              </label>
              <input
                type="text"
                id="industry"
                value={currentOverride.industry || ''}
                onChange={(e) => handleChange('industry', e.target.value)}
                disabled={disabled}
                placeholder="e.g., Technology, Healthcare"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              />
            </div>
          </div>

          {/* Company Size */}
          <div>
            <label
              htmlFor="companySize"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Company Size
            </label>
            <select
              id="companySize"
              value={currentOverride.companySize || ''}
              onChange={(e) =>
                handleChange(
                  'companySize',
                  e.target.value ? (e.target.value as CompanySize) : undefined
                )
              }
              disabled={disabled}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
            >
              <option value="">Any size</option>
              {companySizeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Budget Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Budget Range
            </label>
            <div className="grid grid-cols-2 gap-4">
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                  $
                </span>
                <input
                  type="number"
                  value={currentOverride.budgetMin || ''}
                  onChange={(e) =>
                    handleChange(
                      'budgetMin',
                      e.target.value ? parseInt(e.target.value) : undefined
                    )
                  }
                  disabled={disabled}
                  placeholder="Min"
                  min="0"
                  className="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                />
              </div>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                  $
                </span>
                <input
                  type="number"
                  value={currentOverride.budgetMax || ''}
                  onChange={(e) =>
                    handleChange(
                      'budgetMax',
                      e.target.value ? parseInt(e.target.value) : undefined
                    )
                  }
                  disabled={disabled}
                  placeholder="Max"
                  min="0"
                  className="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                />
              </div>
            </div>
          </div>

          {/* Clear Button */}
          {override && (
            <div className="pt-2">
              <button
                type="button"
                onClick={handleClear}
                disabled={disabled}
                className="text-sm text-red-600 hover:text-red-800 disabled:opacity-50"
              >
                Clear all overrides
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
