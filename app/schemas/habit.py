from pydantic import BaseModel, Field


class HabitLogCreate(BaseModel):
    habit_name: str = Field(min_length=1, max_length=80)
    value: float = Field(ge=0)
    unit: str = Field(default="count", max_length=20)
    notes: str | None = Field(default=None, max_length=1000)


class HabitLogResponse(BaseModel):
    id: int
    user_id: int
    habit_name: str
    value: float
    unit: str
    log_date: str
    logged_hour: int
