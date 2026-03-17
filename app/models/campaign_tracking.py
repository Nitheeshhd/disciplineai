from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class CampaignTracking(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "campaign_tracking"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    utm_source: Mapped[str | None] = mapped_column(String(120), index=True)
    utm_medium: Mapped[str | None] = mapped_column(String(120), index=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(120), index=True)
    utm_term: Mapped[str | None] = mapped_column(String(120))
    utm_content: Mapped[str | None] = mapped_column(String(120))
    visit_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="campaign_tracking")
    session: Mapped["Session"] = relationship()

    __table_args__ = (
        Index(
            "ix_campaign_tracking_source_medium_campaign_date",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "visit_date",
        ),
    )
