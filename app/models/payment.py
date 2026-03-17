from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Payment(Base, TimestampMixin, SoftDeleteMixin):
    """Payment transaction record for monetization analytics."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(40), index=True)
    transaction_ref: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    payment_status: Mapped[str] = mapped_column(String(30), default="paid", nullable=False, index=True)
    paid_date: Mapped[date] = mapped_column(Date, index=True)

    user: Mapped["User"] = relationship(back_populates="payments")

    __table_args__ = (
        Index("ix_payments_user_paid_date", "user_id", "paid_date"),
        Index("ix_payments_status_date", "payment_status", "paid_date"),
        Index("ix_payments_created_at", "created_at"),
    )
