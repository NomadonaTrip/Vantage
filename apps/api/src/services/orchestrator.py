"""Search orchestration service."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Callable

from src.schemas.client_profile import ClientProfile
from src.schemas.lead import CompanySize, Lead, LeadCreate, LeadSource, ScoreBreakdown
from src.schemas.search import (
    ManualSearchParams,
    Search,
    SearchCreate,
    SearchProgressUpdate,
    SearchStatus,
    SearchType,
)
from src.services.scoring import ScoringService
from src.services.sources import (
    AdapterResult,
    RawLead,
    SearchQuery,
    SourceRegistry,
    SourceStatus,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


# Progress callback type
ProgressCallback = Callable[[SearchProgressUpdate], None]


@dataclass
class OrchestrationConfig:
    """Configuration for search orchestration."""

    quality_threshold: float = 0.0  # Minimum score to include (0 = all)
    max_results: int = 50
    dedup_company_threshold: float = 0.85  # Similarity threshold for company dedup
    source_timeout: float = 30.0  # Timeout per source in seconds
    use_mock_sources: bool = False  # Use mock adapters instead of real


@dataclass
class ScoredLead:
    """Lead with scoring information."""

    raw_lead: RawLead
    score_breakdown: ScoreBreakdown
    source: LeadSource

    @property
    def final_score(self) -> float:
        """Get final composite score."""
        return self.score_breakdown.final_score

    @property
    def email(self) -> str | None:
        """Get email for deduplication."""
        return self.raw_lead.email

    @property
    def company(self) -> str:
        """Get company name."""
        return self.raw_lead.company


@dataclass
class OrchestrationResult:
    """Result from search orchestration."""

    search_id: str
    leads: list[ScoredLead] = field(default_factory=list)
    sources_queried: list[LeadSource] = field(default_factory=list)
    sources_successful: list[LeadSource] = field(default_factory=list)
    sources_failed: list[LeadSource] = field(default_factory=list)
    total_raw_leads: int = 0
    total_after_dedup: int = 0
    total_after_filter: int = 0
    execution_time_ms: float = 0.0
    error_message: str | None = None

    @property
    def is_success(self) -> bool:
        """Check if at least one source succeeded."""
        return len(self.sources_successful) > 0

    @property
    def lead_count(self) -> int:
        """Get final lead count."""
        return len(self.leads)


class SearchOrchestrator:
    """
    Orchestrates lead search across multiple sources.

    Coordinates source adapters, scoring, deduplication, and
    result aggregation for a complete search workflow.
    """

    def __init__(
        self,
        source_registry: SourceRegistry,
        config: OrchestrationConfig | None = None,
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            source_registry: Registry of source adapters.
            config: Orchestration configuration.
        """
        self.source_registry = source_registry
        self.config = config or OrchestrationConfig()

    async def execute_search(
        self,
        search_id: str,
        client_profile: ClientProfile,
        search_type: SearchType = SearchType.AUTONOMOUS,
        manual_params: ManualSearchParams | None = None,
        quality_setting: float = 0.7,
        progress_callback: ProgressCallback | None = None,
    ) -> OrchestrationResult:
        """
        Execute a complete search workflow.

        Args:
            search_id: Unique search identifier.
            client_profile: Client profile for context.
            search_type: Search mode (autonomous/manual).
            manual_params: Manual search parameters if applicable.
            quality_setting: Quality vs speed trade-off (0-1).
            progress_callback: Optional callback for progress updates.

        Returns:
            OrchestrationResult with scored and deduplicated leads.
        """
        start_time = datetime.now(timezone.utc)
        logger.info(
            "search_orchestration_started",
            search_id=search_id,
            profile_id=client_profile.id,
            search_type=search_type.value,
        )

        # Select sources to query
        sources = self._select_sources(client_profile, search_type, manual_params)
        if not sources:
            return OrchestrationResult(
                search_id=search_id,
                error_message="No available sources for search",
            )

        # Build search query
        query = self._build_query(client_profile, manual_params, quality_setting)

        # Initialize progress tracking
        progress = SearchProgressUpdate(
            search_id=search_id,
            status=SearchStatus.IN_PROGRESS,
            sources_completed=[],
            sources_pending=list(sources),
            sources_failed=[],
            leads_found=0,
            progress_percent=0.0,
        )

        if progress_callback:
            progress_callback(progress)

        # Query all sources concurrently
        source_results = await self._query_sources(
            sources, query, progress, progress_callback
        )

        # Collect raw leads and track source status
        all_raw_leads: list[RawLead] = []
        sources_successful: list[LeadSource] = []
        sources_failed: list[LeadSource] = []

        for source, result in source_results.items():
            if result.is_success:
                sources_successful.append(source)
                all_raw_leads.extend(result.leads)
            else:
                sources_failed.append(source)
                logger.warning(
                    "source_failed",
                    search_id=search_id,
                    source=source.value,
                    error=result.error_message,
                )

        total_raw = len(all_raw_leads)
        logger.info(
            "raw_leads_collected",
            search_id=search_id,
            total_raw=total_raw,
            sources_successful=len(sources_successful),
            sources_failed=len(sources_failed),
        )

        # Score all leads
        scoring_service = ScoringService(client_profile)
        scored_leads = self._score_leads(all_raw_leads, scoring_service)

        # Deduplicate
        deduped_leads = self._deduplicate_leads(scored_leads)
        total_after_dedup = len(deduped_leads)

        # Filter by quality threshold
        quality_threshold = quality_setting * 30  # Scale 0-1 to 0-30 threshold
        quality_threshold = max(quality_threshold, self.config.quality_threshold)
        filtered_leads = [l for l in deduped_leads if l.final_score >= quality_threshold]
        total_after_filter = len(filtered_leads)

        # Sort by score descending and limit results
        filtered_leads.sort(key=lambda l: l.final_score, reverse=True)
        final_leads = filtered_leads[: self.config.max_results]

        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        logger.info(
            "search_orchestration_completed",
            search_id=search_id,
            total_raw=total_raw,
            total_after_dedup=total_after_dedup,
            total_after_filter=total_after_filter,
            final_count=len(final_leads),
            execution_time_ms=execution_time,
        )

        # Final progress update
        if progress_callback:
            progress.status = SearchStatus.COMPLETED
            progress.leads_found = len(final_leads)
            progress.progress_percent = 100.0
            progress_callback(progress)

        return OrchestrationResult(
            search_id=search_id,
            leads=final_leads,
            sources_queried=sources,
            sources_successful=sources_successful,
            sources_failed=sources_failed,
            total_raw_leads=total_raw,
            total_after_dedup=total_after_dedup,
            total_after_filter=total_after_filter,
            execution_time_ms=execution_time,
        )

    def _select_sources(
        self,
        profile: ClientProfile,
        search_type: SearchType,
        manual_params: ManualSearchParams | None,
    ) -> list[LeadSource]:
        """Select which sources to query based on profile and search type."""
        available = self.source_registry.get_available_sources()

        if search_type == SearchType.MANUAL_OVERRIDE and manual_params:
            # Use only specified sources if provided
            # For now, use all available since manual_params doesn't have source selection
            return available

        # Autonomous mode: select based on profile
        # Prioritize sources based on industry/services
        # For MVP, use all available sources
        return available

    def _build_query(
        self,
        profile: ClientProfile,
        manual_params: ManualSearchParams | None,
        quality_setting: float,
    ) -> SearchQuery:
        """Build search query from profile and manual params."""
        # Start with profile context
        keywords = list(profile.services) if profile.services else []
        keywords.append(profile.industry)

        location = None
        company_sizes = None
        budget_min = None
        budget_max = None
        industry_filter = [profile.industry] if profile.industry else None

        # Override/supplement with manual params
        if manual_params:
            if manual_params.keywords:
                keywords = manual_params.keywords  # Replace
            if manual_params.location:
                location = manual_params.location
            if manual_params.company_sizes:
                company_sizes = manual_params.company_sizes
            if manual_params.budget_min is not None:
                budget_min = manual_params.budget_min
            if manual_params.budget_max is not None:
                budget_max = manual_params.budget_max
            if manual_params.industry_filter:
                industry_filter = manual_params.industry_filter

        # Adjust max results based on quality setting
        # Higher quality = more results to filter from
        max_results = int(30 + quality_setting * 70)  # 30-100 range

        return SearchQuery(
            keywords=keywords,
            location=location,
            company_sizes=company_sizes,
            budget_min=budget_min,
            budget_max=budget_max,
            industry_filter=industry_filter,
            max_results=max_results,
            client_industry=profile.industry,
            client_services=profile.services,
            client_icp=profile.ideal_customer_profile,
        )

    async def _query_sources(
        self,
        sources: list[LeadSource],
        query: SearchQuery,
        progress: SearchProgressUpdate,
        progress_callback: ProgressCallback | None,
    ) -> dict[LeadSource, AdapterResult]:
        """Query all sources concurrently with progress tracking."""

        async def query_with_progress(source: LeadSource) -> tuple[LeadSource, AdapterResult]:
            result = await self.source_registry.search(
                source, query, self.config.source_timeout
            )

            # Update progress
            if source in progress.sources_pending:
                progress.sources_pending.remove(source)

            if result.is_success:
                progress.sources_completed.append(source)
                progress.leads_found += result.lead_count
            else:
                progress.sources_failed.append(source)

            total_sources = len(sources)
            completed = len(progress.sources_completed) + len(progress.sources_failed)
            progress.progress_percent = (completed / total_sources) * 100

            if progress_callback:
                progress_callback(progress)

            return source, result

        # Execute all queries concurrently
        tasks = [query_with_progress(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        source_results: dict[LeadSource, AdapterResult] = {}
        for item in results:
            if isinstance(item, Exception):
                logger.exception("source_query_exception", error=str(item))
                continue
            source, result = item
            source_results[source] = result

        return source_results

    def _score_leads(
        self,
        raw_leads: list[RawLead],
        scoring_service: ScoringService,
    ) -> list[ScoredLead]:
        """Score all raw leads using the scoring engine."""
        scored = []
        for lead in raw_leads:
            try:
                # Build text content for scoring
                text_parts = [lead.title or "", lead.description or ""]
                text_content = " ".join(filter(None, text_parts))

                score_breakdown = scoring_service.score_lead(
                    source=lead.source,
                    text_content=text_content,
                    company_size=lead.company_size,
                    created_at=lead.created_at,
                    budget_amount=lead.budget,
                    lead_industry=lead.industry,
                )

                scored.append(ScoredLead(
                    raw_lead=lead,
                    score_breakdown=score_breakdown,
                    source=lead.source,
                ))
            except Exception as e:
                logger.warning(
                    "lead_scoring_failed",
                    lead_name=lead.name,
                    error=str(e),
                )

        return scored

    def _deduplicate_leads(self, leads: list[ScoredLead]) -> list[ScoredLead]:
        """
        Deduplicate leads based on email and company similarity.

        Keeps the highest-scoring lead for each duplicate group.
        """
        if not leads:
            return []

        # Sort by score descending so we keep highest scores
        sorted_leads = sorted(leads, key=lambda l: l.final_score, reverse=True)

        seen_emails: set[str] = set()
        seen_companies: dict[str, ScoredLead] = {}  # Normalized company -> lead
        deduped: list[ScoredLead] = []

        for lead in sorted_leads:
            # Check email dedup
            if lead.email:
                email_lower = lead.email.lower()
                if email_lower in seen_emails:
                    continue
                seen_emails.add(email_lower)

            # Check company similarity dedup
            company_normalized = self._normalize_company(lead.company)
            is_duplicate = False

            for seen_company in seen_companies:
                similarity = SequenceMatcher(
                    None, company_normalized, seen_company
                ).ratio()
                if similarity >= self.config.dedup_company_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen_companies[company_normalized] = lead
                deduped.append(lead)

        return deduped

    def _normalize_company(self, company: str) -> str:
        """Normalize company name for comparison."""
        # Remove common suffixes and normalize
        normalized = company.lower().strip()
        for suffix in [" inc", " inc.", " llc", " ltd", " ltd.", " corp", " corp."]:
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
        return normalized.strip()

    def convert_to_lead_creates(
        self,
        result: OrchestrationResult,
        client_profile_id: str,
    ) -> list[LeadCreate]:
        """
        Convert orchestration result to LeadCreate objects for persistence.

        Args:
            result: Orchestration result with scored leads.
            client_profile_id: Profile ID to associate leads with.

        Returns:
            List of LeadCreate objects ready for database insertion.
        """
        lead_creates = []

        for scored_lead in result.leads:
            raw = scored_lead.raw_lead
            lead_creates.append(LeadCreate(
                client_profile_id=client_profile_id,
                search_id=result.search_id,
                name=raw.name,
                email=raw.email,
                phone=raw.phone,
                company=raw.company,
                company_size=raw.company_size,
                intent_score=scored_lead.final_score,
                score_breakdown=scored_lead.score_breakdown,
                source=raw.source,
                source_url=raw.source_url,
                raw_data=raw.raw_data,
            ))

        return lead_creates
