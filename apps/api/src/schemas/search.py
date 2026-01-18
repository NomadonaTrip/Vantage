"""Search schema definitions."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from src.schemas.lead import CompanySize, LeadSource


class SearchStatus(str, Enum):
    """Search execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SearchType(str, Enum):
    """Search mode type."""

    AUTONOMOUS = "autonomous"  # Fully AI-driven based on profile
    MANUAL_OVERRIDE = "manual_override"  # Replace profile with manual params
    MANUAL_SUPPLEMENT = "manual_supplement"  # Merge manual params with profile


class ManualSearchParams(BaseModel):
    """Manual search parameter overrides."""

    keywords: list[str] = Field(default_factory=list)
    location: str | None = None
    company_sizes: list[CompanySize] | None = None
    budget_min: float | None = Field(default=None, ge=0)
    budget_max: float | None = Field(default=None, ge=0)
    industry_filter: list[str] | None = None


class SearchCreate(BaseModel):
    """Schema for creating a search."""

    client_profile_id: str
    search_type: SearchType = SearchType.AUTONOMOUS
    manual_params: ManualSearchParams | None = None
    quality_setting: float = Field(default=0.7, ge=0, le=1)
    sources_to_query: list[LeadSource] | None = None  # None = all available


class SearchUpdate(BaseModel):
    """Schema for updating search execution state."""

    status: SearchStatus | None = None
    sources_queried: list[LeadSource] | None = None
    sources_successful: list[LeadSource] | None = None
    sources_failed: list[LeadSource] | None = None
    lead_count: int | None = None
    error_message: str | None = None
    completed_at: datetime | None = None


class Search(BaseModel):
    """Full search model."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    client_profile_id: str

    # Configuration
    search_type: SearchType = SearchType.AUTONOMOUS
    manual_params: ManualSearchParams | None = None
    quality_setting: float = Field(default=0.7, ge=0, le=1)

    # Execution state
    status: SearchStatus = SearchStatus.PENDING
    sources_queried: list[LeadSource] = Field(default_factory=list)
    sources_successful: list[LeadSource] = Field(default_factory=list)
    sources_failed: list[LeadSource] = Field(default_factory=list)
    lead_count: int = 0

    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    # Error handling
    error_message: str | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class SearchResponse(BaseModel):
    """Response model for search operations."""

    id: str
    client_profile_id: str
    search_type: SearchType
    manual_params: ManualSearchParams | None
    quality_setting: float
    status: SearchStatus
    sources_queried: list[LeadSource]
    sources_successful: list[LeadSource]
    sources_failed: list[LeadSource]
    lead_count: int
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None


class SearchListResponse(BaseModel):
    """Response for listing searches."""

    searches: list[SearchResponse]
    total: int


class SearchProgressUpdate(BaseModel):
    """WebSocket progress update message."""

    search_id: str
    status: SearchStatus
    sources_completed: list[LeadSource]
    sources_pending: list[LeadSource]
    sources_failed: list[LeadSource]
    leads_found: int
    progress_percent: float = Field(ge=0, le=100)
    message: str | None = None
