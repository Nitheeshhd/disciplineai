from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain_event import DomainEventOutbox
from app.models.habit_log import HabitLog
from app.repositories.base import BaseRepository


class HabitRepository(BaseRepository[HabitLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, HabitLog)

    async def create_log(
        self,
        user_id: int,
        habit_name: str,
        value: float,
        unit: str,
        notes: str | None,
        log_date: date,
        logged_hour: int,
    ) -> HabitLog:
        log = HabitLog(
            user_id=user_id,
            habit_name=habit_name.lower().strip(),
            value=value,
            unit=unit,
            notes=notes,
            log_date=log_date,
            logged_hour=logged_hour,
        )
        await self.add(log)
        return log

    async def append_outbox_event(
        self,
        event_name: str,
        aggregate_id: str,
        payload_json: str,
    ) -> DomainEventOutbox:
        event = DomainEventOutbox(
            event_name=event_name,
            aggregate_id=aggregate_id,
            payload_json=payload_json,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_user_logs_between(self, user_id: int, start_day: date, end_day: date) -> list[HabitLog]:
        stmt = (
            select(HabitLog)
            .where(
                and_(
                    HabitLog.user_id == user_id,
                    HabitLog.log_date >= start_day,
                    HabitLog.log_date <= end_day,
                    HabitLog.is_deleted.is_(False),
                )
            )
            .order_by(HabitLog.log_date.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def daily_totals(self, user_id: int, days: int = 30) -> dict[date, float]:
        start_day = date.today() - timedelta(days=days - 1)
        logs = await self.list_user_logs_between(user_id, start_day=start_day, end_day=date.today())
        totals: dict[date, float] = defaultdict(float)
        for log in logs:
            totals[log.log_date] += float(log.value)
        return dict(totals)

    async def list_recent_goal_achievements(self, limit: int = 5) -> list[dict]:
        stmt = (
            select(HabitLog)
            .where(HabitLog.is_deleted.is_(False))
            .order_by(desc(HabitLog.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        return [
            {
                "date": row.log_date.isoformat(),
                "user_id": row.user_id,
                "conversion": row.habit_name,
                "value": f"{row.value:g} {row.unit}",
            }
            for row in rows
        ]

    async def list_popular_habits_today(self, target_day: date, limit: int = 5) -> list[dict]:
        stmt = (
            select(
                HabitLog.habit_name,
                func.count(HabitLog.id).label("number"),
                func.count(func.distinct(HabitLog.user_id)).label("unique_users"),
                func.avg(HabitLog.value).label("per_user"),
                func.sum(HabitLog.value).label("sessions"),
            )
            .where(and_(HabitLog.log_date == target_day, HabitLog.is_deleted.is_(False)))
            .group_by(HabitLog.habit_name)
            .order_by(desc("number"))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {
                "team": f"/{habit_name}",
                "number": int(number),
                "unique": int(unique_users),
                "per_user": round(float(per_user or 0), 2),
                "sessions": round(float(sessions or 0), 2),
            }
            for habit_name, number, unique_users, per_user, sessions in rows
        ]
