from hashlib import sha256
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def sha256_hexdigest(value: str) -> str:
    """Return SHA-256 hex digest for deterministic non-reversible hashing."""

    return sha256(value.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    """Build and cache Fernet cipher from environment configuration."""

    settings = get_settings()
    return Fernet(settings.bot_token_encryption_key.encode("utf-8"))


def encrypt_secret(value: str) -> str:
    """Encrypt sensitive values before persistence."""

    token = _get_fernet().encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_secret(value: str) -> str:
    """Decrypt sensitive values from persistence."""

    try:
        plain = _get_fernet().decrypt(value.encode("utf-8"))
        return plain.decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt secret") from exc
