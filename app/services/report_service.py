from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.repositories.report_repository import ReportRepository
from app.utils.datetime import utc_now


class ReportService:
    """Application service for weekly analytics report workflows."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.reports = ReportRepository(session)

    async def generate_weekly_report(self, reference_day: date | None = None) -> dict:
        """
        Generate and persist a weekly report.

        Week window follows ISO week semantics (Monday start).
        """

        day = reference_day or date.today()
        week_start = day - timedelta(days=day.weekday())
        week_end = week_start + timedelta(days=6)

        try:
            stats = await self.reports.weekly_stats(week_start=week_start, week_end=week_end)
            row = await self.reports.upsert_weekly_report(
                week_start=week_start,
                total_users=stats["total_users"],
                avg_productivity=stats["avg_productivity"],
                revenue=stats["revenue"],
                generated_at=utc_now(),
            )
            await self.session.commit()
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise ApplicationError(
                message="Failed to generate weekly report",
                code="weekly_report_generation_failed",
                status_code=500,
            ) from exc

        return self._serialize(row)

    async def list_reports(self, limit: int = 52) -> list[dict]:
        """List persisted weekly reports in reverse chronological order."""

        try:
            rows = await self.reports.list_reports(limit=limit)
        except SQLAlchemyError as exc:
            raise ApplicationError(
                message="Failed to fetch reports",
                code="reports_fetch_failed",
                status_code=500,
            ) from exc
        return [self._serialize(row) for row in rows]

    def _serialize(self, row) -> dict:
        return {
            "id": row.id,
            "week_start": row.week_start,
            "total_users": row.total_users,
            "avg_productivity": round(float(row.avg_productivity), 2),
            "revenue": round(float(row.revenue), 2),
            "generated_at": row.generated_at,
        }

