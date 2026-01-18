"use client";

import { useEffect, useState } from "react";

import { MetricsCards } from "@/components/analytics/metrics-cards";
import { ScoreCorrelationChart } from "@/components/analytics/score-correlation";
import { SourceBreakdown } from "@/components/analytics/source-breakdown";
import { useAnalyticsStore } from "@/stores/analytics-store";
import { useAuthStore } from "@/stores/auth-store";
import { useClientStore } from "@/stores/client-store";

export default function AnalyticsPage() {
  const { session } = useAuthStore();
  const { activeProfile } = useClientStore();
  const {
    profileAnalytics,
    isLoading,
    error,
    fetchProfileAnalytics,
    clearAnalytics,
  } = useAnalyticsStore();

  const [startDate, setStartDate] = useState<string>(() => {
    const date = new Date();
    date.setDate(date.getDate() - 30);
    return date.toISOString().split("T")[0];
  });
  const [endDate, setEndDate] = useState<string>(() => {
    return new Date().toISOString().split("T")[0];
  });

  useEffect(() => {
    if (session?.access_token && activeProfile) {
      fetchProfileAnalytics(session.access_token, startDate, endDate, true);
    }
  }, [session?.access_token, activeProfile?.id, startDate, endDate, fetchProfileAnalytics]);

  // Clear analytics when profile changes
  useEffect(() => {
    clearAnalytics();
  }, [activeProfile?.id, clearAnalytics]);

  const handleDateChange = (start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
  };

  if (!session) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Please log in to view analytics.</p>
      </div>
    );
  }

  if (!activeProfile) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          No Active Profile
        </h2>
        <p className="text-gray-500 dark:text-gray-400">
          Please select a client profile to view analytics.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Analytics
          </h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">
            Lead generation performance for {activeProfile.company_name}
          </p>
        </div>

        {/* Date Range Picker */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-500 dark:text-gray-400">From:</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => handleDateChange(e.target.value, endDate)}
            className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <label className="text-sm text-gray-500 dark:text-gray-400">To:</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => handleDateChange(startDate, e.target.value)}
            className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          <span className="ml-3 text-gray-500">Loading analytics...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-700 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Analytics Content */}
      {profileAnalytics && !isLoading && (
        <>
          {/* Metrics Cards */}
          <MetricsCards
            outcomeMetrics={profileAnalytics.outcome_metrics}
            searchMetrics={profileAnalytics.search_metrics}
          />

          {/* Two Column Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Source Breakdown */}
            <SourceBreakdown sourceMetrics={profileAnalytics.source_metrics} />

            {/* Score Correlation */}
            <ScoreCorrelationChart
              correlations={profileAnalytics.score_correlations}
            />
          </div>

          {/* Status Distribution */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Lead Status Distribution
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
              <StatusCard
                label="New"
                count={profileAnalytics.outcome_metrics.status_new}
                total={profileAnalytics.outcome_metrics.total_leads}
                color="bg-gray-500"
              />
              <StatusCard
                label="Contacted"
                count={profileAnalytics.outcome_metrics.status_contacted}
                total={profileAnalytics.outcome_metrics.total_leads}
                color="bg-blue-500"
              />
              <StatusCard
                label="Responded"
                count={profileAnalytics.outcome_metrics.status_responded}
                total={profileAnalytics.outcome_metrics.total_leads}
                color="bg-yellow-500"
              />
              <StatusCard
                label="Converted"
                count={profileAnalytics.outcome_metrics.status_converted}
                total={profileAnalytics.outcome_metrics.total_leads}
                color="bg-green-500"
              />
              <StatusCard
                label="Lost"
                count={profileAnalytics.outcome_metrics.status_lost}
                total={profileAnalytics.outcome_metrics.total_leads}
                color="bg-red-500"
              />
            </div>
          </div>

          {/* Period Info */}
          <div className="text-center text-sm text-gray-400">
            Showing data from{" "}
            {new Date(profileAnalytics.period_start).toLocaleDateString()} to{" "}
            {new Date(profileAnalytics.period_end).toLocaleDateString()}
          </div>
        </>
      )}

      {/* Empty State */}
      {!profileAnalytics && !isLoading && !error && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            No analytics data available for this period.
          </p>
        </div>
      )}
    </div>
  );
}

function StatusCard({
  label,
  count,
  total,
  color,
}: {
  label: string;
  count: number;
  total: number;
  color: string;
}) {
  const percentage = total > 0 ? (count / total) * 100 : 0;

  return (
    <div className="text-center">
      <div className={`w-8 h-8 ${color} rounded-full mx-auto mb-2 flex items-center justify-center`}>
        <span className="text-white text-xs font-bold">{count}</span>
      </div>
      <div className="text-sm font-medium text-gray-900 dark:text-white">{label}</div>
      <div className="text-xs text-gray-500 dark:text-gray-400">
        {percentage.toFixed(1)}%
      </div>
    </div>
  );
}
