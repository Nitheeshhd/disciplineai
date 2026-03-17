from __future__ import annotations

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin


class DomainEventOutbox(Base, TimestampMixin):
    __tablename__ = "domain_event_outbox"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    aggregate_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    published: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)

    __table_args__ = (
        Index("ix_domain_event_outbox_published_created", "published", "created_at"),
    )
