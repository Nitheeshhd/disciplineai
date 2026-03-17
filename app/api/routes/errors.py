from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_read_session
from app.schemas.errors import ErrorLogItem, ErrorLogListResponse
from app.services.error_log_service import ErrorLogService

router = APIRouter(prefix="/errors", tags=["errors"])


@router.get("", response_model=ErrorLogListResponse)
async def list_errors(
    session: AsyncSession = Depends(get_read_session),
    _: dict = Depends(require_roles("admin", "analyst")),
) -> ErrorLogListResponse:
    """Return all stored bot error logs."""

    service = ErrorLogService(session=session)
    items = await service.list_errors()
    return ErrorLogListResponse(items=[ErrorLogItem(**item) for item in items])


@router.get("/recent", response_model=ErrorLogListResponse)
async def list_recent_errors(
    session: AsyncSession = Depends(get_read_session),
    _: dict = Depends(require_roles("admin", "analyst")),
) -> ErrorLogListResponse:
    """Return recent bot error logs."""

    service = ErrorLogService(session=session)
    items = await service.list_recent_errors(limit=20)
    return ErrorLogListResponse(items=[ErrorLogItem(**item) for item in items])

