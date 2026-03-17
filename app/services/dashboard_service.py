from __future__ import annotations

import json
from datetime import date

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import ApplicationError
from app.core.redis import redis_client
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.habit_repository import HabitRepository
from app.repositories.user_repository import UserRepository


class DashboardService:
    """Application service for dashboard-related business use cases."""

    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings
        self.dashboard_repo = DashboardRepository(session)
        self.habit_repo = HabitRepository(session)
        self.user_repo = UserRepository(session)

    async def get_summary(self, today: date) -> dict:
        """Get dashboard summary from cache/database with resilient error handling."""

        key = f"dashboard:summary:{today.isoformat()}"
        try:
            cached = await redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

        try:
            summary = await self.dashboard_repo.summary_today(today)
        except SQLAlchemyError as exc:
            raise ApplicationError(
                message="Failed to compute dashboard summary",
                code="dashboard_summary_failed",
                status_code=500,
            ) from exc
        try:
            await redis_client.set(
                key,
                json.dumps(summary, ensure_ascii=True),
                ex=self.settings.dashboard_cache_ttl_seconds,
            )
        except Exception:
            pass
        return summary

    async def dashboard_data(self, today: date) -> dict:
        summary = await self.get_summary(today)
        productivity = await self.dashboard_repo.productivity_trend(days=30)
        gender = await self.dashboard_repo.demographic_breakdown()
        premium = await self.dashboard_repo.premium_breakdown()
        recent_achievements_raw = await self.habit_repo.list_recent_goal_achievements(limit=6)
        popular = await self.habit_repo.list_popular_habits_today(target_day=today, limit=6)

        user_map = {}
        for row in recent_achievements_raw:
            if row["user_id"] not in user_map:
                user = await self.user_repo.get_by_id(row["user_id"])
                user_map[row["user_id"]] = (
                    (user.first_name if user and user.first_name else user.username if user else None)
                    or "Anonymous"
                )

        recent_achievements = [
            {
                "date": row["date"],
                "user": user_map[row["user_id"]],
                "conversion": row["conversion"].title(),
                "value": row["value"],
            }
            for row in recent_achievements_raw
        ]

        if not recent_achievements:
            recent_achievements = [{"date": today.isoformat(), "user": "No data", "conversion": "-", "value": "0"}]
        if not popular:
            popular = [{"team": "/habit", "number": 0, "unique": 0, "per_user": 0.0, "sessions": 0.0}]

        return {
            "summary": summary,
            "productivity_trend": productivity,
            "gender_breakdown": gender,
            "premium_breakdown": premium,
            "recent_goal_achievements": recent_achievements,
            "popular_teams": popular,
        }
