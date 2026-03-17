from pydantic import BaseModel


class ProductivityMetricsResponse(BaseModel):
    streak_days: int
    moving_average: float
    anomaly_detected: bool
    behavioral_score: float


class AnalyticsTrendResponse(BaseModel):
    labels: list[str]
    values: list[float]
