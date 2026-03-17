from __future__ import annotations

import asyncio
import logging
from datetime import date, timedelta

from sqlalchemy import and_, func, select

from app.core.celery_app import celery_app
from app.core.database import ReadSessionLocal, WriteSessionLocal
from app.models.habit_log import HabitLog
from app.models.user import User
from app.repositories.analytics_projection_repository import AnalyticsProjectionRepository
from app.services.report_service import ReportService

logger = logging.getLogger(__name__)


async def _project_daily_analytics(metric_day: date) -> dict:
    async with WriteSessionLocal() as session:
        repo = AnalyticsProjectionRepository(session)
        model = await repo.upsert_day(metric_day)
        await session.commit()
        return {
            "metric_date": model.metric_date.isoformat(),
            "sessions_count": model.sessions_count,
            "messages_count": model.messages_count,
        }


@celery_app.task(name="project_daily_analytics")
def project_daily_analytics_task(metric_day_iso: str) -> dict:
    metric_day = date.fromisoformat(metric_day_iso)
    return asyncio.run(_project_daily_analytics(metric_day))


async def _generate_weekly_report() -> dict:
    async with WriteSessionLocal() as session:
        service = ReportService(session=session)
        report = await service.generate_weekly_report(reference_day=date.today())
        payload = {
            "id": int(report["id"]),
            "week_start": report["week_start"].isoformat(),
            "total_users": int(report["total_users"]),
            "avg_productivity": float(report["avg_productivity"]),
            "revenue": float(report["revenue"]),
            "generated_at": report["generated_at"].isoformat(),
        }
    logger.info("Weekly report generated: %s", payload)
    return payload


@celery_app.task(name="generate_weekly_report")
def generate_weekly_report_task() -> dict:
    return asyncio.run(_generate_weekly_report())


async def _recalculate_productivity_projection(days: int = 30) -> dict:
    today = date.today()
    start_day = today - timedelta(days=days - 1)
    projected = 0
    async with WriteSessionLocal() as session:
        repo = AnalyticsProjectionRepository(session)
        for offset in range(days):
            day = start_day + timedelta(days=offset)
            await repo.upsert_day(day)
            projected += 1
        await session.commit()
    return {"projected_days": projected}


@celery_app.task(name="recalculate_productivity")
def recalculate_productivity_task(days: int = 30) -> dict:
    return asyncio.run(_recalculate_productivity_projection(days=days))


async def _detect_inactive_users(threshold_days: int = 7) -> dict:
    cutoff = date.today() - timedelta(days=threshold_days)
    async with ReadSessionLocal() as session:
        subquery = (
            select(HabitLog.user_id, func.max(HabitLog.log_date).label("last_log"))
            .where(HabitLog.is_deleted.is_(False))
            .group_by(HabitLog.user_id)
            .subquery()
        )
        stmt = (
            select(User.id)
            .outerjoin(subquery, subquery.c.user_id == User.id)
            .where(
                and_(
                    User.is_deleted.is_(False),
                    User.is_active.is_(True),
                    (subquery.c.last_log.is_(None) | (subquery.c.last_log < cutoff)),
                )
            )
        )
        rows = await session.execute(stmt)
        inactive_user_ids = [int(user_id) for (user_id,) in rows.all()]
    logger.info("Inactive users detected. count=%s", len(inactive_user_ids))
    return {"inactive_users": inactive_user_ids, "count": len(inactive_user_ids)}


@celery_app.task(name="detect_inactive_users")
def detect_inactive_users_task(threshold_days: int = 7) -> dict:
    return asyncio.run(_detect_inactive_users(threshold_days=threshold_days))
