"""Lead scoring engine implementation."""

import re
from datetime import datetime, timezone
from typing import Any

from src.schemas.lead import CompanySize, LeadSource, ScoreBreakdown
from src.services.scoring.config import (
    BUDGET_NO_SIGNAL_SCORE,
    BUDGET_SCORE_THRESHOLDS,
    COMPANY_SIZE_SCORES,
    COMPILED_PATTERNS,
    ICPTarget,
    INDUSTRY_EXACT_MATCH_MULTIPLIER,
    INDUSTRY_NO_MATCH_MULTIPLIER,
    INDUSTRY_RELATED_MATCH_MULTIPLIER,
    RELATED_INDUSTRIES,
    SOURCE_SCORES,
    TIMING_DEFAULT_SCORE,
    TIMING_THRESHOLDS,
    ScoringWeights,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ScoringEngine:
    """
    Multi-factor lead scoring engine.

    Calculates lead scores based on 6 weighted factors:
    1. Source hierarchy (where the lead came from)
    2. Keywords (intent signals in text)
    3. Company size (fit with ICP)
    4. Timing (recency of the lead)
    5. Budget (explicit budget signals)
    6. Industry (match with target industry)

    Also applies negative signal deductions.
    """

    def __init__(
        self,
        weights: ScoringWeights | None = None,
        target_icp_size: ICPTarget = ICPTarget.ANY,
        target_industries: list[str] | None = None,
    ) -> None:
        """
        Initialize scoring engine with configuration.

        Args:
            weights: Custom scoring weights. Uses defaults if None.
            target_icp_size: Target company size for ICP matching.
            target_industries: List of target industries for matching.
        """
        self.weights = weights or ScoringWeights()
        self.target_icp_size = target_icp_size
        self.target_industries = [i.lower() for i in (target_industries or [])]

    def calculate_score(
        self,
        source: LeadSource,
        text_content: str,
        company_size: CompanySize,
        created_at: datetime | None = None,
        budget_amount: float | None = None,
        lead_industry: str | None = None,
    ) -> ScoreBreakdown:
        """
        Calculate comprehensive lead score.

        Args:
            source: Lead source platform.
            text_content: Combined text (post content, job description, etc.).
            company_size: Company size classification.
            created_at: When the lead was posted/created.
            budget_amount: Explicit budget if detected.
            lead_industry: Industry of the lead's company.

        Returns:
            ScoreBreakdown with all factor scores and final composite.
        """
        # Calculate individual factor scores
        source_score = self._calculate_source_score(source)
        keyword_score = self._calculate_keyword_score(text_content)
        company_size_score = self._calculate_company_size_score(company_size)
        timing_score = self._calculate_timing_score(created_at)
        budget_score = self._calculate_budget_score(text_content, budget_amount)
        industry_multiplier = self._calculate_industry_multiplier(lead_industry)
        negative_deductions = self._calculate_negative_deductions(text_content)

        # Calculate weighted base score
        base_score = (
            source_score * self.weights.source_weight
            + keyword_score * self.weights.keyword_weight
            + company_size_score * self.weights.company_size_weight
            + timing_score * self.weights.timing_weight
            + budget_score * self.weights.budget_weight
        )

        # Normalize to 100 scale (weights should sum to ~1.0)
        weight_sum = (
            self.weights.source_weight
            + self.weights.keyword_weight
            + self.weights.company_size_weight
            + self.weights.timing_weight
            + self.weights.budget_weight
        )

        if weight_sum > 0:
            base_score = base_score / weight_sum

        # Apply industry multiplier
        multiplied_score = base_score * industry_multiplier

        # Apply negative deductions
        final_score = max(0, min(100, multiplied_score + negative_deductions))

        return ScoreBreakdown(
            source_score=round(source_score, 2),
            keyword_score=round(keyword_score, 2),
            company_size_score=round(company_size_score, 2),
            timing_score=round(timing_score, 2),
            budget_score=round(budget_score, 2),
            industry_multiplier=round(industry_multiplier, 2),
            negative_deductions=round(abs(negative_deductions), 2),
            final_score=round(final_score, 2),
        )

    def _calculate_source_score(self, source: LeadSource) -> float:
        """Calculate score based on source hierarchy."""
        return SOURCE_SCORES.get(source, 50.0)

    def _calculate_keyword_score(self, text: str) -> float:
        """
        Calculate score based on intent keywords in text.

        Higher-intent keywords contribute more to the score.
        Returns the highest matching score from each category.
        """
        if not text:
            return 50.0  # Neutral score for empty text

        text_lower = text.lower()
        scores: list[float] = []

        # Check high-intent keywords
        for pattern, score in COMPILED_PATTERNS["high_intent"]:
            if pattern.search(text_lower):
                scores.append(score)
                break  # Take first match from category

        # Check medium-intent keywords
        for pattern, score in COMPILED_PATTERNS["medium_intent"]:
            if pattern.search(text_lower):
                scores.append(score)
                break

        # Check low-intent keywords
        for pattern, score in COMPILED_PATTERNS["low_intent"]:
            if pattern.search(text_lower):
                scores.append(score)
                break

        if not scores:
            return 50.0  # Neutral score if no keywords matched

        # Return weighted average, favoring higher scores
        # Use max * 0.7 + avg * 0.3 to emphasize strongest signal
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)
        return max_score * 0.7 + avg_score * 0.3

    def _calculate_company_size_score(self, company_size: CompanySize) -> float:
        """Calculate score based on company size fit with ICP."""
        size_map = COMPANY_SIZE_SCORES.get(self.target_icp_size, COMPANY_SIZE_SCORES[ICPTarget.ANY])
        return size_map.get(company_size, 50.0)

    def _calculate_timing_score(self, created_at: datetime | None) -> float:
        """Calculate score based on lead recency."""
        if not created_at:
            return 50.0  # Neutral score if no timestamp

        # Ensure timezone-aware comparison
        now = datetime.now(timezone.utc)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        hours_ago = (now - created_at).total_seconds() / 3600

        for threshold_hours, score in TIMING_THRESHOLDS:
            if hours_ago < threshold_hours:
                return score

        return TIMING_DEFAULT_SCORE

    def _calculate_budget_score(
        self,
        text: str,
        explicit_budget: float | None = None,
    ) -> float:
        """
        Calculate score based on budget signals.

        Uses explicit budget if provided, otherwise attempts to extract
        from text content.
        """
        budget_amount = explicit_budget

        if budget_amount is None and text:
            budget_amount = self._extract_budget_from_text(text)

        if budget_amount is None:
            return BUDGET_NO_SIGNAL_SCORE

        for threshold, score in BUDGET_SCORE_THRESHOLDS:
            if budget_amount >= threshold:
                return score

        return BUDGET_SCORE_THRESHOLDS[-1][1]  # Lowest score

    def _extract_budget_from_text(self, text: str) -> float | None:
        """
        Attempt to extract budget amount from text.

        Returns highest amount found.
        """
        # Pattern for currency amounts
        patterns = [
            r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",  # $1,000 or $1000.00
            r"(\d{1,3}(?:,\d{3})*)\s*(?:usd|dollars?)",  # 1000 USD
            r"budget[:\s]+\$?(\d{1,3}(?:,\d{3})*)",  # budget: 5000
        ]

        amounts: list[float] = []

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(",", ""))
                    amounts.append(amount)
                except (ValueError, AttributeError):
                    continue

        return max(amounts) if amounts else None

    def _calculate_industry_multiplier(self, lead_industry: str | None) -> float:
        """
        Calculate industry match multiplier.

        Returns higher multiplier for exact or related industry matches.
        """
        if not lead_industry or not self.target_industries:
            return INDUSTRY_NO_MATCH_MULTIPLIER

        lead_industry_lower = lead_industry.lower()

        # Check for exact match
        if lead_industry_lower in self.target_industries:
            return INDUSTRY_EXACT_MATCH_MULTIPLIER

        # Check for related industry match
        for target_industry in self.target_industries:
            related = RELATED_INDUSTRIES.get(target_industry, [])
            if lead_industry_lower in related:
                return INDUSTRY_RELATED_MATCH_MULTIPLIER

            # Also check reverse - if lead's industry has target as related
            lead_related = RELATED_INDUSTRIES.get(lead_industry_lower, [])
            if target_industry in lead_related:
                return INDUSTRY_RELATED_MATCH_MULTIPLIER

        return INDUSTRY_NO_MATCH_MULTIPLIER

    def _calculate_negative_deductions(self, text: str) -> float:
        """
        Calculate total deductions from negative signals.

        Returns negative value to be added to score.
        """
        if not text:
            return 0.0

        text_lower = text.lower()
        total_deduction = 0.0

        for pattern, deduction in COMPILED_PATTERNS["negative"]:
            if pattern.search(text_lower):
                total_deduction += deduction

        # Cap total deductions to prevent score going too negative
        return max(-80.0, total_deduction)

    def score_raw_lead(
        self,
        raw_data: dict[str, Any],
        source: LeadSource,
    ) -> ScoreBreakdown:
        """
        Score a lead from raw scraped data.

        Extracts relevant fields from raw data and calculates score.

        Args:
            raw_data: Raw scraped data dictionary.
            source: Lead source platform.

        Returns:
            ScoreBreakdown with calculated scores.
        """
        # Extract text content from various possible fields
        text_fields = [
            raw_data.get("title", ""),
            raw_data.get("description", ""),
            raw_data.get("content", ""),
            raw_data.get("body", ""),
            raw_data.get("job_description", ""),
            raw_data.get("post_content", ""),
        ]
        text_content = " ".join(str(f) for f in text_fields if f)

        # Extract company size
        company_size_str = raw_data.get("company_size", "unknown")
        try:
            company_size = CompanySize(company_size_str.lower())
        except ValueError:
            company_size = CompanySize.UNKNOWN

        # Extract timestamp
        created_at = None
        for date_field in ["created_at", "posted_at", "date", "timestamp"]:
            if date_field in raw_data and raw_data[date_field]:
                try:
                    if isinstance(raw_data[date_field], datetime):
                        created_at = raw_data[date_field]
                    else:
                        created_at = datetime.fromisoformat(
                            str(raw_data[date_field]).replace("Z", "+00:00")
                        )
                    break
                except (ValueError, TypeError):
                    continue

        # Extract budget
        budget_amount = None
        for budget_field in ["budget", "budget_amount", "price", "rate"]:
            if budget_field in raw_data and raw_data[budget_field]:
                try:
                    budget_amount = float(raw_data[budget_field])
                    break
                except (ValueError, TypeError):
                    continue

        # Extract industry
        lead_industry = raw_data.get("industry") or raw_data.get("category")

        return self.calculate_score(
            source=source,
            text_content=text_content,
            company_size=company_size,
            created_at=created_at,
            budget_amount=budget_amount,
            lead_industry=str(lead_industry) if lead_industry else None,
        )
