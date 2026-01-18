"""Lead schema definitions."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class LeadStatus(str, Enum):
    """Lead lifecycle status."""

    NEW = "new"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    CONVERTED = "converted"
    LOST = "lost"


class LeadAccuracy(str, Enum):
    """Lead accuracy classification."""

    VERIFIED = "verified"
    EMAIL_BOUNCED = "email_bounced"
    PHONE_INVALID = "phone_invalid"
    WRONG_PERSON = "wrong_person"
    COMPANY_MISMATCH = "company_mismatch"


class LeadSource(str, Enum):
    """Lead source platform."""

    UPWORK = "upwork"
    REDDIT = "reddit"
    APOLLO = "apollo"
    CLUTCH = "clutch"
    BING = "bing"
    GOOGLE = "google"
    MANUAL = "manual"


class CompanySize(str, Enum):
    """Company size classification."""

    SOLO = "solo"
    SMALL = "small"  # 2-10 employees
    MEDIUM = "medium"  # 11-50 employees
    ENTERPRISE = "enterprise"  # 50+ employees
    UNKNOWN = "unknown"


class ScoreBreakdown(BaseModel):
    """Detailed breakdown of lead intent score."""

    source_score: float = Field(default=0.0, ge=0, le=100, description="Score from source hierarchy")
    keyword_score: float = Field(default=0.0, ge=0, le=100, description="Score from keyword matching")
    company_size_score: float = Field(default=0.0, ge=0, le=100, description="Score from company size fit")
    timing_score: float = Field(default=0.0, ge=0, le=100, description="Score from timing/recency")
    budget_score: float = Field(default=0.0, ge=0, le=100, description="Score from budget signals")
    industry_multiplier: float = Field(default=1.0, ge=0, le=2, description="Industry match multiplier")
    negative_deductions: float = Field(default=0.0, ge=0, le=100, description="Deductions for negative signals")
    final_score: float = Field(default=0.0, ge=0, le=100, description="Final composite score")


class LeadBase(BaseModel):
    """Base lead fields."""

    name: str = Field(..., min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=50)
    company: str = Field(..., min_length=1, max_length=200)
    company_size: CompanySize = CompanySize.UNKNOWN
    source: LeadSource
    source_url: str | None = Field(default=None, max_length=2000)


class LeadCreate(LeadBase):
    """Schema for creating a lead."""

    client_profile_id: str
    search_id: str
    intent_score: float = Field(default=0.0, ge=0, le=100)
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    raw_data: dict | None = None


class LeadUpdate(BaseModel):
    """Schema for updating a lead."""

    status: LeadStatus | None = None
    accuracy: LeadAccuracy | None = None
    notes: str | None = Field(default=None, max_length=2000)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=50)


class Lead(LeadBase):
    """Full lead model."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    client_profile_id: str
    search_id: str
    intent_score: float = Field(default=0.0, ge=0, le=100)
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    status: LeadStatus = LeadStatus.NEW
    accuracy: LeadAccuracy | None = None
    raw_data: dict | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        from_attributes = True


class LeadStatusHistory(BaseModel):
    """Lead status change history entry."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    lead_id: str
    previous_status: LeadStatus | None
    new_status: LeadStatus
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    notes: str | None = None


class LeadResponse(BaseModel):
    """Response model for lead operations."""

    id: str
    client_profile_id: str
    search_id: str
    name: str
    email: str | None
    phone: str | None
    company: str
    company_size: CompanySize
    intent_score: float
    score_breakdown: ScoreBreakdown
    source: LeadSource
    source_url: str | None
    status: LeadStatus
    accuracy: LeadAccuracy | None
    created_at: datetime
    updated_at: datetime


class LeadDetailResponse(LeadResponse):
    """Detailed response including status history."""

    raw_data: dict | None
    status_history: list[LeadStatusHistory] = Field(default_factory=list)


class LeadListResponse(BaseModel):
    """Response for listing leads."""

    leads: list[LeadResponse]
    total: int
    page: int = 1
    page_size: int = 20
