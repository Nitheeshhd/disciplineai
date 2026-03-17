from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_read_session
from app.schemas.reports import ReportItem, ReportListResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=ReportListResponse)
async def list_reports(
    _: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_read_session),
) -> ReportListResponse:
    """Return persisted weekly analytics reports."""

    service = ReportService(session=session)
    rows = await service.list_reports(limit=104)
    return ReportListResponse(items=[ReportItem(**row) for row in rows])

