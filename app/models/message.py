from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Message(Base, TimestampMixin, SoftDeleteMixin):
    """Inbound/outbound Telegram message telemetry for analytics."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_chat_id: Mapped[int] = mapped_column(index=True)
    telegram_message_id: Mapped[int] = mapped_column(index=True)
    message_type: Mapped[str] = mapped_column(String(40), index=True)
    message_text: Mapped[str | None] = mapped_column(String(2000))
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    message_date: Mapped[date] = mapped_column(Date, index=True)

    user: Mapped["User"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_messages_user_date_type", "user_id", "message_date", "message_type"),
        Index("ix_messages_chat_msgid", "telegram_chat_id", "telegram_message_id", unique=True),
        Index("ix_messages_created_at", "created_at"),
    )
