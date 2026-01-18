"""Analytics computation service."""

from datetime import date, datetime, timedelta, timezone
from typing import Any

from supabase import Client

from src.schemas.analytics import (
    AnalyticsQueryParams,
    IntentScoreCorrelation,
    LeadOutcomeMetrics,
    ProfileAnalyticsResponse,
    ProfileSummary,
    SearchMetrics,
    SourceMetrics,
    TimeGranularity,
    TimeSeriesDataPoint,
    TimeSeriesMetrics,
    UserAnalyticsResponse,
)
from src.schemas.lead import LeadAccuracy, LeadSource, LeadStatus
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Default score buckets for correlation analysis
DEFAULT_SCORE_BUCKETS = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]


class AnalyticsService:
    """
    Service for computing analytics from lead and search data.

    Provides methods for computing metrics at profile and user levels,
    with support for date filtering, source filtering, and time series.
    """

    def __init__(self, supabase: Client) -> None:
        """
        Initialize analytics service.

        Args:
            supabase: Supabase client for database access.
        """
        self.supabase = supabase

    async def get_profile_analytics(
        self,
        profile_id: str,
        params: AnalyticsQueryParams | None = None,
    ) -> ProfileAnalyticsResponse:
        """
        Get analytics for a single client profile.

        Args:
            profile_id: Client profile ID.
            params: Query parameters for filtering.

        Returns:
            ProfileAnalyticsResponse with computed metrics.
        """
        params = params or AnalyticsQueryParams()

        logger.info(
            "computing_profile_analytics",
            profile_id=profile_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )

        # Determine date range
        end_date = params.end_date or date.today()
        start_date = params.start_date or (end_date - timedelta(days=30))
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

        # Fetch leads for the profile
        leads = await self._fetch_leads(profile_id, start_dt, end_dt, params.sources)

        # Compute outcome metrics
        outcome_metrics = self._compute_outcome_metrics(leads)

        # Compute per-source metrics
        source_metrics = self._compute_source_metrics(leads)

        # Compute score correlations
        score_correlations = self._compute_score_correlations(leads)

        # Compute search metrics
        search_metrics = await self._compute_search_metrics(profile_id, start_dt, end_dt)

        # Compute time series if requested
        time_series = None
        if params.include_time_series:
            time_series = self._compute_time_series(
                leads, start_date, end_date, params.time_granularity
            )

        return ProfileAnalyticsResponse(
            profile_id=profile_id,
            period_start=start_dt,
            period_end=end_dt,
            outcome_metrics=outcome_metrics,
            search_metrics=search_metrics,
            source_metrics=source_metrics,
            score_correlations=score_correlations,
            time_series=time_series,
        )

    async def get_user_analytics(
        self,
        user_id: str,
        params: AnalyticsQueryParams | None = None,
    ) -> UserAnalyticsResponse:
        """
        Get aggregated analytics across all user's profiles.

        Args:
            user_id: User ID.
            params: Query parameters for filtering.

        Returns:
            UserAnalyticsResponse with aggregated metrics.
        """
        params = params or AnalyticsQueryParams()

        logger.info(
            "computing_user_analytics",
            user_id=user_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )

        # Determine date range
        end_date = params.end_date or date.today()
        start_date = params.start_date or (end_date - timedelta(days=30))
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

        # Fetch user's profiles
        profiles = await self._fetch_user_profiles(user_id)

        # Aggregate metrics across all profiles
        all_leads: list[dict[str, Any]] = []
        profile_summaries: list[ProfileSummary] = []
        total_searches = SearchMetrics()

        for profile in profiles:
            profile_id = profile["id"]
            profile_name = profile.get("company_name", "Unknown")

            # Fetch leads for this profile
            profile_leads = await self._fetch_leads(
                profile_id, start_dt, end_dt, params.sources
            )
            all_leads.extend(profile_leads)

            # Compute profile summary
            if profile_leads:
                outcome = self._compute_outcome_metrics(profile_leads)
                avg_score = sum(l.get("intent_score", 0) for l in profile_leads) / len(profile_leads)
                profile_summaries.append(ProfileSummary(
                    profile_id=profile_id,
                    profile_name=profile_name,
                    total_leads=outcome.total_leads,
                    conversion_rate=outcome.conversion_rate,
                    accuracy_rate=outcome.accuracy_rate,
                    avg_intent_score=round(avg_score, 2),
                ))
            else:
                profile_summaries.append(ProfileSummary(
                    profile_id=profile_id,
                    profile_name=profile_name,
                ))

            # Accumulate search metrics
            search = await self._compute_search_metrics(profile_id, start_dt, end_dt)
            total_searches.total_searches += search.total_searches
            total_searches.successful_searches += search.successful_searches
            total_searches.failed_searches += search.failed_searches
            total_searches.cancelled_searches += search.cancelled_searches

        # Compute aggregated metrics
        outcome_metrics = self._compute_outcome_metrics(all_leads)
        source_metrics = self._compute_source_metrics(all_leads)

        # Recompute search averages
        if total_searches.total_searches > 0:
            total_searches.avg_leads_per_search = (
                outcome_metrics.total_leads / total_searches.total_searches
            )

        return UserAnalyticsResponse(
            user_id=user_id,
            period_start=start_dt,
            period_end=end_dt,
            profile_count=len(profiles),
            outcome_metrics=outcome_metrics,
            search_metrics=total_searches,
            source_metrics=source_metrics,
            profile_summaries=profile_summaries,
        )

    async def _fetch_leads(
        self,
        profile_id: str,
        start_dt: datetime,
        end_dt: datetime,
        sources: list[LeadSource] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch leads for a profile within date range."""
        try:
            query = (
                self.supabase.table("leads")
                .select("*")
                .eq("client_profile_id", profile_id)
                .gte("created_at", start_dt.isoformat())
                .lte("created_at", end_dt.isoformat())
            )

            if sources:
                query = query.in_("source", [s.value for s in sources])

            result = query.execute()
            return result.data or []

        except Exception as e:
            logger.exception("fetch_leads_failed", profile_id=profile_id, error=str(e))
            return []

    async def _fetch_user_profiles(self, user_id: str) -> list[dict[str, Any]]:
        """Fetch all profiles for a user."""
        try:
            result = (
                self.supabase.table("client_profiles")
                .select("id, company_name")
                .eq("user_id", user_id)
                .execute()
            )
            return result.data or []

        except Exception as e:
            logger.exception("fetch_profiles_failed", user_id=user_id, error=str(e))
            return []

    async def _compute_search_metrics(
        self,
        profile_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> SearchMetrics:
        """Compute search-related metrics."""
        try:
            result = (
                self.supabase.table("searches")
                .select("status, lead_count, sources_queried, sources_successful")
                .eq("client_profile_id", profile_id)
                .gte("started_at", start_dt.isoformat())
                .lte("started_at", end_dt.isoformat())
                .execute()
            )

            searches = result.data or []
            if not searches:
                return SearchMetrics()

            total = len(searches)
            successful = sum(1 for s in searches if s.get("status") == "completed")
            failed = sum(1 for s in searches if s.get("status") == "failed")
            cancelled = sum(1 for s in searches if s.get("status") == "cancelled")

            total_leads = sum(s.get("lead_count", 0) for s in searches)
            total_sources_queried = sum(len(s.get("sources_queried", [])) for s in searches)
            total_sources_successful = sum(len(s.get("sources_successful", [])) for s in searches)

            avg_leads = total_leads / total if total > 0 else 0
            avg_sources = total_sources_queried / total if total > 0 else 0
            avg_success = (
                total_sources_successful / total_sources_queried * 100
                if total_sources_queried > 0
                else 0
            )

            return SearchMetrics(
                total_searches=total,
                successful_searches=successful,
                failed_searches=failed,
                cancelled_searches=cancelled,
                avg_leads_per_search=round(avg_leads, 2),
                avg_sources_per_search=round(avg_sources, 2),
                avg_source_success_rate=round(avg_success, 2),
            )

        except Exception as e:
            logger.exception("compute_search_metrics_failed", error=str(e))
            return SearchMetrics()

    def _compute_outcome_metrics(self, leads: list[dict[str, Any]]) -> LeadOutcomeMetrics:
        """Compute outcome metrics from leads."""
        metrics = LeadOutcomeMetrics(total_leads=len(leads))

        for lead in leads:
            # Status counts
            status = lead.get("status", "new")
            if status == "new":
                metrics.status_new += 1
            elif status == "contacted":
                metrics.status_contacted += 1
            elif status == "responded":
                metrics.status_responded += 1
            elif status == "converted":
                metrics.status_converted += 1
            elif status == "lost":
                metrics.status_lost += 1

            # Accuracy counts
            accuracy = lead.get("accuracy")
            if accuracy == "verified":
                metrics.accuracy_verified += 1
            elif accuracy == "email_bounced":
                metrics.accuracy_email_bounced += 1
            elif accuracy == "phone_invalid":
                metrics.accuracy_phone_invalid += 1
            elif accuracy == "wrong_person":
                metrics.accuracy_wrong_person += 1
            elif accuracy == "company_mismatch":
                metrics.accuracy_company_mismatch += 1
            else:
                metrics.accuracy_unclassified += 1

        return metrics

    def _compute_source_metrics(self, leads: list[dict[str, Any]]) -> list[SourceMetrics]:
        """Compute per-source metrics."""
        # Group leads by source
        source_groups: dict[str, list[dict[str, Any]]] = {}
        for lead in leads:
            source = lead.get("source", "manual")
            if source not in source_groups:
                source_groups[source] = []
            source_groups[source].append(lead)

        metrics = []
        for source_str, source_leads in source_groups.items():
            try:
                source = LeadSource(source_str)
            except ValueError:
                continue

            sm = SourceMetrics(source=source, total_leads=len(source_leads))

            scores = []
            converted_scores = []
            lost_scores = []

            for lead in source_leads:
                score = lead.get("intent_score", 0)
                scores.append(score)

                status = lead.get("status", "new")
                if status == "contacted":
                    sm.leads_contacted += 1
                elif status == "responded":
                    sm.leads_contacted += 1
                    sm.leads_responded += 1
                elif status == "converted":
                    sm.leads_contacted += 1
                    sm.leads_responded += 1
                    sm.leads_converted += 1
                    converted_scores.append(score)
                elif status == "lost":
                    sm.leads_lost += 1
                    lost_scores.append(score)

                accuracy = lead.get("accuracy")
                if accuracy == "verified":
                    sm.leads_verified += 1
                elif accuracy == "email_bounced":
                    sm.leads_email_bounced += 1
                elif accuracy == "phone_invalid":
                    sm.leads_phone_invalid += 1
                elif accuracy == "wrong_person":
                    sm.leads_wrong_person += 1
                elif accuracy == "company_mismatch":
                    sm.leads_company_mismatch += 1

            sm.avg_intent_score = round(sum(scores) / len(scores), 2) if scores else 0.0
            sm.converted_avg_score = (
                round(sum(converted_scores) / len(converted_scores), 2)
                if converted_scores
                else 0.0
            )
            sm.lost_avg_score = (
                round(sum(lost_scores) / len(lost_scores), 2) if lost_scores else 0.0
            )

            metrics.append(sm)

        return metrics

    def _compute_score_correlations(
        self,
        leads: list[dict[str, Any]],
        buckets: list[tuple[int, int]] | None = None,
    ) -> list[IntentScoreCorrelation]:
        """Compute intent score correlations with outcomes."""
        buckets = buckets or DEFAULT_SCORE_BUCKETS
        correlations = []

        for start, end in buckets:
            bucket_leads = [
                l for l in leads
                if start <= l.get("intent_score", 0) < end
            ]

            if not bucket_leads:
                correlations.append(IntentScoreCorrelation(
                    score_range_start=float(start),
                    score_range_end=float(end),
                ))
                continue

            converted = sum(1 for l in bucket_leads if l.get("status") == "converted")
            lost = sum(1 for l in bucket_leads if l.get("status") == "lost")
            responded = sum(
                1 for l in bucket_leads if l.get("status") in ["responded", "converted"]
            )

            correlations.append(IntentScoreCorrelation(
                score_range_start=float(start),
                score_range_end=float(end),
                total_leads=len(bucket_leads),
                converted_count=converted,
                lost_count=lost,
                responded_count=responded,
            ))

        return correlations

    def _compute_time_series(
        self,
        leads: list[dict[str, Any]],
        start_date: date,
        end_date: date,
        granularity: TimeGranularity,
    ) -> TimeSeriesMetrics:
        """Compute time series metrics."""
        # Generate periods
        periods = self._generate_periods(start_date, end_date, granularity)

        data_points = []
        for period_start, period_end in periods:
            # Filter leads for this period
            period_leads = [
                l for l in leads
                if self._lead_in_period(l, period_start, period_end)
            ]

            if not period_leads:
                data_points.append(TimeSeriesDataPoint(
                    period_start=period_start,
                    period_end=period_end,
                ))
                continue

            converted = sum(1 for l in period_leads if l.get("status") == "converted")
            contacted = sum(
                1 for l in period_leads
                if l.get("status") in ["contacted", "responded", "converted"]
            )
            responded = sum(
                1 for l in period_leads if l.get("status") in ["responded", "converted"]
            )
            verified = sum(1 for l in period_leads if l.get("accuracy") == "verified")
            classified = sum(1 for l in period_leads if l.get("accuracy") is not None)

            response_rate = round(responded / contacted * 100, 2) if contacted > 0 else 0.0
            accuracy_rate = round(verified / classified * 100, 2) if classified > 0 else 0.0
            avg_score = round(
                sum(l.get("intent_score", 0) for l in period_leads) / len(period_leads), 2
            )

            data_points.append(TimeSeriesDataPoint(
                period_start=period_start,
                period_end=period_end,
                leads_generated=len(period_leads),
                leads_converted=converted,
                response_rate=response_rate,
                accuracy_rate=accuracy_rate,
                avg_intent_score=avg_score,
            ))

        return TimeSeriesMetrics(
            granularity=granularity,
            start_date=start_date,
            end_date=end_date,
            data_points=data_points,
        )

    def _generate_periods(
        self,
        start_date: date,
        end_date: date,
        granularity: TimeGranularity,
    ) -> list[tuple[date, date]]:
        """Generate time periods based on granularity."""
        periods = []
        current = start_date

        while current <= end_date:
            if granularity == TimeGranularity.DAILY:
                period_end = current
                next_start = current + timedelta(days=1)
            elif granularity == TimeGranularity.WEEKLY:
                period_end = min(current + timedelta(days=6), end_date)
                next_start = current + timedelta(days=7)
            else:  # MONTHLY
                # Approximate month as 30 days
                period_end = min(current + timedelta(days=29), end_date)
                next_start = current + timedelta(days=30)

            periods.append((current, period_end))
            current = next_start

        return periods

    def _lead_in_period(
        self,
        lead: dict[str, Any],
        period_start: date,
        period_end: date,
    ) -> bool:
        """Check if lead falls within period."""
        created_at = lead.get("created_at")
        if not created_at:
            return False

        try:
            if isinstance(created_at, str):
                lead_date = datetime.fromisoformat(
                    created_at.replace("Z", "+00:00")
                ).date()
            else:
                lead_date = created_at.date()
            return period_start <= lead_date <= period_end
        except (ValueError, AttributeError):
            return False
