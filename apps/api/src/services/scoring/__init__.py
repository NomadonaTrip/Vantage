"""Scoring service module."""

from typing import Any

from src.schemas.client_profile import ClientProfile
from src.schemas.lead import CompanySize, LeadSource, ScoreBreakdown
from src.services.scoring.config import ICPTarget, ScoringWeights
from src.services.scoring.engine import ScoringEngine
from src.utils.logging import get_logger

logger = get_logger(__name__)

__all__ = [
    "ScoringService",
    "ScoringEngine",
    "ScoringWeights",
    "ICPTarget",
]


class ScoringService:
    """
    Service for lead scoring with client profile integration.

    Wraps the ScoringEngine and provides configuration based on
    client profile settings.
    """

    def __init__(self, client_profile: ClientProfile | None = None) -> None:
        """
        Initialize scoring service.

        Args:
            client_profile: Client profile for configuration.
                If provided, uses profile's scoring weights and ICP.
        """
        self.client_profile = client_profile
        self.engine = self._create_engine()

    def _create_engine(self) -> ScoringEngine:
        """Create scoring engine with appropriate configuration."""
        weights = None
        target_icp_size = ICPTarget.ANY
        target_industries: list[str] = []

        if self.client_profile:
            # Extract custom weights from profile if available
            if self.client_profile.scoring_weight_overrides:
                try:
                    profile_weights = self.client_profile.scoring_weight_overrides
                    # Convert from client_profile ScoringWeights to config ScoringWeights
                    weights = ScoringWeights(
                        source_weight=profile_weights.source_weight,
                        keyword_weight=profile_weights.keyword_weight,
                        company_size_weight=profile_weights.company_size_weight,
                        timing_weight=profile_weights.timing_weight,
                        budget_weight=profile_weights.budget_weight,
                    )
                    logger.info(
                        "using_custom_scoring_weights",
                        profile_id=self.client_profile.id,
                    )
                except Exception as e:
                    logger.warning(
                        "invalid_scoring_weights_in_profile",
                        profile_id=self.client_profile.id,
                        error=str(e),
                    )

            # Extract target ICP size from profile's ideal_customer_profile
            target_icp_size = self._extract_icp_target()

            # Extract target industries
            if self.client_profile.industry:
                target_industries = [self.client_profile.industry]

        return ScoringEngine(
            weights=weights,
            target_icp_size=target_icp_size,
            target_industries=target_industries,
        )

    def _extract_icp_target(self) -> ICPTarget:
        """
        Extract target company size from client profile's ICP.

        Analyzes the ideal_customer_profile text to determine
        target company size preference.
        """
        if not self.client_profile or not self.client_profile.ideal_customer_profile:
            return ICPTarget.ANY

        icp_lower = self.client_profile.ideal_customer_profile.lower()

        # Check for size indicators in ICP
        if any(term in icp_lower for term in ["enterprise", "large company", "fortune 500", "corporate"]):
            return ICPTarget.ENTERPRISE
        elif any(term in icp_lower for term in ["mid-size", "medium", "growing company", "scale-up"]):
            return ICPTarget.MEDIUM
        elif any(term in icp_lower for term in ["small business", "smb", "startup", "small team"]):
            return ICPTarget.SMALL
        elif any(term in icp_lower for term in ["solopreneur", "freelancer", "individual", "solo"]):
            return ICPTarget.SOLO

        return ICPTarget.ANY

    def score_lead(
        self,
        source: LeadSource,
        text_content: str,
        company_size: CompanySize = CompanySize.UNKNOWN,
        created_at: Any = None,
        budget_amount: float | None = None,
        lead_industry: str | None = None,
    ) -> ScoreBreakdown:
        """
        Score a lead.

        Args:
            source: Lead source platform.
            text_content: Text content to analyze.
            company_size: Company size classification.
            created_at: When the lead was created.
            budget_amount: Explicit budget if known.
            lead_industry: Industry of the lead.

        Returns:
            ScoreBreakdown with all scores.
        """
        return self.engine.calculate_score(
            source=source,
            text_content=text_content,
            company_size=company_size,
            created_at=created_at,
            budget_amount=budget_amount,
            lead_industry=lead_industry,
        )

    def score_raw_lead(
        self,
        raw_data: dict[str, Any],
        source: LeadSource,
    ) -> ScoreBreakdown:
        """
        Score a lead from raw scraped data.

        Args:
            raw_data: Raw data dictionary from scraper.
            source: Lead source platform.

        Returns:
            ScoreBreakdown with calculated scores.
        """
        return self.engine.score_raw_lead(raw_data, source)

    def update_profile(self, client_profile: ClientProfile) -> None:
        """
        Update scoring service with new client profile.

        Args:
            client_profile: New client profile to use.
        """
        self.client_profile = client_profile
        self.engine = self._create_engine()

    @staticmethod
    def get_default_weights() -> ScoringWeights:
        """Get default scoring weights."""
        return ScoringWeights()

    @staticmethod
    def get_weight_descriptions() -> dict[str, str]:
        """Get descriptions for each weight factor."""
        return {
            "source_weight": "Weight for source platform hierarchy (Upwork, Reddit, etc.)",
            "keyword_weight": "Weight for intent keywords in text (hiring, budget, etc.)",
            "company_size_weight": "Weight for company size fit with your ICP",
            "timing_weight": "Weight for lead recency/freshness",
            "budget_weight": "Weight for budget signals and amounts",
        }
