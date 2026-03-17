from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.payment import Payment
from app.models.read_models import DailyAnalyticsReadModel
from app.models.session import Session
from app.models.user import User


class DashboardRepository:
    """Read-side analytics repository for dashboard aggregate queries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def summary_today(self, today: date) -> dict[str, float | int]:
        """Return summary KPI aggregates using a single SQL round-trip."""

        sessions_subquery = (
            select(func.count(Session.id))
            .where(
                and_(
                    Session.is_deleted.is_(False),
                    func.date(Session.created_at) == today.isoformat(),
                )
            )
            .scalar_subquery()
        )
        users_subquery = (
            select(func.count(User.id))
            .where(User.is_deleted.is_(False))
            .scalar_subquery()
        )
        messages_subquery = (
            select(func.count(Message.id))
            .where(and_(Message.message_date == today, Message.is_deleted.is_(False)))
            .scalar_subquery()
        )
        revenue_subquery = (
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(
                and_(
                    Payment.paid_date == today,
                    Payment.payment_status == "paid",
                    Payment.is_deleted.is_(False),
                )
            )
            .scalar_subquery()
        )

        stmt = select(
            sessions_subquery.label("sessions_today"),
            users_subquery.label("total_users"),
            messages_subquery.label("messages_today"),
            revenue_subquery.label("revenue_today"),
        )
        row = (await self.session.execute(stmt)).one()

        sessions = int(row.sessions_today or 0)
        users = int(row.total_users or 0)
        messages = int(row.messages_today or 0)
        revenue = float(row.revenue_today or 0.0)
        return {
            "sessions_today": sessions,
            "total_users": users,
            "messages_today": messages,
            "revenue_today": round(revenue, 2),
        }

    async def productivity_trend(self, days: int = 30) -> list[dict[str, float | str]]:
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
        by_day = {metric_date: float(avg_productivity) for metric_date, avg_productivity in rows}
        points: list[dict[str, float | str]] = []
        for offset in range(days):
            day = start_day + timedelta(days=offset)
            points.append({"date": day.isoformat(), "value": round(by_day.get(day, 0.0), 2)})
        return points

    async def revenue_trend(self, days: int = 30) -> list[dict[str, float | str]]:
        today = date.today()
        start_day = today - timedelta(days=days - 1)
        stmt = (
            select(DailyAnalyticsReadModel.metric_date, DailyAnalyticsReadModel.revenue_total)
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
        by_day = {metric_date: float(revenue_total) for metric_date, revenue_total in rows}
        points: list[dict[str, float | str]] = []
        for offset in range(days):
            day = start_day + timedelta(days=offset)
            points.append({"date": day.isoformat(), "value": round(by_day.get(day, 0.0), 2)})
        return points

    async def demographic_breakdown(self) -> dict[str, list]:
        result = await self.session.execute(
            select(User.gender, func.count(User.id))
            .where(User.is_deleted.is_(False))
            .group_by(User.gender)
        )
        rows = result.all()
        labels = []
        values = []
        for gender, count in rows:
            labels.append((gender or "Unknown").title())
            values.append(int(count))
        if not labels:
            labels = ["Unknown"]
            values = [0]
        return {"labels": labels, "values": values}

    async def premium_breakdown(self) -> dict[str, list]:
        result = await self.session.execute(
            select(User.is_premium, func.count(User.id))
            .where(User.is_deleted.is_(False))
            .group_by(User.is_premium)
        )
        rows = result.all()
        counts = Counter({"No": 0, "Yes": 0})
        for premium, count in rows:
            counts["Yes" if premium else "No"] = int(count)
        return {"labels": ["No", "Yes"], "values": [counts["No"], counts["Yes"]]}

    async def conversion_rate(self, days: int = 30) -> float:
        today = date.today()
        start_day = today - timedelta(days=days - 1)
        sessions_stmt = select(func.coalesce(func.sum(DailyAnalyticsReadModel.sessions_count), 0)).where(
            and_(
                DailyAnalyticsReadModel.metric_date >= start_day,
                DailyAnalyticsReadModel.metric_date <= today,
            )
        )
        rate_stmt = select(func.avg(DailyAnalyticsReadModel.conversion_rate)).where(
            and_(
                DailyAnalyticsReadModel.metric_date >= start_day,
                DailyAnalyticsReadModel.metric_date <= today,
            )
        )
        sessions = float((await self.session.execute(sessions_stmt)).scalar_one() or 0.0)
        avg_rate = float((await self.session.execute(rate_stmt)).scalar_one() or 0.0)
        if sessions == 0:
            return 0.0
        return round(avg_rate, 2)
