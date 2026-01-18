'use client';

/**
 * Accuracy Badge Component
 *
 * Visual indicator and dropdown for lead accuracy status.
 */

import { useState } from 'react';
import { LeadAccuracy } from '@/stores/leads-store';

interface AccuracyBadgeProps {
  accuracy: LeadAccuracy;
  onChange: (accuracy: LeadAccuracy) => void;
  disabled?: boolean;
}

const accuracyOptions: { value: LeadAccuracy; label: string; icon: string; color: string }[] = [
  { value: 'unverified', label: 'Unverified', icon: '?', color: 'bg-gray-100 text-gray-600' },
  { value: 'verified', label: 'Verified', icon: '✓', color: 'bg-green-100 text-green-700' },
  { value: 'email_bounced', label: 'Email Bounced', icon: '✉', color: 'bg-red-100 text-red-700' },
  { value: 'phone_invalid', label: 'Phone Invalid', icon: '☎', color: 'bg-orange-100 text-orange-700' },
  { value: 'wrong_person', label: 'Wrong Person', icon: '👤', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'company_mismatch', label: 'Company Mismatch', icon: '🏢', color: 'bg-purple-100 text-purple-700' },
];

const getAccuracyConfig = (accuracy: LeadAccuracy) => {
  return accuracyOptions.find((opt) => opt.value === accuracy) || accuracyOptions[0];
};

export function AccuracyBadge({ accuracy, onChange, disabled = false }: AccuracyBadgeProps) {
  const [isOpen, setIsOpen] = useState(false);
  const currentConfig = getAccuracyConfig(accuracy);

  const handleSelect = (newAccuracy: LeadAccuracy) => {
    if (newAccuracy !== accuracy) {
      onChange(newAccuracy);
    }
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        title={currentConfig.label}
        className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium ${currentConfig.color} disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        {currentConfig.icon}
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          {/* Dropdown */}
          <div className="absolute right-0 z-20 mt-1 w-40 bg-white rounded-md shadow-lg border border-gray-200">
            {accuracyOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => handleSelect(option.value)}
                className={`w-full text-left px-3 py-2 text-xs hover:bg-gray-50 first:rounded-t-md last:rounded-b-md ${
                  option.value === accuracy ? 'bg-gray-50 font-medium' : ''
                }`}
              >
                <span className="mr-2">{option.icon}</span>
                {option.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export { getAccuracyConfig, accuracyOptions };
