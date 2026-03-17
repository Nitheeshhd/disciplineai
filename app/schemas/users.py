from datetime import datetime

from pydantic import BaseModel, Field


class UserManagementItem(BaseModel):
    """User projection used by management list/detail endpoints."""

    id: int
    username: str | None
    first_seen: datetime
    last_active: datetime | None
    total_messages: int
    premium_status: bool


class UserListResponse(BaseModel):
    """Paginated user listing response."""

    items: list[UserManagementItem]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)


class UserDeleteResponse(BaseModel):
    """Delete user response contract."""

    message: str
