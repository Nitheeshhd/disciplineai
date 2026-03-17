from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator


class CampaignGenerateRequest(BaseModel):
    """Request contract for generating a UTM campaign URL."""

    base_url: HttpUrl
    utm_source: str = Field(min_length=1, max_length=120)
    utm_medium: str = Field(min_length=1, max_length=120)
    utm_campaign: str = Field(min_length=1, max_length=120)

    @field_validator("utm_source", "utm_medium", "utm_campaign")
    @classmethod
    def validate_utm_string(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("UTM field cannot be empty")
        return normalized


class CampaignResponse(BaseModel):
    """UTM campaign response payload."""

    id: int
    user_id: int
    base_url: str
    utm_source: str
    utm_medium: str
    utm_campaign: str
    full_url: str
    clicks: int
    created_at: datetime


class CampaignListResponse(BaseModel):
    """Owner-scoped campaign listing response."""

    items: list[CampaignResponse]

