from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.cqrs import LogHabitCommand
from app.analytics.events import HABIT_LOGGED_EVENT
from app.core.events import event_bus
from app.repositories.habit_repository import HabitRepository
from app.utils.datetime import utc_now


class HabitService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = HabitRepository(session)

    async def log_habit(self, command: LogHabitCommand) -> dict:
        now = utc_now()
        log = await self.repo.create_log(
            user_id=command.user_id,
            habit_name=command.habit_name,
            value=command.value,
            unit=command.unit,
            notes=command.notes,
            log_date=now.date(),
            logged_hour=now.hour,
        )

        payload = {
            "habit_log_id": log.id,
            "user_id": log.user_id,
            "habit_name": log.habit_name,
            "value": log.value,
            "log_date": log.log_date.isoformat(),
            "logged_hour": log.logged_hour,
        }
        await self.repo.append_outbox_event(
            event_name=HABIT_LOGGED_EVENT,
            aggregate_id=str(log.id),
            payload_json=json.dumps(payload, ensure_ascii=True),
        )
        await self.session.commit()

        # Domain event dispatch (event-driven orchestration to Celery/read model projection).
        await event_bus.publish(HABIT_LOGGED_EVENT, payload)

        return {
            "id": log.id,
            "user_id": log.user_id,
            "habit_name": log.habit_name,
            "value": float(log.value),
            "unit": log.unit,
            "log_date": log.log_date.isoformat(),
            "logged_hour": log.logged_hour,
        }
