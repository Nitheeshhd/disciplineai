from datetime import date
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings
from app.core.config import Settings
from app.core.database import get_read_session
from app.schemas.dashboard import DashboardDataResponse, DashboardSummary
from app.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

async def get_dashboard_service(
    session: AsyncSession = Depends(get_read_session),
    settings: Settings = Depends(get_app_settings),
) -> DashboardService:
    return DashboardService(session=session, settings=settings)

@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummary:
    """Return high-level dashboard KPIs for today's activity and revenue."""
    result = await service.get_summary(today=date.today())
    return DashboardSummary(**result)

@router.get("/data", response_model=DashboardDataResponse)
async def dashboard_data(
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardDataResponse:
    try:
        return await service.dashboard_data()
    except Exception as e:
        logger.error(f"Dashboard data API failed: {e}")
        raise
