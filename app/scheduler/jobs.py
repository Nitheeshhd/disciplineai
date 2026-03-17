from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from telegram.ext import Application

from app.config import Settings
from app.services.reminders import optimize_reminder_hours, send_smart_reminders

logger = logging.getLogger(__name__)


async def optimize_reminder_hours_job(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        updated = await optimize_reminder_hours(session)
    logger.info("Reminder-hour optimization completed. Updated users=%s", updated)


async def send_smart_reminders_job(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_app: Application | None,
    settings: Settings,
) -> None:
    if telegram_app is None:
        return

    async with session_factory() as session:
        stats = await send_smart_reminders(
            session=session,
            bot=telegram_app.bot,
            timezone=settings.timezone,
            reminder_text=settings.reminder_text,
        )
    logger.info(
        "Smart reminders executed. sent=%s failed=%s skipped=%s",
        stats["sent"],
        stats["failed"],
        stats["skipped"],
    )


def register_scheduler_jobs(
    scheduler: AsyncIOScheduler,
    session_factory: async_sessionmaker[AsyncSession],
    telegram_app: Application | None,
    settings: Settings,
) -> None:
    scheduler.add_job(
        optimize_reminder_hours_job,
        trigger=CronTrigger(hour=0, minute=10, timezone=settings.timezone),
        kwargs={"session_factory": session_factory},
        id="optimize_reminder_hours",
        replace_existing=True,
    )
    scheduler.add_job(
        send_smart_reminders_job,
        trigger=CronTrigger(minute=0, timezone=settings.timezone),
        kwargs={
            "session_factory": session_factory,
            "telegram_app": telegram_app,
            "settings": settings,
        },
        id="send_smart_reminders",
        replace_existing=True,
    )
