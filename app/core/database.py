from __future__ import annotations

from collections.abc import AsyncIterator
import logging

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.base import Base

settings = get_settings()
logger = logging.getLogger(__name__)


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
    if "full_name" not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN full_name VARCHAR(255)")
    if "picture" not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN picture VARCHAR(512)")
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


def _ensure_user_nullable_oauth_fields(sync_conn) -> None:
    inspector = inspect(sync_conn)
    try:
        existing_columns = {
            column["name"]: column
            for column in inspector.get_columns("users")
        }
    except Exception:
        return

    nullable_columns = ("telegram_user_id", "hashed_password")
    columns_to_fix = [
        column_name
        for column_name in nullable_columns
        if column_name in existing_columns and not existing_columns[column_name].get("nullable", True)
    ]
    if not columns_to_fix:
        return

    dialect_name = sync_conn.dialect.name
    if dialect_name == "sqlite":
        _rebuild_sqlite_users_table(sync_conn, set(existing_columns))
        logger.info("Rebuilt SQLite users table to allow nullable OAuth fields: %s", ", ".join(columns_to_fix))
        return

    for column_name in columns_to_fix:
        sync_conn.execute(text(f"ALTER TABLE users ALTER COLUMN {column_name} DROP NOT NULL"))
    logger.info("Updated users table to allow nullable OAuth fields: %s", ", ".join(columns_to_fix))


def _rebuild_sqlite_users_table(sync_conn, existing_column_names: set[str]) -> None:
    from app.models.user import User

    sync_conn.execute(text("PRAGMA foreign_keys=OFF"))
    sync_conn.execute(text("PRAGMA legacy_alter_table=ON"))
    try:
        sync_conn.execute(text("ALTER TABLE users RENAME TO users__legacy"))

        legacy_indexes = sync_conn.execute(text("PRAGMA index_list('users__legacy')")).mappings().all()
        for index in legacy_indexes:
            index_name = index["name"]
            if index_name.startswith("sqlite_autoindex"):
                continue
            sync_conn.execute(text(f'DROP INDEX IF EXISTS "{index_name}"'))

        User.__table__.create(sync_conn)

        insert_column_names: list[str] = []
        select_expressions: list[str] = []
        insert_params: dict[str, object] = {}
        for column in User.__table__.columns:
            insert_column_names.append(column.name)
            if column.name in existing_column_names:
                select_expressions.append(f'"{column.name}"')
                continue

            default = _get_column_default_value(column)
            if default is not None:
                bind_name = f"compat_{column.name}"
                insert_params[bind_name] = default
                select_expressions.append(f':{bind_name} AS "{column.name}"')
                continue

            if column.nullable:
                select_expressions.append(f'NULL AS "{column.name}"')
                continue

            raise RuntimeError(f"Unable to rebuild users table: missing non-null column '{column.name}' has no default")

        insert_columns_sql = ", ".join(f'"{column_name}"' for column_name in insert_column_names)
        select_sql = ", ".join(select_expressions)
        sync_conn.execute(
            text(
                f'INSERT INTO users ({insert_columns_sql}) '
                f'SELECT {select_sql} FROM users__legacy'
            ),
            insert_params,
        )
        sync_conn.execute(text("DROP TABLE users__legacy"))
    finally:
        sync_conn.execute(text("PRAGMA legacy_alter_table=OFF"))
        sync_conn.execute(text("PRAGMA foreign_keys=ON"))


def _get_column_default_value(column) -> object | None:
    default = getattr(column, "default", None)
    if default is not None and getattr(default, "is_scalar", False):
        return default.arg
    return None


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
        await conn.run_sync(_ensure_user_nullable_oauth_fields)
        await conn.run_sync(_ensure_user_profile_columns)
