from __future__ import annotations

from datetime import timedelta

from telegram import Update
from telegram.ext import ContextTypes

from app.db.repositories import HabitRepository, MoodRepository, UserRepository
from app.services.analytics import build_daily_summary, build_weekly_points
from app.services.graphing import render_weekly_productivity_chart
from app.utils.time import now_in_timezone


def _format_summary(summary_text: list[str]) -> str:
    return "\n".join(summary_text)


def _safe_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return

    settings = context.application.bot_data["settings"]
    session_factory = context.application.bot_data["session_factory"]
    now_local = now_in_timezone(settings.timezone)

    async with session_factory() as session:
        await UserRepository.get_or_create_from_telegram(
            session=session,
            telegram_user=update.effective_user,
            timezone=settings.timezone,
            seen_at=now_local,
        )
        await session.commit()

    await update.message.reply_text(
        "Welcome to DisciplineAI.\n"
        "Track habits and get intelligent productivity insights.\n\n"
        "Commands:\n"
        "/log <habit> <value> [notes]\n"
        "/summary\n"
        "/weekly\n"
        "/streak\n"
        "/leaderboard\n"
        "/mood <1-5> [note]\n"
        "/help"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "Usage:\n"
        "/log study 3\n"
        "/log workout 1.5 morning session\n"
        "/summary -> daily productivity report\n"
        "/weekly -> weekly chart\n"
        "/streak -> current streak\n"
        "/leaderboard -> top users (last 7 days)\n"
        "/mood 4 felt focused"
    )


async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /log <habit> <value> [notes]")
        return

    habit_name = context.args[0].strip().lower()
    parsed_value = _safe_float(context.args[1])
    notes = " ".join(context.args[2:]).strip() if len(context.args) > 2 else None
    if parsed_value is None:
        await update.message.reply_text("Value must be numeric. Example: /log study 3")
        return
    if parsed_value < 0:
        await update.message.reply_text("Value must be non-negative.")
        return

    settings = context.application.bot_data["settings"]
    session_factory = context.application.bot_data["session_factory"]
    now_local = now_in_timezone(settings.timezone)

    async with session_factory() as session:
        user = await UserRepository.get_or_create_from_telegram(
            session=session,
            telegram_user=update.effective_user,
            timezone=settings.timezone,
            seen_at=now_local,
        )
        await HabitRepository.add_log(
            session=session,
            user_id=user.id,
            habit_name=habit_name,
            value=parsed_value,
            log_date=now_local.date(),
            logged_hour=now_local.hour,
            notes=notes,
        )
        await session.commit()

    await update.message.reply_text(
        f"Logged: {habit_name} = {parsed_value:g} ({now_local.strftime('%Y-%m-%d %H:%M')})"
    )


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return

    settings = context.application.bot_data["settings"]
    session_factory = context.application.bot_data["session_factory"]
    now_local = now_in_timezone(settings.timezone)

    async with session_factory() as session:
        user = await UserRepository.get_or_create_from_telegram(
            session=session,
            telegram_user=update.effective_user,
            timezone=settings.timezone,
            seen_at=now_local,
        )
        summary = await build_daily_summary(
            session=session,
            user=user,
            target_day=now_local.date(),
            goal_daily_target=settings.goal_daily_target,
        )
        await session.commit()

    lines = [
        f"Date: {summary.date.isoformat()}",
        f"Total value: {summary.total_value:g}",
        f"Habit logs: {summary.habits_logged}",
        f"Streak: {summary.streak} day(s)",
        f"Productivity score: {summary.productivity_score}/100",
    ]
    if summary.low_productivity_days:
        low_days = ", ".join(day.isoformat() for day in summary.low_productivity_days[-4:])
        lines.append(f"Low productivity days: {low_days}")
    if summary.skipped_habits:
        skipped = ", ".join(habit.title() for habit in summary.skipped_habits[:5])
        lines.append(f"Skipped habits detected: {skipped}")
    lines.append("AI suggestions:")
    for suggestion in summary.suggestions[:3]:
        lines.append(f"- {suggestion}")

    await update.message.reply_text(_format_summary(lines))


async def weekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return

    settings = context.application.bot_data["settings"]
    session_factory = context.application.bot_data["session_factory"]
    now_local = now_in_timezone(settings.timezone)

    async with session_factory() as session:
        user = await UserRepository.get_or_create_from_telegram(
            session=session,
            telegram_user=update.effective_user,
            timezone=settings.timezone,
            seen_at=now_local,
        )
        points = await build_weekly_points(session, user.id, now_local.date())
        await session.commit()

    chart = render_weekly_productivity_chart(
        points,
        title=f"{(user.first_name or 'Your')} Weekly Productivity",
    )
    await update.message.reply_photo(
        photo=chart,
        caption="Weekly analytics: value trend and habit volume.",
    )


async def streak_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return

    settings = context.application.bot_data["settings"]
    session_factory = context.application.bot_data["session_factory"]
    now_local = now_in_timezone(settings.timezone)

    async with session_factory() as session:
        user = await UserRepository.get_or_create_from_telegram(
            session=session,
            telegram_user=update.effective_user,
            timezone=settings.timezone,
            seen_at=now_local,
        )
        summary = await build_daily_summary(
            session=session,
            user=user,
            target_day=now_local.date(),
            goal_daily_target=settings.goal_daily_target,
        )
        await session.commit()

    await update.message.reply_text(
        f"Current streak: {summary.streak} day(s)\n"
        f"Today's productivity score: {summary.productivity_score}/100"
    )


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    settings = context.application.bot_data["settings"]
    session_factory = context.application.bot_data["session_factory"]
    now_local = now_in_timezone(settings.timezone)
    week_start = now_local.date() - timedelta(days=6)

    async with session_factory() as session:
        rows = await HabitRepository.list_leaderboard(session, from_day=week_start, limit=10)

    if not rows:
        await update.message.reply_text("Leaderboard is empty. Start with /log <habit> <value>.")
        return

    message_lines = [f"Leaderboard ({week_start.isoformat()} to {now_local.date().isoformat()}):"]
    for idx, item in enumerate(rows, start=1):
        message_lines.append(
            f"{idx}. {item['name']} | score={item['score']} | logs={item['logs']}"
        )
    await update.message.reply_text("\n".join(message_lines))


async def mood_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /mood <1-5> [note]")
        return

    mood_value = _safe_float(context.args[0])
    if mood_value is None or int(mood_value) != mood_value or not 1 <= int(mood_value) <= 5:
        await update.message.reply_text("Mood must be an integer from 1 to 5.")
        return
    note = " ".join(context.args[1:]).strip() if len(context.args) > 1 else None

    settings = context.application.bot_data["settings"]
    session_factory = context.application.bot_data["session_factory"]
    now_local = now_in_timezone(settings.timezone)

    async with session_factory() as session:
        user = await UserRepository.get_or_create_from_telegram(
            session=session,
            telegram_user=update.effective_user,
            timezone=settings.timezone,
            seen_at=now_local,
        )
        await MoodRepository.add_mood(
            session=session,
            user_id=user.id,
            mood_score=int(mood_value),
            mood_date=now_local.date(),
            note=note,
        )
        await session.commit()

    await update.message.reply_text(f"Mood saved: {int(mood_value)}/5")
