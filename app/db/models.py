from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    logs: Mapped[list[HabitLog]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    mood_logs: Mapped[list[MoodLog]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    reminder_dispatches: Mapped[list[ReminderDispatch]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "reminder_hour IS NULL OR (reminder_hour >= 0 AND reminder_hour <= 23)",
            name="ck_user_profiles_reminder_hour",
        ),
    )


class HabitLog(Base):
    __tablename__ = "habit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), index=True)
    habit_name: Mapped[str] = mapped_column(String(80), index=True)
    value: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[str] = mapped_column(String(20), default="count")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    log_date: Mapped[date] = mapped_column(Date, index=True)
    logged_hour: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[UserProfile] = relationship(back_populates="logs")

    __table_args__ = (
        CheckConstraint("logged_hour >= 0 AND logged_hour <= 23", name="ck_habit_logs_logged_hour"),
    )


class MoodLog(Base):
    __tablename__ = "mood_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), index=True)
    mood_score: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    mood_date: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[UserProfile] = relationship(back_populates="mood_logs")

    __table_args__ = (
        CheckConstraint("mood_score >= 1 AND mood_score <= 5", name="ck_mood_logs_score"),
    )


class ReminderDispatch(Base):
    __tablename__ = "reminder_dispatches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), index=True)
    scheduled_for: Mapped[date] = mapped_column(Date, index=True)
    reminder_hour: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(20), default="sent")
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[UserProfile] = relationship(back_populates="reminder_dispatches")

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "scheduled_for",
            "reminder_hour",
            name="uq_reminder_dispatches_user_day_hour",
        ),
        CheckConstraint("reminder_hour >= 0 AND reminder_hour <= 23", name="ck_reminder_hour"),
    )
