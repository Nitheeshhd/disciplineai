from datetime import datetime

from pydantic import BaseModel, Field


class BotCreateRequest(BaseModel):
    """Payload for registering a bot under authenticated owner account."""

    name: str = Field(min_length=1, max_length=120)
    token: str = Field(min_length=10, max_length=2048)
    is_active: bool = True


class BotResponse(BaseModel):
    """Safe bot response contract (token is never returned in plaintext)."""

    id: int
    name: str
    owner_id: int
    created_at: datetime
    is_active: bool


class BotsListResponse(BaseModel):
    """Owner-scoped list response for my bots."""

    items: list[BotResponse]
