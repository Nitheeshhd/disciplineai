from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.badge import Badge
    from app.models.bot import Bot
    from app.models.campaign import Campaign
    from app.models.campaign_tracking import CampaignTracking
    from app.models.conversion import Conversion
    from app.models.habit_log import HabitLog
    from app.models.message import Message
    from app.models.payment import Payment
    from app.models.role import Role
    from app.models.session import Session
    from app.models.task_status import DailyTaskStatus


class User(Base, TimestampMixin, SoftDeleteMixin):
    """Core user entity for authentication and analytics ownership."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    picture: Mapped[str | None] = mapped_column(String(512))
    name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    age: Mapped[int | None] = mapped_column(nullable=True)
    level: Mapped[str] = mapped_column(String(32), default="Achiever", nullable=False)
    streak_days: Mapped[int] = mapped_column(default=0, nullable=False)
    highest_productivity_score: Mapped[float] = mapped_column(default=0.0, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(120))
    last_name: Mapped[str | None] = mapped_column(String(120))
    username: Mapped[str | None] = mapped_column(String(64), index=True)
    gender: Mapped[str | None] = mapped_column(String(20), index=True)
    locale: Mapped[str | None] = mapped_column(String(16))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    roles: Mapped[list["Role"]] = relationship(
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",
    )
    sessions: Mapped[list["Session"]] = relationship(back_populates="user", lazy="selectin")
    messages: Mapped[list["Message"]] = relationship(back_populates="user", lazy="selectin")
    payments: Mapped[list["Payment"]] = relationship(back_populates="user", lazy="selectin")
    bots: Mapped[list["Bot"]] = relationship(back_populates="owner", lazy="selectin")
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="user", lazy="selectin")
    habit_logs: Mapped[list["HabitLog"]] = relationship(back_populates="user", lazy="selectin")
    daily_task_statuses: Mapped[list["DailyTaskStatus"]] = relationship(back_populates="user", lazy="selectin")
    badges: Mapped[list["Badge"]] = relationship(back_populates="user", lazy="selectin")
    conversions: Mapped[list["Conversion"]] = relationship(back_populates="user", lazy="selectin")
    campaign_tracking: Mapped[list["CampaignTracking"]] = relationship(back_populates="user", lazy="selectin")

    __table_args__ = (
        CheckConstraint("length(email) >= 5", name="ck_users_email_len"),
        Index("ix_users_active_deleted", "is_active", "is_deleted"),
        Index("ix_users_premium_deleted", "is_premium", "is_deleted"),
        Index("ix_users_created_at", "created_at"),
    )
