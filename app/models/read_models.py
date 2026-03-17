from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin


class DailyAnalyticsReadModel(Base, TimestampMixin):
    """
    CQRS read model with denormalized daily metrics for dashboard and analytics queries.
    """

    __tablename__ = "daily_analytics_read_model"

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    sessions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    users_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    messages_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_productivity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    __table_args__ = (
        Index("ix_daily_analytics_metric_date", "metric_date"),
    )
