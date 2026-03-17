from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import Settings
from app.workers.tasks import (
    detect_inactive_users_task,
    generate_weekly_report_task,
    recalculate_productivity_task,
)


def build_scheduler(settings: Settings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)

    scheduler.add_job(
        lambda: generate_weekly_report_task.delay(),
        trigger=CronTrigger(day_of_week="sun", hour=23, minute=0, timezone=settings.scheduler_timezone),
        id="weekly_report_job",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: recalculate_productivity_task.delay(30),
        trigger=CronTrigger(hour="*/6", minute=0, timezone=settings.scheduler_timezone),
        id="productivity_recalculation_job",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: detect_inactive_users_task.delay(settings.inactive_days_threshold),
        trigger=CronTrigger(hour=1, minute=0, timezone=settings.scheduler_timezone),
        id="inactive_user_detection_job",
        replace_existing=True,
    )
    return scheduler
