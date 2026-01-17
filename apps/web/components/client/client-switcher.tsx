'use client';

/**
 * Client Switcher Component
 *
 * Dropdown component for quickly switching between client profiles.
 */

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  useClientStore,
  useProfiles,
  useActiveProfile,
  useClientLoading,
  ClientProfile,
} from '@/stores/client-store';
import { logger } from '@/lib/logger';

interface ClientSwitcherProps {
  variant?: 'compact' | 'full';
  className?: string;
}

export function ClientSwitcher({
  variant = 'compact',
  className = '',
}: ClientSwitcherProps) {
  const router = useRouter();
  const profiles = useProfiles();
  const activeProfile = useActiveProfile();
  const isLoading = useClientLoading();
  const { setActiveProfile, fetchProfiles } = useClientStore();

  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch profiles if not loaded
  useEffect(() => {
    if (profiles.length === 0 && !isLoading) {
      fetchProfiles();
    }
  }, [profiles.length, isLoading, fetchProfiles]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close on escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  const handleSwitch = async (profile: ClientProfile) => {
    if (profile.id === activeProfile?.id) {
      setIsOpen(false);
      return;
    }

    logger.info({
      event: 'client_switch',
      fromId: activeProfile?.id,
      toId: profile.id,
    });

    await setActiveProfile(profile.id);
    setIsOpen(false);
  };

  const handleCreateNew = () => {
    setIsOpen(false);
    router.push('/clients/new');
  };

  const handleManageProfiles = () => {
    setIsOpen(false);
    router.push('/clients');
  };

  if (isLoading && profiles.length === 0) {
    return (
      <div className={`flex items-center ${className}`}>
        <div className="animate-pulse flex items-center space-x-2">
          <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
          <div className="h-4 bg-gray-200 rounded w-24"></div>
        </div>
      </div>
    );
  }

  if (profiles.length === 0) {
    return (
      <button
        onClick={handleCreateNew}
        className={`flex items-center text-sm text-blue-600 hover:text-blue-700 ${className}`}
      >
        Create Profile
      </button>
    );
  }

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label="Switch client profile"
        className={`flex items-center gap-2 px-3 py-1.5 rounded-full transition-colors ${
          variant === 'compact'
            ? 'text-sm bg-blue-50 text-blue-700 hover:bg-blue-100'
            : 'text-base bg-white border border-gray-300 shadow-sm hover:bg-gray-50'
        }`}
      >
        {/* Active indicator */}
        <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0"></span>

        {/* Profile name */}
        <span className="truncate max-w-[150px]">
          {activeProfile?.company_name || 'Select Profile'}
        </span>

        {/* Dropdown arrow */}
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          role="listbox"
          aria-label="Client profiles"
          className="absolute right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 z-50 overflow-hidden"
        >
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
              Switch Profile
            </p>
          </div>

          {/* Profile List */}
          <div className="max-h-64 overflow-y-auto">
            {profiles.map((profile) => (
              <button
                key={profile.id}
                role="option"
                aria-selected={profile.id === activeProfile?.id}
                onClick={() => handleSwitch(profile)}
                className={`w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors flex items-start gap-3 ${
                  profile.id === activeProfile?.id ? 'bg-blue-50' : ''
                }`}
              >
                {/* Selection indicator */}
                <span
                  className={`w-4 h-4 mt-0.5 rounded-full border-2 flex-shrink-0 flex items-center justify-center ${
                    profile.id === activeProfile?.id
                      ? 'border-blue-500 bg-blue-500'
                      : 'border-gray-300'
                  }`}
                >
                  {profile.id === activeProfile?.id && (
                    <svg
                      className="w-2.5 h-2.5 text-white"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </span>

                {/* Profile info */}
                <div className="flex-1 min-w-0">
                  <p
                    className={`text-sm font-medium truncate ${
                      profile.id === activeProfile?.id
                        ? 'text-blue-700'
                        : 'text-gray-900'
                    }`}
                  >
                    {profile.company_name}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {profile.industry}
                  </p>
                </div>
              </button>
            ))}
          </div>

          {/* Footer Actions */}
          <div className="border-t border-gray-100 bg-gray-50 px-4 py-3 flex justify-between">
            <button
              onClick={handleCreateNew}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              + New Profile
            </button>
            <button
              onClick={handleManageProfiles}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Manage All
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
