from app.core.config import Settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)


def build_settings() -> Settings:
    return Settings(
        jwt_secret_key="test_access_secret_that_is_32_chars_long",
        jwt_refresh_secret_key="test_refresh_secret_that_is_32_chars_long",
        write_database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
        read_database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
    )


def test_password_hashing_roundtrip():
    raw = "SecurePass!123"
    hashed = hash_password(raw)
    assert verify_password(raw, hashed) is True


def test_access_token_encode_decode():
    settings = build_settings()
    token = create_access_token("user@example.com", settings, {"uid": 1, "roles": ["user"]})
    payload = decode_access_token(token, settings)
    assert payload["sub"] == "user@example.com"
    assert payload["uid"] == 1
    assert payload["type"] == "access"


def test_refresh_token_encode_decode():
    settings = build_settings()
    token = create_refresh_token("user@example.com", settings, {"uid": 1})
    payload = decode_refresh_token(token, settings)
    assert payload["sub"] == "user@example.com"
    assert payload["type"] == "refresh"
    assert "jti" in payload
