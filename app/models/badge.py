from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin


class Badge(Base, TimestampMixin):
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    badge_name: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    date_earned: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="badges")

    __table_args__ = (
        UniqueConstraint("user_id", "badge_name", name="uq_badges_user_badge_name"),
        Index("ix_badges_user_date", "user_id", "date_earned"),
    )
