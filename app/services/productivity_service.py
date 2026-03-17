from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from statistics import mean, pstdev

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analytics_query_repository import AnalyticsQueryRepository


@dataclass
class ProductivityMetrics:
    streak_days: int
    moving_average: float
    anomaly_detected: bool
    behavioral_score: float


class ProductivityService:
    def __init__(self, session: AsyncSession):
        self.repo = AnalyticsQueryRepository(session)

    @staticmethod
    def calculate_streak(daily_totals: dict[date, float], target_day: date | None = None) -> int:
        if target_day is None:
            target_day = date.today()
        streak = 0
        cursor = target_day
        while daily_totals.get(cursor, 0.0) > 0:
            streak += 1
            cursor = cursor - timedelta(days=1)
        return streak

    @staticmethod
    def calculate_moving_average(daily_totals: dict[date, float], days: int = 7) -> float:
        if not daily_totals:
            return 0.0
        ordered = sorted(daily_totals.items(), key=lambda item: item[0], reverse=True)
        values = [value for _, value in ordered[:days]]
        if not values:
            return 0.0
        return round(mean(values), 2)

    @staticmethod
    def detect_anomaly(daily_totals: dict[date, float]) -> bool:
        if len(daily_totals) < 8:
            return False
        ordered = sorted(daily_totals.items(), key=lambda item: item[0])
        values = [value for _, value in ordered]
        baseline = values[:-1]
        latest = values[-1]
        avg = mean(baseline)
        std_dev = pstdev(baseline) if len(baseline) > 1 else 0
        threshold = avg + (2 * std_dev)
        return latest > threshold if std_dev > 0 else latest > avg * 1.8

    @staticmethod
    def behavioral_score(streak_days: int, moving_average: float, anomaly_detected: bool) -> float:
        score = min(streak_days * 3.0, 35.0) + min(moving_average * 7.0, 50.0)
        if anomaly_detected:
            score -= 5
        return round(max(min(score, 100.0), 0.0), 2)

    async def build_metrics(self, user_id: int, days: int = 30) -> ProductivityMetrics:
        totals = await self.repo.user_daily_totals(user_id=user_id, days=days)
        streak_days = self.calculate_streak(totals)
        moving_avg = self.calculate_moving_average(totals, days=7)
        anomaly = self.detect_anomaly(totals)
        score = self.behavioral_score(streak_days, moving_avg, anomaly)
        return ProductivityMetrics(
            streak_days=streak_days,
            moving_average=moving_avg,
            anomaly_detected=anomaly,
            behavioral_score=score,
        )
