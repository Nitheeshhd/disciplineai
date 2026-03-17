from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.message import Message
from app.models.role import Role, UserRole
from app.models.session import Session
from app.models.user import User
from app.repositories.base import BaseRepository
from app.utils.datetime import utc_now


class UserRepository(BaseRepository[User]):
    """Repository for user identity and management queries."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(and_(User.email == email, User.is_deleted.is_(False)))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_telegram_user_id(self, telegram_user_id: int) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(and_(User.telegram_user_id == telegram_user_id, User.is_deleted.is_(False)))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_roles(self, user_id: int) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(and_(User.id == user_id, User.is_deleted.is_(False)))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        telegram_user_id: int,
        first_name: str | None,
        last_name: str | None,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            telegram_user_id=telegram_user_id,
            first_name=first_name,
            last_name=last_name,
        )
        await self.add(user)
        return user

    async def ensure_role(self, role_name: str, description: str | None = None) -> Role:
        stmt = select(Role).where(and_(Role.name == role_name, Role.is_deleted.is_(False)))
        result = await self.session.execute(stmt)
        role = result.scalar_one_or_none()
        if role:
            return role
        role = Role(name=role_name, description=description)
        self.session.add(role)
        await self.session.flush()
        return role

    async def assign_role(self, user_id: int, role_id: int) -> None:
        stmt = select(UserRole).where(and_(UserRole.user_id == user_id, UserRole.role_id == role_id))
        result = await self.session.execute(stmt)
        exists = result.scalar_one_or_none()
        if exists:
            return
        self.session.add(UserRole(user_id=user_id, role_id=role_id))
        await self.session.flush()

    async def create_session(
        self,
        user_id: int,
        refresh_token_jti: str,
        refresh_token_hash: str,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Session:
        session = Session(
            user_id=user_id,
            refresh_token_jti=refresh_token_jti,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(session)
        await self.session.flush()
        return session

    async def get_session_by_jti(self, refresh_token_jti: str) -> Session | None:
        stmt = select(Session).where(
            and_(
                Session.refresh_token_jti == refresh_token_jti,
                Session.is_deleted.is_(False),
                Session.revoked_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users_paginated(
        self,
        offset: int,
        limit: int,
        premium: bool | None = None,
    ) -> tuple[list[dict], int]:
        """Return paginated users with message aggregates and optional premium filter."""

        messages_subquery = (
            select(
                Message.user_id.label("user_id"),
                func.count(Message.id).label("total_messages"),
                func.max(Message.created_at).label("last_active"),
            )
            .where(Message.is_deleted.is_(False))
            .group_by(Message.user_id)
            .subquery()
        )

        filters = [User.is_deleted.is_(False)]
        if premium is not None:
            filters.append(User.is_premium.is_(premium))

        stmt = (
            select(
                User.id,
                User.username,
                User.created_at.label("first_seen"),
                messages_subquery.c.last_active,
                func.coalesce(messages_subquery.c.total_messages, 0).label("total_messages"),
                User.is_premium.label("premium_status"),
            )
            .outerjoin(messages_subquery, messages_subquery.c.user_id == User.id)
            .where(and_(*filters))
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_stmt = select(func.count(User.id)).where(and_(*filters))

        rows = (await self.session.execute(stmt)).all()
        total = int((await self.session.execute(count_stmt)).scalar_one() or 0)
        payload = [
            {
                "id": int(row.id),
                "username": row.username,
                "first_seen": row.first_seen,
                "last_active": row.last_active,
                "total_messages": int(row.total_messages or 0),
                "premium_status": bool(row.premium_status),
            }
            for row in rows
        ]
        return payload, total

    async def get_user_management_view(self, user_id: int) -> dict | None:
        """Return management projection for a single user."""

        messages_subquery = (
            select(
                Message.user_id.label("user_id"),
                func.count(Message.id).label("total_messages"),
                func.max(Message.created_at).label("last_active"),
            )
            .where(Message.is_deleted.is_(False))
            .group_by(Message.user_id)
            .subquery()
        )
        stmt = (
            select(
                User.id,
                User.username,
                User.created_at.label("first_seen"),
                messages_subquery.c.last_active,
                func.coalesce(messages_subquery.c.total_messages, 0).label("total_messages"),
                User.is_premium.label("premium_status"),
            )
            .outerjoin(messages_subquery, messages_subquery.c.user_id == User.id)
            .where(and_(User.id == user_id, User.is_deleted.is_(False)))
        )
        row = (await self.session.execute(stmt)).first()
        if row is None:
            return None
        return {
            "id": int(row.id),
            "username": row.username,
            "first_seen": row.first_seen,
            "last_active": row.last_active,
            "total_messages": int(row.total_messages or 0),
            "premium_status": bool(row.premium_status),
        }

    async def soft_delete_user(self, user_id: int) -> bool:
        """Soft delete a user by id. Returns True when deletion was applied."""

        user = await self.get_by_id(user_id)
        if user is None or user.is_deleted:
            return False
        user.is_deleted = True
        user.deleted_at = utc_now()
        await self.session.flush()
        return True
