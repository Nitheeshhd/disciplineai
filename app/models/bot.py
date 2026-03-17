from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Bot(Base, TimestampMixin, SoftDeleteMixin):
    """Telegram bot credentials owned by a platform user."""

    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    token: Mapped[str] = mapped_column(String(2048), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    owner: Mapped["User"] = relationship(back_populates="bots")

    __table_args__ = (
        Index("ix_bots_owner_created", "owner_id", "created_at"),
        Index("ix_bots_owner_active", "owner_id", "is_active"),
        Index("ix_bots_owner_deleted", "owner_id", "is_deleted"),
        Index("ix_bots_owner_name", "owner_id", "name"),
    )
