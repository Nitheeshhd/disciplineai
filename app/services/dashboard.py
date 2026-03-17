from __future__ import annotations

from collections import Counter
from datetime import timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import HabitRepository, UserRepository
from app.utils.time import now_in_timezone


async def build_dashboard_payload(session: AsyncSession, timezone: str) -> dict:
    local_now = now_in_timezone(timezone)
    today = local_now.date()
    start_day = today - timedelta(days=29)

    sessions_today = await HabitRepository.count_sessions_on_day(session, today)
    messages_today = await HabitRepository.count_messages_on_day(session, today)
    total_users = await UserRepository.count_total(session)
    revenue_today = 0

    lifecycle_rows = await UserRepository.list_user_lifecycle_rows(session)
    created_counter = Counter(created for created, _ in lifecycle_rows)

    labels: list[str] = []
    number_of_users: list[int] = []
    new_users: list[int] = []
    departed_users: list[int] = []

    rolling_users = sum(1 for created_date, _ in lifecycle_rows if created_date < start_day)
    for offset in range(30):
        day = start_day + timedelta(days=offset)
        day_label = day.strftime("%b %d")
        labels.append(day_label)

        created_today = created_counter.get(day, 0)
        rolling_users += created_today
        new_users.append(created_today)
        number_of_users.append(rolling_users)

        inactivity_cutoff = day - timedelta(days=7)
        departed = sum(
            1
            for created_date, last_log_date in lifecycle_rows
            if created_date <= day
            and (last_log_date is None or last_log_date <= inactivity_cutoff)
        )
        departed_users.append(departed)

    gender_breakdown = await UserRepository.gender_breakdown(session)
    premium_breakdown = await UserRepository.premium_breakdown(session)
    recent_achievements = await HabitRepository.list_recent_achievements(session, limit=6)
    popular_habits = await HabitRepository.list_popular_habits_for_day(session, today, limit=6)

    if not recent_achievements:
        recent_achievements = [
            {
                "date": local_now.strftime("%Y-%m-%d"),
                "timestamp": local_now.isoformat(),
                "user": "No data yet",
                "conversion": "Start logging",
                "value": "0",
            }
        ]
    if not popular_habits:
        popular_habits = [
            {"team": "/study", "number": 0, "unique": 0, "per_user": 0.0, "sessions": 0.0}
        ]

    return {
        "overview": {
            "sessions_today": sessions_today,
            "total_users": total_users,
            "messages_today": messages_today,
            "revenue_today": revenue_today,
        },
        "trends": {
            "labels": labels,
            "number_of_users": number_of_users,
            "new_users": new_users,
            "departed_users": departed_users,
        },
        "gender": {
            "labels": list(gender_breakdown.keys()),
            "values": list(gender_breakdown.values()),
        },
        "premium": {
            "labels": list(premium_breakdown.keys()),
            "values": list(premium_breakdown.values()),
        },
        "recent_achievements": recent_achievements,
        "popular_habits": popular_habits,
        "updated_at": local_now.astimezone(ZoneInfo("UTC")).isoformat(),
    }
