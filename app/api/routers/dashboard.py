from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_session
from app.schemas.dashboard import DashboardPayload
from app.services.dashboard import build_dashboard_payload

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/data", response_model=DashboardPayload)
async def dashboard_data(session: AsyncSession = Depends(get_session)) -> DashboardPayload:
    settings = get_settings()
    payload = await build_dashboard_payload(session=session, timezone=settings.timezone)
    return DashboardPayload(**payload)


@router.get("/overview")
async def dashboard_overview(session: AsyncSession = Depends(get_session)) -> dict:
    settings = get_settings()
    payload = await build_dashboard_payload(session=session, timezone=settings.timezone)
    return payload["overview"]


@router.get("/trends")
async def dashboard_trends(session: AsyncSession = Depends(get_session)) -> dict:
    settings = get_settings()
    payload = await build_dashboard_payload(session=session, timezone=settings.timezone)
    return payload["trends"]
