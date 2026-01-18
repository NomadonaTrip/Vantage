"use client";

import { create } from "zustand";

interface SourceMetrics {
  source: string;
  total_leads: number;
  leads_contacted: number;
  leads_responded: number;
  leads_converted: number;
  leads_lost: number;
  leads_verified: number;
  leads_email_bounced: number;
  leads_phone_invalid: number;
  avg_intent_score: number;
  response_rate: number;
  conversion_rate: number;
  accuracy_rate: number;
}

interface OutcomeMetrics {
  total_leads: number;
  status_new: number;
  status_contacted: number;
  status_responded: number;
  status_converted: number;
  status_lost: number;
  accuracy_verified: number;
  accuracy_email_bounced: number;
  accuracy_phone_invalid: number;
  accuracy_wrong_person: number;
  accuracy_company_mismatch: number;
  accuracy_unclassified: number;
  response_rate: number;
  conversion_rate: number;
  accuracy_rate: number;
}

interface SearchMetrics {
  total_searches: number;
  successful_searches: number;
  failed_searches: number;
  cancelled_searches: number;
  avg_leads_per_search: number;
  avg_sources_per_search: number;
  avg_source_success_rate: number;
  success_rate: number;
}

interface ScoreCorrelation {
  score_range_start: number;
  score_range_end: number;
  total_leads: number;
  converted_count: number;
  lost_count: number;
  responded_count: number;
  conversion_rate: number;
  response_rate: number;
}

interface TimeSeriesDataPoint {
  period_start: string;
  period_end: string;
  leads_generated: number;
  leads_converted: number;
  response_rate: number;
  accuracy_rate: number;
  avg_intent_score: number;
}

interface TimeSeriesMetrics {
  granularity: string;
  start_date: string;
  end_date: string;
  data_points: TimeSeriesDataPoint[];
}

interface ProfileAnalytics {
  profile_id: string;
  period_start: string;
  period_end: string;
  outcome_metrics: OutcomeMetrics;
  search_metrics: SearchMetrics;
  source_metrics: SourceMetrics[];
  score_correlations: ScoreCorrelation[];
  time_series: TimeSeriesMetrics | null;
}

interface ProfileSummary {
  profile_id: string;
  profile_name: string;
  total_leads: number;
  conversion_rate: number;
  accuracy_rate: number;
  avg_intent_score: number;
}

interface UserAnalytics {
  user_id: string;
  period_start: string;
  period_end: string;
  profile_count: number;
  outcome_metrics: OutcomeMetrics;
  search_metrics: SearchMetrics;
  source_metrics: SourceMetrics[];
  profile_summaries: ProfileSummary[];
}

interface AnalyticsState {
  profileAnalytics: ProfileAnalytics | null;
  userAnalytics: UserAnalytics | null;
  isLoading: boolean;
  error: string | null;

  fetchProfileAnalytics: (
    token: string,
    startDate?: string,
    endDate?: string,
    includeTimeSeries?: boolean,
    granularity?: string
  ) => Promise<void>;

  fetchUserAnalytics: (
    token: string,
    startDate?: string,
    endDate?: string
  ) => Promise<void>;

  clearAnalytics: () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const useAnalyticsStore = create<AnalyticsState>((set) => ({
  profileAnalytics: null,
  userAnalytics: null,
  isLoading: false,
  error: null,

  fetchProfileAnalytics: async (
    token,
    startDate,
    endDate,
    includeTimeSeries = false,
    granularity = "weekly"
  ) => {
    set({ isLoading: true, error: null });

    try {
      const params = new URLSearchParams();
      if (startDate) params.append("start_date", startDate);
      if (endDate) params.append("end_date", endDate);
      params.append("include_time_series", String(includeTimeSeries));
      params.append("granularity", granularity);

      const response = await fetch(
        `${API_BASE}/v1/analytics/profile?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch profile analytics");
      }

      const data: ProfileAnalytics = await response.json();
      set({ profileAnalytics: data, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Unknown error",
        isLoading: false,
      });
    }
  },

  fetchUserAnalytics: async (token, startDate, endDate) => {
    set({ isLoading: true, error: null });

    try {
      const params = new URLSearchParams();
      if (startDate) params.append("start_date", startDate);
      if (endDate) params.append("end_date", endDate);

      const response = await fetch(
        `${API_BASE}/v1/analytics/user?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch user analytics");
      }

      const data: UserAnalytics = await response.json();
      set({ userAnalytics: data, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Unknown error",
        isLoading: false,
      });
    }
  },

  clearAnalytics: () => {
    set({ profileAnalytics: null, userAnalytics: null, error: null });
  },
}));
