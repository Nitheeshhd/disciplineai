from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Conversion(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "conversions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversion_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    streak_length: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped["User"] = relationship(back_populates="conversions")

    __table_args__ = (
        Index("ix_conversions_user_date", "user_id", "conversion_date"),
        Index("ix_conversions_user_streak", "user_id", "streak_length"),
    )
