from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import Date, and_, cast, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import HabitLog, MoodLog, ReminderDispatch, UserProfile


class UserRepository:
    @staticmethod
    def _normalize_date(value: Any) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value[:10])
        raise ValueError(f"Unexpected date value: {value!r}")

    @staticmethod
    async def get_by_telegram_id(
        session: AsyncSession, telegram_user_id: int
    ) -> UserProfile | None:
        result = await session.execute(
            select(UserProfile).where(UserProfile.telegram_user_id == telegram_user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_from_telegram(
        session: AsyncSession,
        telegram_user: Any,
        timezone: str,
        seen_at: datetime,
    ) -> UserProfile:
        user = await UserRepository.get_by_telegram_id(session, telegram_user.id)
        if user is None:
            user = UserProfile(
                telegram_user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                timezone=timezone,
                is_premium=bool(getattr(telegram_user, "is_premium", False)),
                last_seen_at=seen_at,
            )
            session.add(user)
        else:
            user.username = telegram_user.username
            user.first_name = telegram_user.first_name
            user.last_name = telegram_user.last_name
            user.is_premium = bool(getattr(telegram_user, "is_premium", user.is_premium))
            user.last_seen_at = seen_at

        await session.flush()
        return user

    @staticmethod
    async def list_for_reminder_hour(
        session: AsyncSession, reminder_hour: int
    ) -> list[UserProfile]:
        result = await session.execute(
            select(UserProfile).where(UserProfile.reminder_hour == reminder_hour)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_all(session: AsyncSession) -> list[UserProfile]:
        result = await session.execute(select(UserProfile))
        return list(result.scalars().all())

    @staticmethod
    async def count_total(session: AsyncSession) -> int:
        result = await session.execute(select(func.count(UserProfile.id)))
        return int(result.scalar_one() or 0)

    @staticmethod
    async def gender_breakdown(session: AsyncSession) -> dict[str, int]:
        result = await session.execute(select(UserProfile.gender))
        rows = result.scalars().all()
        counter: Counter[str] = Counter()
        for gender in rows:
            key = (gender or "Unknown").strip().title()
            counter[key] += 1
        if not counter:
            counter["Unknown"] = 0
        return dict(counter)

    @staticmethod
    async def premium_breakdown(session: AsyncSession) -> dict[str, int]:
        result = await session.execute(
            select(
                UserProfile.is_premium,
                func.count(UserProfile.id),
            ).group_by(UserProfile.is_premium)
        )
        rows = result.all()
        counts = {"No": 0, "Yes": 0}
        for is_premium, value in rows:
            counts["Yes" if is_premium else "No"] = int(value)
        return counts

    @staticmethod
    async def list_user_lifecycle_rows(
        session: AsyncSession,
    ) -> list[tuple[date, date | None]]:
        last_log_subquery = (
            select(
                HabitLog.user_id.label("user_id"),
                func.max(HabitLog.log_date).label("last_log_date"),
            )
            .group_by(HabitLog.user_id)
            .subquery()
        )
        stmt = select(
            cast(UserProfile.created_at, Date).label("created_date"),
            last_log_subquery.c.last_log_date,
        ).outerjoin(last_log_subquery, last_log_subquery.c.user_id == UserProfile.id)
        rows = await session.execute(stmt)
        normalized: list[tuple[date, date | None]] = []
        for created_date, last_log_date in rows:
            created = UserRepository._normalize_date(created_date)
            last = UserRepository._normalize_date(last_log_date) if last_log_date else None
            normalized.append((created, last))
        return normalized

    @staticmethod
    async def update_reminder_hour(
        session: AsyncSession, user_id: int, reminder_hour: int | None
    ) -> None:
        result = await session.execute(select(UserProfile).where(UserProfile.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            return
        user.reminder_hour = reminder_hour
        await session.flush()


class HabitRepository:
    @staticmethod
    async def add_log(
        session: AsyncSession,
        user_id: int,
        habit_name: str,
        value: float,
        log_date: date,
        logged_hour: int,
        unit: str = "count",
        notes: str | None = None,
    ) -> HabitLog:
        entry = HabitLog(
            user_id=user_id,
            habit_name=habit_name.lower().strip(),
            value=value,
            log_date=log_date,
            logged_hour=logged_hour,
            unit=unit,
            notes=notes,
        )
        session.add(entry)
        await session.flush()
        return entry

    @staticmethod
    async def list_user_logs_for_day(
        session: AsyncSession, user_id: int, target_day: date
    ) -> list[HabitLog]:
        result = await session.execute(
            select(HabitLog)
            .where(and_(HabitLog.user_id == user_id, HabitLog.log_date == target_day))
            .order_by(HabitLog.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_user_logs_between(
        session: AsyncSession, user_id: int, start_day: date, end_day: date
    ) -> list[HabitLog]:
        result = await session.execute(
            select(HabitLog)
            .where(
                and_(
                    HabitLog.user_id == user_id,
                    HabitLog.log_date >= start_day,
                    HabitLog.log_date <= end_day,
                )
            )
            .order_by(HabitLog.log_date.asc(), HabitLog.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_user_logged_dates(
        session: AsyncSession, user_id: int, days_back: int
    ) -> list[date]:
        from_day = date.today() - timedelta(days=days_back)
        result = await session.execute(
            select(HabitLog.log_date)
            .where(and_(HabitLog.user_id == user_id, HabitLog.log_date >= from_day))
            .group_by(HabitLog.log_date)
            .order_by(HabitLog.log_date.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def detect_most_active_hour(
        session: AsyncSession, user_id: int, lookback_days: int = 30
    ) -> int | None:
        from_day = date.today() - timedelta(days=lookback_days)
        result = await session.execute(
            select(HabitLog.logged_hour, func.count(HabitLog.id).label("activity"))
            .where(and_(HabitLog.user_id == user_id, HabitLog.log_date >= from_day))
            .group_by(HabitLog.logged_hour)
            .order_by(desc("activity"), HabitLog.logged_hour.asc())
            .limit(1)
        )
        row = result.first()
        return int(row[0]) if row else None

    @staticmethod
    async def count_messages_on_day(session: AsyncSession, target_day: date) -> int:
        result = await session.execute(
            select(func.count(HabitLog.id)).where(HabitLog.log_date == target_day)
        )
        return int(result.scalar_one() or 0)

    @staticmethod
    async def count_sessions_on_day(session: AsyncSession, target_day: date) -> int:
        result = await session.execute(
            select(func.count(func.distinct(HabitLog.user_id))).where(HabitLog.log_date == target_day)
        )
        return int(result.scalar_one() or 0)

    @staticmethod
    async def list_recent_achievements(
        session: AsyncSession, limit: int = 5
    ) -> list[dict[str, Any]]:
        result = await session.execute(
            select(
                HabitLog.log_date,
                HabitLog.created_at,
                HabitLog.habit_name,
                HabitLog.value,
                HabitLog.unit,
                UserProfile.first_name,
                UserProfile.username,
            )
            .join(UserProfile, UserProfile.id == HabitLog.user_id)
            .order_by(HabitLog.created_at.desc())
            .limit(limit)
        )
        rows = result.all()
        payload: list[dict[str, Any]] = []
        for log_date, created_at, habit_name, value, unit, first_name, username in rows:
            payload.append(
                {
                    "date": log_date.isoformat(),
                    "timestamp": created_at.isoformat(),
                    "user": first_name or username or "Anonymous",
                    "conversion": habit_name.title(),
                    "value": f"{value:g} {unit}",
                }
            )
        return payload

    @staticmethod
    async def list_popular_habits_for_day(
        session: AsyncSession, target_day: date, limit: int = 5
    ) -> list[dict[str, Any]]:
        result = await session.execute(
            select(
                HabitLog.habit_name,
                func.count(HabitLog.id).label("number"),
                func.count(func.distinct(HabitLog.user_id)).label("unique_users"),
                func.avg(HabitLog.value).label("per_user"),
                func.sum(HabitLog.value).label("sessions"),
            )
            .where(HabitLog.log_date == target_day)
            .group_by(HabitLog.habit_name)
            .order_by(desc("number"))
            .limit(limit)
        )
        rows = result.all()
        return [
            {
                "team": f"/{habit_name}",
                "number": int(number),
                "unique": int(unique_users),
                "per_user": round(float(per_user or 0), 2),
                "sessions": round(float(sessions or 0), 2),
            }
            for habit_name, number, unique_users, per_user, sessions in rows
        ]

    @staticmethod
    async def list_leaderboard(
        session: AsyncSession, from_day: date, limit: int = 10
    ) -> list[dict[str, Any]]:
        result = await session.execute(
            select(
                UserProfile.first_name,
                UserProfile.username,
                func.sum(HabitLog.value).label("score"),
                func.count(HabitLog.id).label("logs"),
            )
            .join(UserProfile, UserProfile.id == HabitLog.user_id)
            .where(HabitLog.log_date >= from_day)
            .group_by(UserProfile.id, UserProfile.first_name, UserProfile.username)
            .order_by(desc("score"), desc("logs"))
            .limit(limit)
        )
        rows = result.all()
        return [
            {
                "name": first_name or username or "Anonymous",
                "score": round(float(score or 0), 2),
                "logs": int(logs),
            }
            for first_name, username, score, logs in rows
        ]

    @staticmethod
    async def build_daily_totals(
        session: AsyncSession, user_id: int, start_day: date, end_day: date
    ) -> dict[date, float]:
        logs = await HabitRepository.list_user_logs_between(session, user_id, start_day, end_day)
        totals: dict[date, float] = defaultdict(float)
        for log in logs:
            totals[log.log_date] += float(log.value)
        return dict(totals)

    @staticmethod
    async def list_habit_frequency(
        session: AsyncSession, user_id: int, start_day: date, end_day: date
    ) -> dict[str, int]:
        result = await session.execute(
            select(HabitLog.habit_name, func.count(HabitLog.id))
            .where(
                and_(
                    HabitLog.user_id == user_id,
                    HabitLog.log_date >= start_day,
                    HabitLog.log_date <= end_day,
                )
            )
            .group_by(HabitLog.habit_name)
        )
        return {habit_name: int(total) for habit_name, total in result.all()}


class MoodRepository:
    @staticmethod
    async def add_mood(
        session: AsyncSession,
        user_id: int,
        mood_score: int,
        mood_date: date,
        note: str | None = None,
    ) -> MoodLog:
        entry = MoodLog(
            user_id=user_id,
            mood_score=mood_score,
            mood_date=mood_date,
            note=note,
        )
        session.add(entry)
        await session.flush()
        return entry


class ReminderRepository:
    @staticmethod
    async def already_sent(
        session: AsyncSession, user_id: int, target_day: date, reminder_hour: int
    ) -> bool:
        result = await session.execute(
            select(func.count(ReminderDispatch.id)).where(
                and_(
                    ReminderDispatch.user_id == user_id,
                    ReminderDispatch.scheduled_for == target_day,
                    ReminderDispatch.reminder_hour == reminder_hour,
                )
            )
        )
        count = int(result.scalar_one() or 0)
        return count > 0

    @staticmethod
    async def add_dispatch(
        session: AsyncSession,
        user_id: int,
        target_day: date,
        reminder_hour: int,
        status: str,
    ) -> ReminderDispatch:
        dispatch = ReminderDispatch(
            user_id=user_id,
            scheduled_for=target_day,
            reminder_hour=reminder_hour,
            status=status,
        )
        session.add(dispatch)
        await session.flush()
        return dispatch
