from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.cqrs import LogHabitCommand
from app.core.security import hash_password
from app.models.message import Message
from app.repositories.user_repository import UserRepository
from app.services.habit_service import HabitService


class TelegramIngestionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.habits = HabitService(session)

    async def ingest_update(self, payload: dict) -> None:
        message_data = payload.get("message")
        if not message_data:
            return

        from_user = message_data.get("from", {})
        chat_data = message_data.get("chat", {})
        text = message_data.get("text", "") or ""
        telegram_user_id = int(from_user.get("id", 0))
        if telegram_user_id <= 0:
            return

        user = await self.users.get_by_telegram_user_id(telegram_user_id)
        if user is None:
            user = await self.users.create_user(
                email=f"{telegram_user_id}@telegram.local",
                hashed_password=hash_password("telegram_external_auth"),
                telegram_user_id=telegram_user_id,
                first_name=from_user.get("first_name"),
                last_name=from_user.get("last_name"),
            )
            role = await self.users.ensure_role("user")
            await self.users.assign_role(user.id, role.id)

        message = Message(
            user_id=user.id,
            telegram_chat_id=int(chat_data.get("id", 0)),
            telegram_message_id=int(message_data.get("message_id", 0)),
            message_type="command" if text.startswith("/") else "text",
            message_text=text[:2000],
            sentiment_score=None,
            message_date=date.today(),
        )
        self.session.add(message)
        await self.session.flush()

        if text.startswith("/log "):
            parts = text.split(maxsplit=2)
            if len(parts) >= 3:
                habit_name = parts[1]
                try:
                    value = float(parts[2].split()[0])
                except ValueError:
                    value = 0.0
                await self.habits.log_habit(
                    LogHabitCommand(
                        user_id=user.id,
                        habit_name=habit_name,
                        value=max(value, 0),
                        unit="count",
                        notes="logged from telegram webhook",
                    )
                )
                return

        await self.session.commit()
