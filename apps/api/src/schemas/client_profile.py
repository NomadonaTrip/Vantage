"""Client profile schema definitions."""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class ScoringWeights(BaseModel):
    """Custom scoring weights for lead scoring."""

    source_hierarchy: float = Field(default=1.0, ge=0, le=1)
    keywords: float = Field(default=1.0, ge=0, le=1)
    company_size: float = Field(default=1.0, ge=0, le=1)
    timing_recency: float = Field(default=1.0, ge=0, le=1)
    budget_signals: float = Field(default=1.0, ge=0, le=1)
    industry_multipliers: float = Field(default=1.0, ge=0, le=1)


class ClientProfileBase(BaseModel):
    """Base client profile fields."""

    company_name: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=100)
    ideal_customer_profile: str = Field(..., min_length=1, max_length=2000)
    services: list[str] = Field(default_factory=list)
    additional_context: str | None = Field(default=None, max_length=5000)
    scoring_weight_overrides: ScoringWeights | None = None


class ClientProfileCreate(ClientProfileBase):
    """Schema for creating a client profile."""

    pass


class ClientProfileUpdate(BaseModel):
    """Schema for updating a client profile."""

    company_name: str | None = Field(default=None, min_length=1, max_length=200)
    industry: str | None = Field(default=None, min_length=1, max_length=100)
    ideal_customer_profile: str | None = Field(default=None, min_length=1, max_length=2000)
    services: list[str] | None = None
    additional_context: str | None = Field(default=None, max_length=5000)
    scoring_weight_overrides: ScoringWeights | None = None


class ClientProfile(ClientProfileBase):
    """Full client profile model."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    is_active: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        from_attributes = True


class ClientProfileResponse(BaseModel):
    """Response model for client profile."""

    id: str
    user_id: str
    company_name: str
    industry: str
    ideal_customer_profile: str
    services: list[str]
    additional_context: str | None
    scoring_weight_overrides: ScoringWeights | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ClientProfileListResponse(BaseModel):
    """Response model for listing client profiles."""

    profiles: list[ClientProfileResponse]
    total: int
