from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Bot

from app.db.repositories import HabitRepository, ReminderRepository, UserRepository
from app.utils.time import now_in_timezone

logger = logging.getLogger(__name__)


async def optimize_reminder_hours(session: AsyncSession) -> int:
    users = await UserRepository.list_all(session)
    updated = 0
    for user in users:
        active_hour = await HabitRepository.detect_most_active_hour(session, user.id)
        if active_hour is None:
            continue
        if user.reminder_hour != active_hour:
            user.reminder_hour = active_hour
            updated += 1
    await session.commit()
    return updated


async def send_smart_reminders(
    session: AsyncSession,
    bot: Bot,
    timezone: str,
    reminder_text: str,
) -> dict[str, int]:
    local_now = now_in_timezone(timezone)
    today = local_now.date()
    hour = local_now.hour

    due_users = await UserRepository.list_for_reminder_hour(session, hour)
    sent = 0
    failed = 0
    skipped = 0

    for user in due_users:
        already_sent = await ReminderRepository.already_sent(session, user.id, today, hour)
        if already_sent:
            skipped += 1
            continue

        try:
            await bot.send_message(chat_id=user.telegram_user_id, text=reminder_text)
            await ReminderRepository.add_dispatch(session, user.id, today, hour, status="sent")
            sent += 1
        except Exception as exc:  # pragma: no cover - depends on Telegram runtime
            logger.warning("Failed reminder for user %s: %s", user.telegram_user_id, exc)
            await ReminderRepository.add_dispatch(session, user.id, today, hour, status="failed")
            failed += 1

    await session.commit()
    return {"sent": sent, "failed": failed, "skipped": skipped}
