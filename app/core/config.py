from functools import lru_cache

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment configuration with strict validation for production usage."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "DisciplineAI SaaS"
    app_env: str = "development"
    app_version: str = "2.0.0"
    api_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000
    timezone: str = "UTC"
    log_level: str = "INFO"
    enable_docs: bool = True

    jwt_access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1, le=90)
    jwt_algorithm: str = "HS256"
    jwt_secret_key: str = "change_me_access_secret"
    jwt_refresh_secret_key: str = "change_me_refresh_secret"
    bot_token_encryption_key: str = "6Aa3moc7dwoJ3slSMkdFKCYf9XsU79xy1go9-ygfXjw="
    password_min_length: int = Field(default=8, ge=8, le=64)
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    rate_limit_enabled: bool = True
    rate_limit_requests: int = Field(default=120, ge=10, le=10000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)

    write_database_url: str = "sqlite+aiosqlite:///./disciplineai_enterprise.db"
    read_database_url: str = "sqlite+aiosqlite:///./disciplineai_enterprise.db"
    sql_echo: bool = False
    db_pool_size: int = Field(default=20, ge=5, le=100)
    db_max_overflow: int = Field(default=40, ge=0, le=100)

    redis_url: str = "redis://localhost:6379/0"
    dashboard_cache_ttl_seconds: int = Field(default=60, ge=10, le=3600)

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    scheduler_enabled: bool = True
    scheduler_timezone: str = "UTC"
    inactive_days_threshold: int = Field(default=7, ge=1, le=60)

    telegram_bot_token: str = "CHANGE_ME"
    webhook_base_url: str | None = None
    webhook_path: str = "/telegram/webhook"
    telegram_webhook_secret: str | None = None

    # Google OAuth
    google_client_id: str | None = Field(default=None, env="GOOGLE_CLIENT_ID")
    google_client_secret: str | None = Field(default=None, env="GOOGLE_CLIENT_SECRET")
    session_secret_key: str = Field(default="super-secret-session-key", env="SESSION_SECRET_KEY")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @computed_field
    @property
    def webhook_url(self) -> str | None:
        if not self.webhook_base_url:
            return None
        return f"{self.webhook_base_url.rstrip('/')}{self.webhook_path}"

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @computed_field
    @property
    def docs_url(self) -> str | None:
        return "/docs" if self.enable_docs else None

    @computed_field
    @property
    def redoc_url(self) -> str | None:
        return "/redoc" if self.enable_docs else None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
