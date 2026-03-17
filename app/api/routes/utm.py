from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_read_session, get_write_session
from app.schemas.utm import CampaignGenerateRequest, CampaignListResponse, CampaignResponse
from app.services.utm_service import UtmService

router = APIRouter(prefix="/utm", tags=["utm"])


@router.post("/generate", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def generate_utm_campaign(
    payload: CampaignGenerateRequest,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_write_session),
) -> CampaignResponse:
    """Generate and persist a UTM campaign URL for the current user."""

    service = UtmService(session=session)
    result = await service.generate_campaign(
        user_id=user["id"],
        base_url=str(payload.base_url),
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
    )
    return CampaignResponse(**result)


@router.get("", response_model=CampaignListResponse)
async def list_utm_campaigns(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_read_session),
) -> CampaignListResponse:
    """List all UTM campaigns created by the current user."""

    service = UtmService(session=session)
    items = await service.list_campaigns(user_id=user["id"])
    return CampaignListResponse(items=[CampaignResponse(**item) for item in items])


@router.post("/{campaign_id}/click", response_model=CampaignResponse, status_code=status.HTTP_200_OK)
async def track_utm_click(
    campaign_id: int,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_write_session),
) -> CampaignResponse:
    """Increment click counter for an owner-scoped campaign."""

    service = UtmService(session=session)
    payload = await service.track_click(user_id=user["id"], campaign_id=campaign_id)
    return CampaignResponse(**payload)

