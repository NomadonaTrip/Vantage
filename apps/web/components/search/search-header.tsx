'use client';

/**
 * Search Header Component
 *
 * Displays active client context and search controls.
 */

import { ClientProfile } from '@/stores/client-store';
import { QualitySlider } from './quality-slider';

interface SearchHeaderProps {
  activeProfile: ClientProfile | null;
  qualityLevel: number;
  onQualityChange: (level: number) => void;
  onStartSearch: () => void;
  isSearching: boolean;
}

export function SearchHeader({
  activeProfile,
  qualityLevel,
  onQualityChange,
  onStartSearch,
  isSearching,
}: SearchHeaderProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6 space-y-6">
      {/* Active Client Context */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Search for Leads</h1>
        {activeProfile ? (
          <div className="mt-2 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-900">
                  Active Client Profile
                </p>
                <p className="text-lg font-semibold text-blue-800">
                  {activeProfile.company_name}
                </p>
                <p className="text-sm text-blue-600">{activeProfile.industry}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-blue-500">ICP</p>
                <p className="text-sm text-blue-700 max-w-xs truncate">
                  {activeProfile.ideal_customer_profile}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="mt-2 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              No active client profile. Please select or create a client profile
              to start searching for leads.
            </p>
          </div>
        )}
      </div>

      {/* Quality Slider */}
      <div className="max-w-md">
        <QualitySlider
          value={qualityLevel}
          onChange={onQualityChange}
          disabled={isSearching}
        />
      </div>

      {/* Start Search Button */}
      <div>
        <button
          onClick={onStartSearch}
          disabled={!activeProfile || isSearching}
          className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSearching ? (
            <>
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Searching...
            </>
          ) : (
            <>
              <svg
                className="-ml-1 mr-2 h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                  clipRule="evenodd"
                />
              </svg>
              Start Search
            </>
          )}
        </button>
      </div>
    </div>
  );
}
