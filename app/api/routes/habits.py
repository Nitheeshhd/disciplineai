from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.cqrs import LogHabitCommand
from app.api.deps import get_current_user
from app.core.database import get_write_session
from app.schemas.habit import HabitLogCreate, HabitLogResponse
from app.services.habit_service import HabitService

router = APIRouter(prefix="/habits", tags=["habits"])


@router.post("/log", response_model=HabitLogResponse)
async def log_habit(
    payload: HabitLogCreate,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_write_session),
) -> HabitLogResponse:
    service = HabitService(session=session)
    command = LogHabitCommand(
        user_id=user["id"],
        habit_name=payload.habit_name,
        value=payload.value,
        unit=payload.unit,
        notes=payload.notes,
    )
    entry = await service.log_habit(command)
    return HabitLogResponse(**entry)
