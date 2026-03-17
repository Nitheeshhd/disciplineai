from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin


class DailyTaskStatus(Base, TimestampMixin):
    __tablename__ = "daily_task_statuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    task_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship(back_populates="daily_task_statuses")

    __table_args__ = (
        UniqueConstraint("user_id", "task_name", "task_date", name="uq_daily_task_statuses_user_task_date"),
        Index("ix_daily_task_statuses_user_date_status", "user_id", "task_date", "status"),
    )
