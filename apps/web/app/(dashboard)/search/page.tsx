'use client';

/**
 * Search Page
 *
 * Lead generation search page with progress tracking and results display.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useClientStore, useActiveProfile } from '@/stores/client-store';
import {
  useSearchStore,
  useSearchStatus,
  useSearchProgress,
  useSearchSources,
  useSearchLeads,
  useSearchError,
  useQualityLevel,
  useManualOverride,
} from '@/stores/search-store';
import {
  SearchHeader,
  ManualOverride,
  SearchProgress,
  SearchResults,
} from '@/components/search';
import { logger } from '@/lib/logger';

export default function SearchPage() {
  const router = useRouter();
  const activeProfile = useActiveProfile();
  const { fetchProfiles } = useClientStore();

  // Search store state
  const status = useSearchStatus();
  const progress = useSearchProgress();
  const sources = useSearchSources();
  const leads = useSearchLeads();
  const error = useSearchError();
  const qualityLevel = useQualityLevel();
  const manualOverride = useManualOverride();

  // Search store actions
  const {
    startSearch,
    cancelSearch,
    setQualityLevel,
    setManualOverride,
    reset: resetSearch,
  } = useSearchStore();

  // Fetch profiles on mount
  useEffect(() => {
    fetchProfiles();
    logger.info({ event: 'page_view', page: 'search' });
  }, [fetchProfiles]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      useSearchStore.getState().stopPolling();
    };
  }, []);

  const handleStartSearch = async () => {
    if (!activeProfile) {
      logger.warn({ event: 'search_attempt_no_profile' });
      router.push('/clients');
      return;
    }

    logger.info({
      event: 'search_initiated',
      profileId: activeProfile.id,
      qualityLevel,
      hasManualOverride: !!manualOverride,
    });

    await startSearch(activeProfile.id);
  };

  const handleRetry = () => {
    resetSearch();
    handleStartSearch();
  };

  const isSearching = status === 'searching';
  const showProgress = status === 'searching' || status === 'completed' || status === 'cancelled';
  const showResults = leads.length > 0 || status === 'completed' || status === 'cancelled' || status === 'error';

  return (
    <div className="space-y-6">
      {/* Search Header with Quality Slider and Start Button */}
      <SearchHeader
        activeProfile={activeProfile}
        qualityLevel={qualityLevel}
        onQualityChange={setQualityLevel}
        onStartSearch={handleStartSearch}
        isSearching={isSearching}
      />

      {/* Manual Override Panel */}
      <ManualOverride
        override={manualOverride}
        onChange={setManualOverride}
        disabled={isSearching}
      />

      {/* Search Progress */}
      {showProgress && (
        <SearchProgress
          status={status}
          progress={progress}
          sources={sources}
          leadsFound={leads.length}
          onCancel={cancelSearch}
        />
      )}

      {/* Search Results */}
      {showResults && (
        <SearchResults
          leads={leads}
          status={status}
          error={error}
          onRetry={handleRetry}
        />
      )}
    </div>
  );
}
