from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.base import Base

settings = get_settings()


def _build_engine(database_url: str) -> AsyncEngine:
    kwargs = {"echo": settings.sql_echo, "pool_pre_ping": True}
    if not database_url.startswith("sqlite"):
        kwargs["pool_size"] = settings.db_pool_size
        kwargs["max_overflow"] = settings.db_max_overflow
    return create_async_engine(database_url, **kwargs)


write_engine = _build_engine(settings.write_database_url)
read_engine = _build_engine(settings.read_database_url)

WriteSessionLocal = async_sessionmaker(
    bind=write_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

ReadSessionLocal = async_sessionmaker(
    bind=read_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_write_session() -> AsyncIterator[AsyncSession]:
    async with WriteSessionLocal() as session:
        yield session


async def get_read_session() -> AsyncIterator[AsyncSession]:
    async with ReadSessionLocal() as session:
        yield session


def _ensure_user_profile_columns(sync_conn) -> None:
    inspector = inspect(sync_conn)
    try:
        existing_columns = {column["name"] for column in inspector.get_columns("users")}
    except Exception:
        return

    alter_statements: list[str] = []
    if "name" not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN name VARCHAR(255)")
    if "phone" not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN phone VARCHAR(30)")
    if "age" not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN age INTEGER")
    if "level" not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN level VARCHAR(32) NOT NULL DEFAULT 'Achiever'")
    if "streak_days" not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN streak_days INTEGER NOT NULL DEFAULT 0")
    if "highest_productivity_score" not in existing_columns:
        alter_statements.append(
            "ALTER TABLE users ADD COLUMN highest_productivity_score FLOAT NOT NULL DEFAULT 0"
        )

    for statement in alter_statements:
        sync_conn.execute(text(statement))


async def init_models() -> None:
    # Import all models to register metadata before create_all.
    from app.models import (  # noqa: F401
        badge,
        bot,
        campaign,
        campaign_tracking,
        conversion,
        domain_event,
        error_log,
        habit_log,
        message,
        payment,
        report,
        read_models,
        role,
        session,
        task_status,
        user,
    )

    async with write_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_user_profile_columns)
