from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.repositories.user_repository import UserRepository


class UserManagementService:
    """Application service for user listing, detail retrieval, and soft deletion."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)

    async def list_users(self, page: int, page_size: int, premium: bool | None) -> dict:
        """Return paginated users with optional premium-only filtering."""

        offset = (page - 1) * page_size
        try:
            items, total = await self.users.list_users_paginated(
                offset=offset,
                limit=page_size,
                premium=premium,
            )
        except SQLAlchemyError as exc:
            raise ApplicationError(
                message="Failed to fetch users list",
                code="users_list_failed",
                status_code=500,
            ) from exc
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    async def get_user(self, user_id: int) -> dict:
        """Return single user management view or raise 404 if missing."""

        try:
            user = await self.users.get_user_management_view(user_id)
        except SQLAlchemyError as exc:
            raise ApplicationError(
                message="Failed to fetch user",
                code="user_fetch_failed",
                status_code=500,
            ) from exc
        if user is None:
            raise ApplicationError(
                message="User not found",
                code="user_not_found",
                status_code=404,
            )
        return user

    async def delete_user(self, user_id: int) -> None:
        """Soft delete user by id with transactional commit."""

        try:
            deleted = await self.users.soft_delete_user(user_id)
            if not deleted:
                raise ApplicationError(
                    message="User not found",
                    code="user_not_found",
                    status_code=404,
                )
            await self.session.commit()
        except ApplicationError:
            await self.session.rollback()
            raise
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise ApplicationError(
                message="Failed to delete user",
                code="user_delete_failed",
                status_code=500,
            ) from exc
