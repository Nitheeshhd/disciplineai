from __future__ import annotations

from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversion import Conversion
from app.models.habit_log import HabitLog
from app.models.message import Message
from app.models.payment import Payment
from app.models.read_models import DailyAnalyticsReadModel
from app.models.user import User


class AnalyticsProjectionRepository:
    """
    Write-side projection repository that maintains read model tables.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_day(self, metric_date: date) -> DailyAnalyticsReadModel:
        existing_stmt = select(DailyAnalyticsReadModel).where(DailyAnalyticsReadModel.metric_date == metric_date)
        existing_result = await self.session.execute(existing_stmt)
        model = existing_result.scalar_one_or_none()
        if model is None:
            model = DailyAnalyticsReadModel(metric_date=metric_date)
            self.session.add(model)
            await self.session.flush()

        sessions_stmt = select(func.count(func.distinct(HabitLog.user_id))).where(
            and_(HabitLog.log_date == metric_date, HabitLog.is_deleted.is_(False))
        )
        users_stmt = select(func.count(User.id)).where(User.is_deleted.is_(False))
        messages_stmt = select(func.count(Message.id)).where(
            and_(Message.message_date == metric_date, Message.is_deleted.is_(False))
        )
        revenue_stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            and_(
                Payment.paid_date == metric_date,
                Payment.payment_status == "paid",
                Payment.is_deleted.is_(False),
            )
        )
        conversion_stmt = select(func.count(Conversion.id)).where(
            and_(Conversion.conversion_date == metric_date, Conversion.is_deleted.is_(False))
        )
        productivity_stmt = select(func.coalesce(func.avg(HabitLog.value), 0)).where(
            and_(HabitLog.log_date == metric_date, HabitLog.is_deleted.is_(False))
        )

        sessions = int((await self.session.execute(sessions_stmt)).scalar_one() or 0)
        users = int((await self.session.execute(users_stmt)).scalar_one() or 0)
        messages = int((await self.session.execute(messages_stmt)).scalar_one() or 0)
        revenue = float((await self.session.execute(revenue_stmt)).scalar_one() or 0.0)
        conversions = int((await self.session.execute(conversion_stmt)).scalar_one() or 0)
        avg_productivity = float((await self.session.execute(productivity_stmt)).scalar_one() or 0.0)

        model.sessions_count = sessions
        model.users_count = users
        model.messages_count = messages
        model.revenue_total = round(revenue, 2)
        model.avg_productivity = round(avg_productivity, 2)
        model.conversion_rate = round((conversions / sessions * 100) if sessions else 0.0, 2)

        await self.session.flush()
        return model
