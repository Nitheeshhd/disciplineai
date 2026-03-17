from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ErrorLogItem(BaseModel):
    """Error log projection used by API responses."""

    id: int
    user_id: int | None
    command: str
    error_message: str
    stack_trace: str | None
    created_at: datetime


class ErrorLogListResponse(BaseModel):
    """Error log list response contract."""

    items: list[ErrorLogItem]

