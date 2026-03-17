from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogHabitCommand:
    user_id: int
    habit_name: str
    value: float
    unit: str
    notes: str | None


@dataclass(frozen=True, slots=True)
class DashboardSummaryQuery:
    pass
