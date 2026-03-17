from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.habit_log import HabitLog
from app.models.read_models import DailyAnalyticsReadModel
from app.models.user import User


class AnalyticsQueryRepository:
    """Read side repository for analytics (CQRS query model)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def productivity_points(self, days: int = 30) -> tuple[list[str], list[float]]:
        today = date.today()
        start_day = today - timedelta(days=days - 1)
        stmt = (
            select(DailyAnalyticsReadModel.metric_date, DailyAnalyticsReadModel.avg_productivity)
            .where(
                and_(
                    DailyAnalyticsReadModel.metric_date >= start_day,
                    DailyAnalyticsReadModel.metric_date <= today,
                )
            )
            .order_by(DailyAnalyticsReadModel.metric_date.asc())
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        by_date = {metric_date: float(value) for metric_date, value in rows}
        labels = []
        values = []
        for offset in range(days):
            day = start_day + timedelta(days=offset)
            labels.append(day.isoformat())
            values.append(round(by_date.get(day, 0.0), 2))
        return labels, values

    async def user_daily_totals(self, user_id: int, days: int = 30) -> dict[date, float]:
        today = date.today()
        start_day = today - timedelta(days=days - 1)
        stmt = (
            select(HabitLog.log_date, func.sum(HabitLog.value))
            .where(
                and_(
                    HabitLog.user_id == user_id,
                    HabitLog.log_date >= start_day,
                    HabitLog.log_date <= today,
                    HabitLog.is_deleted.is_(False),
                )
            )
            .group_by(HabitLog.log_date)
            .order_by(HabitLog.log_date.asc())
        )
        result = await self.session.execute(stmt)
        totals: dict[date, float] = defaultdict(float)
        for log_date, total in result.all():
            totals[log_date] = float(total or 0.0)
        return totals

    async def most_active_hour(self, user_id: int, days: int = 30) -> int | None:
        today = date.today()
        start_day = today - timedelta(days=days - 1)
        stmt = (
            select(HabitLog.logged_hour, func.count(HabitLog.id).label("count"))
            .where(
                and_(
                    HabitLog.user_id == user_id,
                    HabitLog.log_date >= start_day,
                    HabitLog.log_date <= today,
                    HabitLog.is_deleted.is_(False),
                )
            )
            .group_by(HabitLog.logged_hour)
            .order_by(desc("count"), HabitLog.logged_hour.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.first()
        return int(row[0]) if row else None

    async def top_recent_users(self, limit: int = 5) -> list[dict]:
        stmt = (
            select(User.id, User.first_name, User.username, func.max(HabitLog.created_at).label("last_activity"))
            .join(HabitLog, HabitLog.user_id == User.id)
            .where(and_(User.is_deleted.is_(False), HabitLog.is_deleted.is_(False)))
            .group_by(User.id, User.first_name, User.username)
            .order_by(desc("last_activity"))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {
                "user_id": user_id,
                "user_name": first_name or username or "Anonymous",
                "last_activity": last_activity.isoformat() if last_activity else "",
            }
            for user_id, first_name, username, last_activity in rows
        ]
