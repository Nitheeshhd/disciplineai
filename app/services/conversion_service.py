from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.repositories.conversion_repository import ConversionRepository


class ConversionService:
    """Service that derives conversions from 7-day habit streaks."""

    STREAK_THRESHOLD = 7

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ConversionRepository(session)

    async def get_conversions(self) -> list[dict]:
        """Recompute conversion rows from habit logs and return all conversion events."""

        await self._sync_all_users()
        try:
            rows = await self.repo.list_all()
        except SQLAlchemyError as exc:
            raise ApplicationError(
                message="Failed to fetch conversions",
                code="conversions_fetch_failed",
                status_code=500,
            ) from exc
        return [self._serialize(row) for row in rows]

    async def get_conversion_rate(self) -> dict:
        """Return platform conversion rate as percentage of active users converted."""

        await self._sync_all_users()
        try:
            total_users = await self.repo.count_total_users()
            converted_users = await self.repo.count_converted_users()
        except SQLAlchemyError as exc:
            raise ApplicationError(
                message="Failed to calculate conversion rate",
                code="conversion_rate_failed",
                status_code=500,
            ) from exc

        rate = round((converted_users / total_users * 100) if total_users else 0.0, 2)
        return {"rate": rate}

    async def _sync_all_users(self) -> None:
        """Refresh conversion events for all active users."""

        try:
            user_ids = await self.repo.list_active_user_ids()
            for user_id in user_ids:
                dates = await self.repo.list_habit_log_dates(user_id=user_id)
                events = self._detect_conversions(dates)
                await self.repo.replace_user_conversions(user_id=user_id, items=events)
            await self.session.commit()
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise ApplicationError(
                message="Failed to sync conversions",
                code="conversion_sync_failed",
                status_code=500,
            ) from exc

    def _detect_conversions(self, dates: list[date]) -> list[tuple[date, int]]:
        """Detect conversion events where a streak reaches at least 7 consecutive days."""

        if not dates:
            return []

        events: list[tuple[date, int]] = []
        streak_length = 1
        previous = dates[0]

        for current in dates[1:]:
            if current == previous + timedelta(days=1):
                streak_length += 1
            else:
                if streak_length >= self.STREAK_THRESHOLD:
                    events.append((previous, streak_length))
                streak_length = 1
            previous = current

        if streak_length >= self.STREAK_THRESHOLD:
            events.append((previous, streak_length))

        return events

    def _serialize(self, row) -> dict:
        return {
            "id": row.id,
            "user_id": row.user_id,
            "conversion_date": row.conversion_date,
            "streak_length": row.streak_length,
        }

