from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserProfile
from app.db.repositories import HabitRepository


@dataclass
class DailySummary:
    date: date
    total_value: float
    habits_logged: int
    streak: int
    productivity_score: float
    low_productivity_days: list[date]
    skipped_habits: list[str]
    suggestions: list[str]


def calculate_streak(logged_dates: set[date], reference_day: date) -> int:
    streak = 0
    cursor = reference_day
    while cursor in logged_dates:
        streak += 1
        cursor = cursor - timedelta(days=1)
    return streak


def productivity_score(
    total_value: float,
    habits_logged: int,
    streak: int,
    goal_daily_target: float,
) -> float:
    # Weighted score uses output volume, day-to-day consistency, and habit diversity.
    output_component = min(total_value / goal_daily_target, 1.5) * 55
    consistency_component = min(streak / 14, 1.0) * 30
    diversity_component = min(habits_logged / 5, 1.0) * 15
    return round(min(output_component + consistency_component + diversity_component, 100.0), 2)


def detect_low_productivity_days(daily_totals: dict[date, float]) -> list[date]:
    if len(daily_totals) < 5:
        return []
    values = list(daily_totals.values())
    average_value = sum(values) / len(values)
    threshold = max(average_value * 0.6, 1.0)
    return sorted([day for day, total in daily_totals.items() if total < threshold])


def detect_skipped_habits(
    habit_frequency: dict[str, int], today_habits: set[str], minimum_frequency: int = 3
) -> list[str]:
    skipped = [
        habit
        for habit, frequency in habit_frequency.items()
        if frequency >= minimum_frequency and habit not in today_habits
    ]
    return sorted(skipped)


def build_suggestions(
    low_productivity_days: list[date],
    skipped_habits: list[str],
    streak: int,
    active_hour: int | None,
) -> list[str]:
    suggestions: list[str] = []
    if low_productivity_days:
        days = ", ".join(day.strftime("%a") for day in low_productivity_days[-3:])
        suggestions.append(f"Protect your weakest days ({days}) with a 15-minute starter task.")
    if skipped_habits:
        skipped_text = ", ".join(habit.title() for habit in skipped_habits[:3])
        suggestions.append(f"Pre-schedule skipped habits: {skipped_text}.")
    if streak < 3:
        suggestions.append("Aim for 3 consecutive days first; consistency beats intensity.")
    if active_hour is not None:
        suggestions.append(
            f"Your most active hour is around {active_hour:02d}:00. Keep reminders centered there."
        )
    if not suggestions:
        suggestions.append("Great consistency. Increase one high-impact habit by 10% this week.")
    return suggestions


async def build_daily_summary(
    session: AsyncSession,
    user: UserProfile,
    target_day: date,
    goal_daily_target: float,
) -> DailySummary:
    window_start = target_day - timedelta(days=13)
    logs_today = await HabitRepository.list_user_logs_for_day(session, user.id, target_day)
    logs_window = await HabitRepository.list_user_logs_between(
        session,
        user.id,
        window_start,
        target_day,
    )
    totals_by_day: dict[date, float] = defaultdict(float)
    for entry in logs_window:
        totals_by_day[entry.log_date] += float(entry.value)
    logged_dates = set(totals_by_day.keys())
    streak = calculate_streak(logged_dates, target_day)

    habit_frequency = await HabitRepository.list_habit_frequency(
        session,
        user.id,
        window_start,
        target_day,
    )
    today_habits = {entry.habit_name for entry in logs_today}
    low_days = detect_low_productivity_days(dict(totals_by_day))
    skipped = detect_skipped_habits(habit_frequency, today_habits)

    total_today = round(sum(float(entry.value) for entry in logs_today), 2)
    unique_habits_today = len(today_habits)
    score = productivity_score(total_today, unique_habits_today, streak, goal_daily_target)
    active_hour = await HabitRepository.detect_most_active_hour(session, user.id, lookback_days=30)

    return DailySummary(
        date=target_day,
        total_value=total_today,
        habits_logged=len(logs_today),
        streak=streak,
        productivity_score=score,
        low_productivity_days=low_days,
        skipped_habits=skipped,
        suggestions=build_suggestions(low_days, skipped, streak, active_hour),
    )


async def build_weekly_points(
    session: AsyncSession,
    user_id: int,
    target_day: date,
) -> list[dict[str, float | str]]:
    week_start = target_day - timedelta(days=6)
    logs = await HabitRepository.list_user_logs_between(session, user_id, week_start, target_day)
    totals: dict[date, float] = defaultdict(float)
    habit_counts: dict[date, int] = defaultdict(int)
    for entry in logs:
        totals[entry.log_date] += float(entry.value)
        habit_counts[entry.log_date] += 1

    points: list[dict[str, float | str]] = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        points.append(
            {
                "date": day.isoformat(),
                "value": round(totals.get(day, 0.0), 2),
                "habits": float(habit_counts.get(day, 0)),
            }
        )
    return points
