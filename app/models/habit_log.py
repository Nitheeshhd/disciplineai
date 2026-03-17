from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class HabitLog(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "habit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    habit_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="count", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    logged_hour: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="habit_logs")

    __table_args__ = (
        Index("ix_habit_logs_user_date", "user_id", "log_date"),
        Index("ix_habit_logs_user_habit_date", "user_id", "habit_name", "log_date"),
    )
