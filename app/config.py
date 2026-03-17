from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized environment configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "DisciplineAI"
    app_env: str = "development"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    enable_telegram_bot: bool = True
    telegram_bot_token: str = "CHANGE_ME"
    webhook_base_url: str | None = None
    webhook_path: str = "/telegram/webhook"
    telegram_webhook_secret: str | None = None

    database_url: str = "sqlite+aiosqlite:///./disciplineai.db"
    sql_echo: bool = False

    timezone: str = "Asia/Kolkata"
    scheduler_enabled: bool = True
    reminder_text: str = "Time to log your progress. Use /log <habit> <value>."
    dashboard_refresh_seconds: int = Field(default=60, ge=10, le=3600)
    goal_daily_target: float = Field(default=8.0, ge=1.0, le=100.0)

    @property
    def webhook_url(self) -> str | None:
        if not self.webhook_base_url:
            return None
        return f"{self.webhook_base_url.rstrip('/')}{self.webhook_path}"

    @property
    def telegram_enabled(self) -> bool:
        return self.enable_telegram_bot and self.telegram_bot_token not in {"", "CHANGE_ME"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
