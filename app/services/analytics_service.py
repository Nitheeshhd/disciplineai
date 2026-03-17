from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analytics_query_repository import AnalyticsQueryRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.services.productivity_service import ProductivityService


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.query_repo = AnalyticsQueryRepository(session)
        self.dashboard_repo = DashboardRepository(session)
        self.productivity = ProductivityService(session)

    async def productivity_trend(self, days: int = 30) -> dict:
        labels, values = await self.query_repo.productivity_points(days=days)
        return {"labels": labels, "values": values}

    async def demographic_breakdown(self) -> dict:
        return await self.dashboard_repo.demographic_breakdown()

    async def conversion_rate(self, days: int = 30) -> dict:
        return {"rate": await self.dashboard_repo.conversion_rate(days=days)}

    async def revenue_trend(self, days: int = 30) -> dict:
        return {"points": await self.dashboard_repo.revenue_trend(days=days)}

    async def productivity_metrics(self, user_id: int) -> dict:
        metrics = await self.productivity.build_metrics(user_id=user_id, days=30)
        return {
            "streak_days": metrics.streak_days,
            "moving_average": metrics.moving_average,
            "anomaly_detected": metrics.anomaly_detected,
            "behavioral_score": metrics.behavioral_score,
        }
