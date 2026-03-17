from __future__ import annotations

from datetime import date

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.habit_log import HabitLog
from app.models.payment import Payment
from app.models.report import Report
from app.models.user import User
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Repository for weekly report aggregation and persistence."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Report)

    async def weekly_stats(self, week_start: date, week_end: date) -> dict:
        """Calculate weekly users, productivity and revenue in one query round-trip."""

        users_subquery = (
            select(func.count(User.id))
            .where(and_(User.is_deleted.is_(False), User.is_active.is_(True)))
            .scalar_subquery()
        )
        productivity_subquery = (
            select(func.coalesce(func.avg(HabitLog.value), 0))
            .where(
                and_(
                    HabitLog.log_date >= week_start,
                    HabitLog.log_date <= week_end,
                    HabitLog.is_deleted.is_(False),
                )
            )
            .scalar_subquery()
        )
        revenue_subquery = (
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(
                and_(
                    Payment.paid_date >= week_start,
                    Payment.paid_date <= week_end,
                    Payment.payment_status == "paid",
                    Payment.is_deleted.is_(False),
                )
            )
            .scalar_subquery()
        )

        stmt = select(
            users_subquery.label("total_users"),
            productivity_subquery.label("avg_productivity"),
            revenue_subquery.label("revenue"),
        )
        row = (await self.session.execute(stmt)).one()
        return {
            "total_users": int(row.total_users or 0),
            "avg_productivity": round(float(row.avg_productivity or 0.0), 2),
            "revenue": round(float(row.revenue or 0.0), 2),
        }

    async def get_by_week_start(self, week_start: date) -> Report | None:
        stmt = select(Report).where(Report.week_start == week_start)
        row = await self.session.execute(stmt)
        return row.scalar_one_or_none()

    async def upsert_weekly_report(
        self,
        week_start: date,
        total_users: int,
        avg_productivity: float,
        revenue: float,
        generated_at,
    ) -> Report:
        """Create or update weekly report row."""

        row = await self.get_by_week_start(week_start=week_start)
        if row is None:
            row = Report(
                week_start=week_start,
                total_users=total_users,
                avg_productivity=avg_productivity,
                revenue=revenue,
                generated_at=generated_at,
            )
            self.session.add(row)
        else:
            row.total_users = total_users
            row.avg_productivity = avg_productivity
            row.revenue = revenue
            row.generated_at = generated_at
        await self.session.flush()
        return row

    async def list_reports(self, limit: int = 52) -> list[Report]:
        stmt = select(Report).order_by(desc(Report.week_start)).limit(limit)
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())

