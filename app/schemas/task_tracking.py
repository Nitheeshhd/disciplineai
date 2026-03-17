from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class TaskStatusToggleRequest(BaseModel):
    task_name: str = Field(min_length=1, max_length=120)
    status: bool
    task_date: date | None = None
    source: Literal["task", "habit"] = "task"


class UserProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    age: int | None = Field(default=None, ge=1, le=120)


class FocusSessionSyncRequest(BaseModel):
    minutes: int = Field(ge=1, le=240)
    focus_date: date | None = Field(default=None, alias="date")
