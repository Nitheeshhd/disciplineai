from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import UserProfile
from app.db.repositories import HabitRepository, UserRepository
from app.db.session import get_session
from app.schemas.habits import HabitLogCreate, HabitLogResponse
from app.utils.time import now_in_timezone

router = APIRouter(prefix="/habits", tags=["habits"])


@router.post("/log", response_model=HabitLogResponse)
async def create_habit_log(
    payload: HabitLogCreate,
    session: AsyncSession = Depends(get_session),
) -> HabitLogResponse:
    settings = get_settings()
    local_now = now_in_timezone(settings.timezone)

    user = await UserRepository.get_by_telegram_id(session, payload.telegram_user_id)
    if user is None:
        user = UserProfile(
            telegram_user_id=payload.telegram_user_id,
            timezone=settings.timezone,
            first_name="API User",
        )
        session.add(user)
        await session.flush()

    entry = await HabitRepository.add_log(
        session=session,
        user_id=user.id,
        habit_name=payload.habit_name,
        value=payload.value,
        log_date=local_now.date(),
        logged_hour=local_now.hour,
        notes=payload.notes,
    )
    await session.commit()

    return HabitLogResponse(
        id=entry.id,
        user_id=entry.user_id,
        habit_name=entry.habit_name,
        value=float(entry.value),
        log_date=entry.log_date.isoformat(),
        logged_hour=entry.logged_hour,
    )
