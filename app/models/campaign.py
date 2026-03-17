from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Campaign(Base):
    """UTM campaign entity owned by a single authenticated user."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    base_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    utm_source: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    utm_medium: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    utm_campaign: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    full_url: Mapped[str] = mapped_column(String(4096), nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    user: Mapped["User"] = relationship(back_populates="campaigns")

    __table_args__ = (
        Index("ix_campaigns_user_created", "user_id", "created_at"),
        Index("ix_campaigns_user_utm_triplet", "user_id", "utm_source", "utm_medium", "utm_campaign"),
    )

