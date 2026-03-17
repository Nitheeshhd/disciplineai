from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from telegram.ext import Application, CommandHandler, ContextTypes

from app.bot.commands import (
    help_command,
    leaderboard_command,
    log_command,
    mood_command,
    start_command,
    streak_command,
    summary_command,
    weekly_command,
)
from app.config import Settings

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled Telegram handler error. update=%s", update, exc_info=context.error)


def build_telegram_application(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> Application:
    telegram_app = Application.builder().token(settings.telegram_bot_token).build()
    telegram_app.bot_data["settings"] = settings
    telegram_app.bot_data["session_factory"] = session_factory

    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("log", log_command))
    telegram_app.add_handler(CommandHandler("summary", summary_command))
    telegram_app.add_handler(CommandHandler("weekly", weekly_command))
    telegram_app.add_handler(CommandHandler("streak", streak_command))
    telegram_app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    telegram_app.add_handler(CommandHandler("mood", mood_command))
    telegram_app.add_error_handler(error_handler)
    return telegram_app
