from pydantic import BaseModel


class DashboardSummary(BaseModel):
    sessions_today: int
    total_users: int
    messages_today: int
    revenue_today: float


class DemographicBreakdown(BaseModel):
    labels: list[str]
    values: list[int]


class TrendPoint(BaseModel):
    date: str
    value: float


class ProductivityTrendResponse(BaseModel):
    points: list[TrendPoint]


class RevenueTrendResponse(BaseModel):
    points: list[TrendPoint]


class ConversionRateResponse(BaseModel):
    rate: float


class DashboardPanelRow(BaseModel):
    date: str
    user: str
    conversion: str
    value: str


class PopularHabitRow(BaseModel):
    team: str
    number: int
    unique: int
    per_user: float
    sessions: float


class DashboardDataResponse(BaseModel):
    summary: DashboardSummary
    productivity_trend: list[TrendPoint]
    gender_breakdown: DemographicBreakdown
    premium_breakdown: DemographicBreakdown
    recent_goal_achievements: list[DashboardPanelRow]
    popular_teams: list[PopularHabitRow]


class LiveStatsResponse(BaseModel):
    focus_time_today: int
    tasks_completed: int
    habits_completed: int
    current_streak: int
