from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ConversionItem(BaseModel):
    """Conversion row derived from habit-streak detection."""

    id: int
    user_id: int
    conversion_date: date
    streak_length: int


class ConversionListResponse(BaseModel):
    """Response contract for conversion events list."""

    items: list[ConversionItem]


class ConversionTrackingRateResponse(BaseModel):
    """Response contract for overall conversion rate."""

    rate: float
