from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_read_session
from app.schemas.analytics import AnalyticsTrendResponse, ProductivityMetricsResponse
from app.schemas.dashboard import ConversionRateResponse, DemographicBreakdown, RevenueTrendResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/productivity-trend", response_model=AnalyticsTrendResponse)
async def productivity_trend(
    days: int = Query(default=30, ge=7, le=90),
    session: AsyncSession = Depends(get_read_session),
    _: dict = Depends(require_roles("admin", "analyst")),
) -> AnalyticsTrendResponse:
    service = AnalyticsService(session=session)
    trend = await service.productivity_trend(days=days)
    return AnalyticsTrendResponse(**trend)


@router.get("/demographics", response_model=DemographicBreakdown)
async def demographics(
    session: AsyncSession = Depends(get_read_session),
    _: dict = Depends(require_roles("admin", "analyst")),
) -> DemographicBreakdown:
    service = AnalyticsService(session=session)
    data = await service.demographic_breakdown()
    return DemographicBreakdown(**data)


@router.get("/conversion-rate", response_model=ConversionRateResponse)
async def conversion_rate(
    days: int = Query(default=30, ge=7, le=90),
    session: AsyncSession = Depends(get_read_session),
    _: dict = Depends(require_roles("admin", "analyst")),
) -> ConversionRateResponse:
    service = AnalyticsService(session=session)
    data = await service.conversion_rate(days=days)
    return ConversionRateResponse(**data)


@router.get("/revenue-trend", response_model=RevenueTrendResponse)
async def revenue_trend(
    days: int = Query(default=30, ge=7, le=90),
    session: AsyncSession = Depends(get_read_session),
    _: dict = Depends(require_roles("admin", "analyst")),
) -> RevenueTrendResponse:
    service = AnalyticsService(session=session)
    data = await service.revenue_trend(days=days)
    return RevenueTrendResponse(**data)


@router.get("/productivity-metrics", response_model=ProductivityMetricsResponse)
async def my_productivity_metrics(
    session: AsyncSession = Depends(get_read_session),
    user: dict = Depends(get_current_user),
) -> ProductivityMetricsResponse:
    service = AnalyticsService(session=session)
    metrics = await service.productivity_metrics(user_id=user["id"])
    return ProductivityMetricsResponse(**metrics)
