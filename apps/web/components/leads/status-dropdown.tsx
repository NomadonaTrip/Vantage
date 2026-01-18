'use client';

/**
 * Status Dropdown Component
 *
 * Dropdown for updating lead status.
 */

import { useState } from 'react';
import { LeadStatus } from '@/stores/leads-store';

interface StatusDropdownProps {
  status: LeadStatus;
  onChange: (status: LeadStatus) => void;
  disabled?: boolean;
}

const statusOptions: { value: LeadStatus; label: string; color: string }[] = [
  { value: 'new', label: 'New', color: 'bg-blue-100 text-blue-800' },
  { value: 'contacted', label: 'Contacted', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'responded', label: 'Responded', color: 'bg-purple-100 text-purple-800' },
  { value: 'converted', label: 'Converted', color: 'bg-green-100 text-green-800' },
  { value: 'lost', label: 'Lost', color: 'bg-gray-100 text-gray-800' },
];

const getStatusConfig = (status: LeadStatus) => {
  return statusOptions.find((opt) => opt.value === status) || statusOptions[0];
};

export function StatusDropdown({ status, onChange, disabled = false }: StatusDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const currentConfig = getStatusConfig(status);

  const handleSelect = (newStatus: LeadStatus) => {
    if (newStatus !== status) {
      onChange(newStatus);
    }
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${currentConfig.color} disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        {currentConfig.label}
        <svg
          className={`ml-1 h-3 w-3 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          {/* Dropdown */}
          <div className="absolute z-20 mt-1 w-32 bg-white rounded-md shadow-lg border border-gray-200">
            {statusOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => handleSelect(option.value)}
                className={`w-full text-left px-3 py-2 text-xs hover:bg-gray-50 first:rounded-t-md last:rounded-b-md ${
                  option.value === status ? 'bg-gray-50 font-medium' : ''
                }`}
              >
                <span className={`inline-block w-2 h-2 rounded-full mr-2 ${option.color.split(' ')[0]}`} />
                {option.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export { getStatusConfig, statusOptions };
