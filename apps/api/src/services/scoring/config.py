"""Scoring configuration with default weights and patterns."""

import re
from enum import Enum

from pydantic import BaseModel, Field

from src.schemas.lead import CompanySize, LeadSource


class ScoringWeights(BaseModel):
    """Configurable weights for each scoring factor."""

    source_weight: float = Field(default=0.20, ge=0, le=1, description="Weight for source hierarchy score")
    keyword_weight: float = Field(default=0.25, ge=0, le=1, description="Weight for keyword match score")
    company_size_weight: float = Field(default=0.15, ge=0, le=1, description="Weight for company size fit")
    timing_weight: float = Field(default=0.15, ge=0, le=1, description="Weight for timing/recency")
    budget_weight: float = Field(default=0.25, ge=0, le=1, description="Weight for budget signals")

    class Config:
        """Pydantic config."""

        validate_assignment = True


# Source hierarchy scores (higher = more intent-driven)
SOURCE_SCORES: dict[LeadSource, float] = {
    LeadSource.MANUAL: 100.0,    # User-provided, highest trust
    LeadSource.UPWORK: 90.0,     # Explicit project posts with budget
    LeadSource.REDDIT: 85.0,     # Intent signals in posts/comments
    LeadSource.APOLLO: 75.0,     # Company data enrichment
    LeadSource.CLUTCH: 70.0,     # Agency directory listings
    LeadSource.BING: 50.0,       # General web search
    LeadSource.GOOGLE: 50.0,     # General web search
}


# Company size scoring based on target ICP
class ICPTarget(str, Enum):
    """Target ICP size preferences."""

    SOLO = "solo"           # Targeting solopreneurs
    SMALL = "small"         # Targeting small businesses (2-10)
    MEDIUM = "medium"       # Targeting medium businesses (11-50)
    ENTERPRISE = "enterprise"  # Targeting enterprises (50+)
    ANY = "any"             # No preference


# Company size fit scores based on ICP target
COMPANY_SIZE_SCORES: dict[ICPTarget, dict[CompanySize, float]] = {
    ICPTarget.SOLO: {
        CompanySize.SOLO: 100.0,
        CompanySize.SMALL: 60.0,
        CompanySize.MEDIUM: 30.0,
        CompanySize.ENTERPRISE: 10.0,
        CompanySize.UNKNOWN: 50.0,
    },
    ICPTarget.SMALL: {
        CompanySize.SOLO: 50.0,
        CompanySize.SMALL: 100.0,
        CompanySize.MEDIUM: 70.0,
        CompanySize.ENTERPRISE: 40.0,
        CompanySize.UNKNOWN: 50.0,
    },
    ICPTarget.MEDIUM: {
        CompanySize.SOLO: 20.0,
        CompanySize.SMALL: 50.0,
        CompanySize.MEDIUM: 100.0,
        CompanySize.ENTERPRISE: 80.0,
        CompanySize.UNKNOWN: 50.0,
    },
    ICPTarget.ENTERPRISE: {
        CompanySize.SOLO: 10.0,
        CompanySize.SMALL: 30.0,
        CompanySize.MEDIUM: 60.0,
        CompanySize.ENTERPRISE: 100.0,
        CompanySize.UNKNOWN: 50.0,
    },
    ICPTarget.ANY: {
        CompanySize.SOLO: 80.0,
        CompanySize.SMALL: 80.0,
        CompanySize.MEDIUM: 80.0,
        CompanySize.ENTERPRISE: 80.0,
        CompanySize.UNKNOWN: 50.0,
    },
}


# Timing score thresholds (hours)
TIMING_THRESHOLDS: list[tuple[int, float]] = [
    (24, 100.0),       # < 24 hours: 100
    (24 * 7, 80.0),    # < 7 days: 80
    (24 * 30, 60.0),   # < 30 days: 60
    (24 * 90, 40.0),   # < 90 days: 40
]
TIMING_DEFAULT_SCORE = 20.0  # > 90 days


# High-intent keywords with scores
HIGH_INTENT_KEYWORDS: list[tuple[str, float]] = [
    (r"\b(looking\s+for|need\s+help\s+with|hiring|seeking)\b", 90.0),
    (r"\b(budget|willing\s+to\s+pay|ready\s+to\s+start)\b", 85.0),
    (r"\b(urgent|asap|immediately|deadline)\b", 80.0),
    (r"\b(contract|project|engagement|retainer)\b", 75.0),
]

