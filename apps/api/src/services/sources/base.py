"""Base source adapter interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from src.schemas.lead import CompanySize, LeadSource


class SourceStatus(str, Enum):
    """Source adapter execution status."""

    SUCCESS = "success"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"


class RateLimitStatus(BaseModel):
    """Rate limit status for a source."""

    remaining_requests: int = Field(ge=0)
    reset_at: datetime | None = None
    is_limited: bool = False


class SearchQuery(BaseModel):
    """Query parameters for source search."""

    keywords: list[str] = Field(default_factory=list)
    location: str | None = None
    company_sizes: list[CompanySize] | None = None
    budget_min: float | None = Field(default=None, ge=0)
    budget_max: float | None = Field(default=None, ge=0)
    industry_filter: list[str] | None = None
    max_results: int = Field(default=50, ge=1, le=100)

    # Client profile context for intelligent search
    client_industry: str | None = None
    client_services: list[str] = Field(default_factory=list)
    client_icp: str | None = None


@dataclass
class RawLead:
    """
    Standardized raw lead data from any source.

    All adapters must convert their source-specific data to this format.
    """

    # Required fields
    name: str
    company: str
    source: LeadSource
    source_url: str

    # Optional contact info
    email: str | None = None
    phone: str | None = None

    # Metadata
    company_size: CompanySize = CompanySize.UNKNOWN
    industry: str | None = None
    budget: float | None = None
    created_at: datetime | None = None

    # Original raw data for debugging/scoring
    raw_data: dict[str, Any] = field(default_factory=dict)

    # Text content for keyword scoring
    title: str | None = None
    description: str | None = None


@dataclass
class AdapterResult:
    """Result from a source adapter search."""

    source: LeadSource
    status: SourceStatus
    leads: list[RawLead] = field(default_factory=list)
    error_message: str | None = None
    execution_time_ms: float = 0.0
    rate_limit_status: RateLimitStatus | None = None

    @property
    def is_success(self) -> bool:
        """Check if the search was successful."""
        return self.status == SourceStatus.SUCCESS

    @property
    def lead_count(self) -> int:
        """Get number of leads found."""
        return len(self.leads)


class BaseSourceAdapter(ABC):
    """
    Abstract base class for all source adapters.

    All source implementations (Upwork, Reddit, Apollo, etc.) must
    inherit from this class and implement the required methods.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Initialize the adapter.

        Args:
            config: Optional configuration dictionary for the adapter.
        """
        self.config = config or {}
        self._is_available = True

    @property
    @abstractmethod
    def source_type(self) -> LeadSource:
        """Get the source type this adapter handles."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get human-readable name for this adapter."""
        pass

    @abstractmethod
    async def search(self, query: SearchQuery) -> AdapterResult:
        """
        Execute a search query against the source.

        Args:
            query: Search parameters.

        Returns:
            AdapterResult with leads and status.
        """
        pass

    @abstractmethod
    async def check_availability(self) -> bool:
        """
        Check if the source is currently available.

        Returns:
            True if the source can be queried.
        """
        pass

    @abstractmethod
    def get_rate_limit_status(self) -> RateLimitStatus:
        """
        Get current rate limit status.

        Returns:
            RateLimitStatus with remaining requests and reset time.
        """
        pass

    @property
    def is_available(self) -> bool:
        """Check if adapter is available for use."""
        return self._is_available

    def mark_unavailable(self, reason: str | None = None) -> None:
        """Mark adapter as temporarily unavailable."""
        self._is_available = False

    def mark_available(self) -> None:
        """Mark adapter as available."""
        self._is_available = True

    def build_search_text(self, query: SearchQuery) -> str:
        """
        Build search text from query parameters.

        Args:
            query: Search query with keywords and context.

        Returns:
            Formatted search string.
        """
        parts = []

        if query.keywords:
            parts.extend(query.keywords)

        if query.client_services:
            parts.extend(query.client_services[:3])  # Limit to avoid too long

        return " ".join(parts) if parts else "software development"
