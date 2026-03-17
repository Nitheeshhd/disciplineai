from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class ReportItem(BaseModel):
    """Weekly analytics report payload."""

    id: int
    week_start: date
    total_users: int
    avg_productivity: float
    revenue: float
    generated_at: datetime


class ReportListResponse(BaseModel):
    """List response for weekly reports."""

    items: list[ReportItem]

