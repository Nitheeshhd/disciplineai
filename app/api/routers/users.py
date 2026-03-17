from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.repositories import HabitRepository, UserRepository
from app.db.session import get_session
from app.schemas.analytics import DailySummaryResponse, WeeklyPoint
from app.services.analytics import build_daily_summary, build_weekly_points
from app.utils.time import now_in_timezone

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{telegram_user_id}/summary", response_model=DailySummaryResponse)
async def user_summary(
    telegram_user_id: int,
    session: AsyncSession = Depends(get_session),
) -> DailySummaryResponse:
    settings = get_settings()
    local_now = now_in_timezone(settings.timezone)
    user = await UserRepository.get_by_telegram_id(session, telegram_user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    summary = await build_daily_summary(
        session=session,
        user=user,
        target_day=local_now.date(),
        goal_daily_target=settings.goal_daily_target,
    )
    return DailySummaryResponse(
        date=summary.date.isoformat(),
        total_value=summary.total_value,
        habits_logged=summary.habits_logged,
        streak=summary.streak,
        productivity_score=summary.productivity_score,
        low_productivity_days=[day.isoformat() for day in summary.low_productivity_days],
        skipped_habits=summary.skipped_habits,
        suggestions=summary.suggestions,
    )


@router.get("/{telegram_user_id}/weekly", response_model=list[WeeklyPoint])
async def user_weekly(
    telegram_user_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[WeeklyPoint]:
    settings = get_settings()
    local_now = now_in_timezone(settings.timezone)
    user = await UserRepository.get_by_telegram_id(session, telegram_user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    points = await build_weekly_points(session=session, user_id=user.id, target_day=local_now.date())
    return [WeeklyPoint(**item) for item in points]


@router.get("/leaderboard/global")
async def global_leaderboard(session: AsyncSession = Depends(get_session)) -> dict:
    settings = get_settings()
    local_now = now_in_timezone(settings.timezone)
    week_start = local_now.date() - timedelta(days=6)
    rows = await HabitRepository.list_leaderboard(session, from_day=week_start, limit=15)
    return {"week_start": week_start.isoformat(), "week_end": local_now.date().isoformat(), "rows": rows}