MEDIUM_INTENT_KEYWORDS: list[tuple[str, float]] = [
    (r"\b(interested|exploring|considering)\b", 60.0),
    (r"\b(might\s+need|could\s+use|thinking\s+about)\b", 55.0),
    (r"\b(recommendations|suggestions|advice)\b", 50.0),
]

LOW_INTENT_KEYWORDS: list[tuple[str, float]] = [
    (r"\b(just\s+curious|wondering|anyone\s+know)\b", 30.0),
    (r"\b(maybe|someday|eventually)\b", 25.0),
]


# Negative signals with deductions
NEGATIVE_SIGNALS: list[tuple[str, float]] = [
    # Financial constraints - highest deductions
    (r"\b(free|no\s+budget|pro\s+bono|cheap|lowest\s+price)\b", -40.0),
    (r"\b(can['\s]?t\s+afford|tight\s+budget|limited\s+budget)\b", -35.0),

    # Educational/non-commercial - medium-high deductions
    (r"\b(student|school\s+project|university|college|thesis)\b", -30.0),
    (r"\b(homework|assignment|coursework|class\s+project)\b", -30.0),

    # Hobbyist/personal - medium deductions
    (r"\b(learning|hobby|personal\s+project|side\s+project)\b", -25.0),
    (r"\b(just\s+for\s+fun|playing\s+around|experimenting)\b", -25.0),

    # Non-commercial work - lower deductions
    (r"\b(internship|volunteer|nonprofit|charity)\b", -20.0),
    (r"\b(open\s+source|community|contribute)\b", -15.0),
]


# Budget signal patterns and scores
BUDGET_PATTERNS: list[tuple[str, tuple[float, float], float]] = [
    # Pattern, (min_amount, max_amount), score
    (r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*[-–to]\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)", None, None),  # Range
    (r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)", None, None),  # Single amount
    (r"(\d{1,3}(?:,\d{3})*)\s*(?:usd|dollars?)", None, None),  # Written currency
]

# Budget amount thresholds for scoring
BUDGET_SCORE_THRESHOLDS: list[tuple[float, float]] = [
    (50000, 100.0),   # $50k+: 100
    (20000, 90.0),    # $20k-50k: 90
    (10000, 80.0),    # $10k-20k: 80
    (5000, 70.0),     # $5k-10k: 70
    (2000, 60.0),     # $2k-5k: 60
    (1000, 50.0),     # $1k-2k: 50
    (500, 40.0),      # $500-1k: 40
    (100, 30.0),      # $100-500: 30
    (0, 20.0),        # <$100: 20
]
BUDGET_NO_SIGNAL_SCORE = 50.0  # No budget mentioned


# Industry matching
RELATED_INDUSTRIES: dict[str, list[str]] = {
    "software": ["technology", "saas", "fintech", "healthtech", "edtech", "e-commerce"],
    "technology": ["software", "saas", "fintech", "healthtech", "edtech", "hardware"],
    "finance": ["fintech", "banking", "insurance", "investment", "accounting"],
    "healthcare": ["healthtech", "medical", "pharmaceutical", "biotechnology"],
    "retail": ["e-commerce", "consumer goods", "fashion", "food & beverage"],
    "marketing": ["advertising", "media", "digital marketing", "branding"],
    "consulting": ["professional services", "management", "strategy"],
    "manufacturing": ["industrial", "automotive", "aerospace", "electronics"],
    "real estate": ["construction", "property management", "architecture"],
    "education": ["edtech", "e-learning", "training", "publishing"],
}

INDUSTRY_EXACT_MATCH_MULTIPLIER = 1.5
INDUSTRY_RELATED_MATCH_MULTIPLIER = 1.2
INDUSTRY_NO_MATCH_MULTIPLIER = 1.0


def compile_patterns() -> dict[str, list[tuple[re.Pattern, float]]]:
    """Compile regex patterns for performance."""
    return {
        "high_intent": [(re.compile(p, re.IGNORECASE), s) for p, s in HIGH_INTENT_KEYWORDS],
        "medium_intent": [(re.compile(p, re.IGNORECASE), s) for p, s in MEDIUM_INTENT_KEYWORDS],
        "low_intent": [(re.compile(p, re.IGNORECASE), s) for p, s in LOW_INTENT_KEYWORDS],
        "negative": [(re.compile(p, re.IGNORECASE), s) for p, s in NEGATIVE_SIGNALS],
    }


# Pre-compiled patterns for use in scoring engine
COMPILED_PATTERNS = compile_patterns()
