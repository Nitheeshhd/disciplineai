from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_write_session
from app.schemas.conversions import ConversionItem, ConversionListResponse, ConversionTrackingRateResponse
from app.services.conversion_service import ConversionService

router = APIRouter(tags=["conversions"])


@router.get("/conversions", response_model=ConversionListResponse)
async def list_conversions(
    _: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_write_session),
) -> ConversionListResponse:
    """List conversion events derived from 7-day habit logging streaks."""

    service = ConversionService(session=session)
    rows = await service.get_conversions()
    return ConversionListResponse(items=[ConversionItem(**row) for row in rows])


@router.get("/conversion-rate", response_model=ConversionTrackingRateResponse)
async def conversion_rate(
    _: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_write_session),
) -> ConversionTrackingRateResponse:
    """Return conversion rate percentage across active users."""

    service = ConversionService(session=session)
    payload = await service.get_conversion_rate()
    return ConversionTrackingRateResponse(**payload)
