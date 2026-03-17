from __future__ import annotations

from datetime import date

from sqlalchemy import and_, delete, desc, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversion import Conversion
from app.models.habit_log import HabitLog
from app.models.user import User
from app.repositories.base import BaseRepository


class ConversionRepository(BaseRepository[Conversion]):
    """Repository for conversion persistence and streak source queries."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Conversion)

    async def list_active_user_ids(self) -> list[int]:
        stmt = select(User.id).where(and_(User.is_deleted.is_(False), User.is_active.is_(True)))
        rows = await self.session.execute(stmt)
        return [int(user_id) for user_id in rows.scalars().all()]

    async def list_habit_log_dates(self, user_id: int) -> list[date]:
        stmt = (
            select(distinct(HabitLog.log_date))
            .where(and_(HabitLog.user_id == user_id, HabitLog.is_deleted.is_(False)))
            .order_by(HabitLog.log_date.asc())
        )
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())

    async def replace_user_conversions(self, user_id: int, items: list[tuple[date, int]]) -> None:
        await self.session.execute(delete(Conversion).where(Conversion.user_id == user_id))
        for conversion_date, streak_length in items:
            row = Conversion(
                user_id=user_id,
                conversion_date=conversion_date,
                streak_length=streak_length,
            )
            self.session.add(row)
        await self.session.flush()

    async def list_all(self) -> list[Conversion]:
        stmt = select(Conversion).where(Conversion.is_deleted.is_(False)).order_by(desc(Conversion.conversion_date))
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())

    async def count_total_users(self) -> int:
        stmt = select(func.count(User.id)).where(and_(User.is_deleted.is_(False), User.is_active.is_(True)))
        return int((await self.session.execute(stmt)).scalar_one() or 0)

    async def count_converted_users(self) -> int:
        stmt = select(func.count(distinct(Conversion.user_id))).where(Conversion.is_deleted.is_(False))
        return int((await self.session.execute(stmt)).scalar_one() or 0)

