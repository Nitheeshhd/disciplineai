from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from app.core.database import _ensure_user_nullable_oauth_fields, _ensure_user_profile_columns
from app.models.user import User


def test_sqlite_users_table_allows_nullable_oauth_fields(tmp_path: Path):
    db_path = tmp_path / "legacy_users.db"
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER NOT NULL PRIMARY KEY,
                    telegram_user_id BIGINT NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    first_name VARCHAR(120),
                    last_name VARCHAR(120),
                    username VARCHAR(64),
                    gender VARCHAR(20),
                    locale VARCHAR(16),
                    timezone VARCHAR(64) NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    is_verified BOOLEAN NOT NULL,
                    is_premium BOOLEAN NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    is_deleted BOOLEAN NOT NULL,
                    deleted_at DATETIME,
                    CONSTRAINT ck_users_email_len CHECK (length(email) >= 5),
                    UNIQUE (telegram_user_id),
                    UNIQUE (email)
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX ix_users_username ON users (username)"))
        conn.execute(text("CREATE INDEX ix_users_gender ON users (gender)"))
        conn.execute(
            text(
                """
                CREATE TABLE sessions (
                    id INTEGER NOT NULL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO users (
                    id, telegram_user_id, email, hashed_password, first_name, last_name, username,
                    gender, locale, timezone, is_active, is_verified, is_premium, created_at,
                    updated_at, is_deleted, deleted_at
                ) VALUES (
                    1, 123456, 'legacy@example.com', 'hashed', 'Legacy', 'User', 'legacy_user',
                    NULL, NULL, 'UTC', 1, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, NULL
                )
                """
            )
        )
        conn.execute(text("INSERT INTO sessions (id, user_id) VALUES (1, 1)"))

        _ensure_user_nullable_oauth_fields(conn)
        _ensure_user_profile_columns(conn)

        columns = {column["name"]: column for column in inspect(conn).get_columns("users")}
        assert columns["telegram_user_id"]["nullable"] is True
        assert columns["hashed_password"]["nullable"] is True
        assert "full_name" in columns
        assert "picture" in columns
        assert "name" in columns
        foreign_keys = conn.execute(text("PRAGMA foreign_key_list('sessions')")).mappings().all()
        assert foreign_keys[0]["table"] == "users"

        oauth_insert_columns = [
            column.name
            for column in User.__table__.columns
            if column.name != "id"
        ]
        oauth_insert_values = {
            "telegram_user_id": None,
            "email": "oauth@example.com",
            "hashed_password": None,
            "full_name": "OAuth User",
            "picture": "https://example.com/avatar.png",
            "name": "OAuth User",
            "phone": None,
            "age": None,
            "level": "Achiever",
            "streak_days": 0,
            "highest_productivity_score": 0.0,
            "first_name": None,
            "last_name": None,
            "username": None,
            "gender": None,
            "locale": None,
            "timezone": "UTC",
            "is_active": True,
            "is_verified": True,
            "is_premium": False,
            "created_at": "2026-03-30 16:44:50.916120",
            "updated_at": "2026-03-30 16:44:50.916124",
            "is_deleted": False,
            "deleted_at": None,
        }
        column_sql = ", ".join(oauth_insert_columns)
        value_sql = ", ".join(f":{column_name}" for column_name in oauth_insert_columns)
        conn.execute(text(f"INSERT INTO users ({column_sql}) VALUES ({value_sql})"), oauth_insert_values)

        inserted = conn.execute(
            text("SELECT telegram_user_id, hashed_password, email FROM users WHERE email = :email"),
            {"email": "oauth@example.com"},
        ).mappings().one()
        assert inserted["telegram_user_id"] is None
        assert inserted["hashed_password"] is None
