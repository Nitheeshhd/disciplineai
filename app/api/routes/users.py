from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_read_session, get_write_session
from app.schemas.users import UserDeleteResponse, UserListResponse, UserManagementItem
from app.services.user_management_service import UserManagementService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    premium: bool | None = Query(default=None),
    session: AsyncSession = Depends(get_read_session),
    _: dict = Depends(require_roles("admin", "analyst")),
) -> UserListResponse:
    """List users with pagination and optional premium filter."""

    service = UserManagementService(session=session)
    payload = await service.list_users(page=page, page_size=page_size, premium=premium)
    return UserListResponse(**payload)


@router.get("/{user_id}", response_model=UserManagementItem)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_read_session),
    _: dict = Depends(require_roles("admin", "analyst")),
) -> UserManagementItem:
    """Get one user profile in management projection format."""

    service = UserManagementService(session=session)
    payload = await service.get_user(user_id=user_id)
    return UserManagementItem(**payload)


@router.delete("/{user_id}", response_model=UserDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_write_session),
    _: dict = Depends(require_roles("admin")),
) -> UserDeleteResponse:
    """Soft delete user by id."""

    service = UserManagementService(session=session)
    await service.delete_user(user_id=user_id)
    return UserDeleteResponse(message="User deleted successfully")
