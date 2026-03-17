from __future__ import annotations

from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.badge import Badge
from app.repositories.base import BaseRepository


class BadgeRepository(BaseRepository[Badge]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Badge)

    async def list_by_user_id(self, user_id: int) -> list[Badge]:
        stmt = select(Badge).where(Badge.user_id == user_id).order_by(Badge.date_earned.asc(), Badge.badge_name.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def ensure_badge(self, user_id: int, badge_name: str, date_earned: date) -> Badge:
        stmt = select(Badge).where(and_(Badge.user_id == user_id, Badge.badge_name == badge_name)).limit(1)
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        badge = Badge(
            user_id=user_id,
            badge_name=badge_name,
            date_earned=date_earned,
        )
        self.session.add(badge)
        await self.session.flush()
        return badge
