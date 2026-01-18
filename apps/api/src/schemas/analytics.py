"""Analytics schema definitions."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field

from src.schemas.lead import LeadAccuracy, LeadSource, LeadStatus


class TimeGranularity(str, Enum):
    """Time granularity for aggregations."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class SourceMetrics(BaseModel):
    """Metrics for a single lead source."""

    source: LeadSource
    total_leads: int = Field(default=0, ge=0)
    leads_contacted: int = Field(default=0, ge=0)
    leads_responded: int = Field(default=0, ge=0)
    leads_converted: int = Field(default=0, ge=0)
    leads_lost: int = Field(default=0, ge=0)

    # Accuracy metrics
    leads_verified: int = Field(default=0, ge=0)
    leads_email_bounced: int = Field(default=0, ge=0)
    leads_phone_invalid: int = Field(default=0, ge=0)
    leads_wrong_person: int = Field(default=0, ge=0)
    leads_company_mismatch: int = Field(default=0, ge=0)

    # Scoring metrics
    avg_intent_score: float = Field(default=0.0, ge=0, le=100)
    converted_avg_score: float = Field(default=0.0, ge=0, le=100)
    lost_avg_score: float = Field(default=0.0, ge=0, le=100)

    @property
    def response_rate(self) -> float:
        """Calculate response rate (responded / contacted)."""
        if self.leads_contacted == 0:
            return 0.0
        return round(self.leads_responded / self.leads_contacted * 100, 2)

    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate (converted / total)."""
        if self.total_leads == 0:
            return 0.0
        return round(self.leads_converted / self.total_leads * 100, 2)

    @property
    def accuracy_rate(self) -> float:
        """Calculate accuracy rate (verified / total with feedback)."""
        total_feedback = (
            self.leads_verified
            + self.leads_email_bounced
            + self.leads_phone_invalid
            + self.leads_wrong_person
            + self.leads_company_mismatch
        )
        if total_feedback == 0:
            return 0.0
        return round(self.leads_verified / total_feedback * 100, 2)

    @property
    def feedback_capture_rate(self) -> float:
        """Calculate feedback capture rate."""
        total_feedback = (
            self.leads_verified
            + self.leads_email_bounced
            + self.leads_phone_invalid
            + self.leads_wrong_person
            + self.leads_company_mismatch
        )
        if self.total_leads == 0:
            return 0.0
        return round(total_feedback / self.total_leads * 100, 2)


class LeadOutcomeMetrics(BaseModel):
    """Metrics aggregating lead outcomes."""

    total_leads: int = Field(default=0, ge=0)

    # Status distribution
    status_new: int = Field(default=0, ge=0)
    status_contacted: int = Field(default=0, ge=0)
    status_responded: int = Field(default=0, ge=0)
    status_converted: int = Field(default=0, ge=0)
    status_lost: int = Field(default=0, ge=0)

    # Accuracy distribution
    accuracy_verified: int = Field(default=0, ge=0)
    accuracy_email_bounced: int = Field(default=0, ge=0)
    accuracy_phone_invalid: int = Field(default=0, ge=0)
    accuracy_wrong_person: int = Field(default=0, ge=0)
    accuracy_company_mismatch: int = Field(default=0, ge=0)
    accuracy_unclassified: int = Field(default=0, ge=0)

    @property
    def response_rate(self) -> float:
        """Overall response rate."""
        if self.status_contacted == 0:
            return 0.0
        return round(self.status_responded / self.status_contacted * 100, 2)

    @property
    def conversion_rate(self) -> float:
        """Overall conversion rate."""
        if self.total_leads == 0:
            return 0.0
        return round(self.status_converted / self.total_leads * 100, 2)

    @property
    def accuracy_rate(self) -> float:
        """Overall accuracy rate (verified / classified)."""
        total_classified = (
            self.accuracy_verified
            + self.accuracy_email_bounced
            + self.accuracy_phone_invalid
            + self.accuracy_wrong_person
            + self.accuracy_company_mismatch
        )
        if total_classified == 0:
            return 0.0
        return round(self.accuracy_verified / total_classified * 100, 2)


class IntentScoreCorrelation(BaseModel):
    """Correlation between intent scores and outcomes."""

    score_range_start: float = Field(ge=0, le=100)
    score_range_end: float = Field(ge=0, le=100)
    total_leads: int = Field(default=0, ge=0)
    converted_count: int = Field(default=0, ge=0)
    lost_count: int = Field(default=0, ge=0)
    responded_count: int = Field(default=0, ge=0)

    @property
    def conversion_rate(self) -> float:
        """Conversion rate for this score range."""
        if self.total_leads == 0:
            return 0.0
        return round(self.converted_count / self.total_leads * 100, 2)

    @property
    def response_rate(self) -> float:
        """Response rate for this score range."""
        if self.total_leads == 0:
            return 0.0
        return round(self.responded_count / self.total_leads * 100, 2)


class SearchMetrics(BaseModel):
    """Metrics for search operations."""

    total_searches: int = Field(default=0, ge=0)
    successful_searches: int = Field(default=0, ge=0)
    failed_searches: int = Field(default=0, ge=0)
    cancelled_searches: int = Field(default=0, ge=0)

    avg_leads_per_search: float = Field(default=0.0, ge=0)
    avg_sources_per_search: float = Field(default=0.0, ge=0)
    avg_source_success_rate: float = Field(default=0.0, ge=0, le=100)

    @property
    def success_rate(self) -> float:
        """Search success rate."""
        if self.total_searches == 0:
            return 0.0
        return round(self.successful_searches / self.total_searches * 100, 2)


class TimeSeriesDataPoint(BaseModel):
    """Single data point in time series."""

    period_start: date
    period_end: date
    leads_generated: int = Field(default=0, ge=0)
    leads_converted: int = Field(default=0, ge=0)
    response_rate: float = Field(default=0.0, ge=0, le=100)
    accuracy_rate: float = Field(default=0.0, ge=0, le=100)
    avg_intent_score: float = Field(default=0.0, ge=0, le=100)


class TimeSeriesMetrics(BaseModel):
    """Time series metrics for trend analysis."""

    granularity: TimeGranularity
    start_date: date
    end_date: date
    data_points: list[TimeSeriesDataPoint] = Field(default_factory=list)


class ProfileAnalyticsResponse(BaseModel):
    """Analytics response for a single client profile."""

    profile_id: str
    period_start: datetime
    period_end: datetime

    # Aggregate metrics
    outcome_metrics: LeadOutcomeMetrics
    search_metrics: SearchMetrics

    # Per-source breakdown
    source_metrics: list[SourceMetrics] = Field(default_factory=list)

    # Score correlation
    score_correlations: list[IntentScoreCorrelation] = Field(default_factory=list)

    # Time series (optional, if requested)
    time_series: TimeSeriesMetrics | None = None


class UserAnalyticsResponse(BaseModel):
    """Analytics response aggregated across all user's profiles."""

    user_id: str
    period_start: datetime
    period_end: datetime
    profile_count: int = Field(default=0, ge=0)

    # Aggregate metrics across all profiles
    outcome_metrics: LeadOutcomeMetrics
    search_metrics: SearchMetrics

    # Per-source breakdown (aggregated)
    source_metrics: list[SourceMetrics] = Field(default_factory=list)

    # Per-profile summaries
    profile_summaries: list["ProfileSummary"] = Field(default_factory=list)


class ProfileSummary(BaseModel):
    """Brief summary of a profile's analytics."""

    profile_id: str
    profile_name: str
    total_leads: int = Field(default=0, ge=0)
    conversion_rate: float = Field(default=0.0, ge=0, le=100)
    accuracy_rate: float = Field(default=0.0, ge=0, le=100)
    avg_intent_score: float = Field(default=0.0, ge=0, le=100)


class AnalyticsQueryParams(BaseModel):
    """Query parameters for analytics requests."""

    start_date: date | None = None
    end_date: date | None = None
    include_time_series: bool = False
    time_granularity: TimeGranularity = TimeGranularity.WEEKLY
    sources: list[LeadSource] | None = None  # Filter by sources
