from pydantic import BaseModel, Field


class HabitLogCreate(BaseModel):
    telegram_user_id: int
    habit_name: str = Field(min_length=1, max_length=80)
    value: float = Field(ge=0)
    notes: str | None = Field(default=None, max_length=500)


class HabitLogResponse(BaseModel):
    id: int
    user_id: int
    habit_name: str
    value: float
    log_date: str
    logged_hour: int
