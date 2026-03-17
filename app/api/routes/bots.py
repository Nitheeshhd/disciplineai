from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_write_session
from app.schemas.common import MessageResponse
from app.schemas.bots import BotCreateRequest, BotResponse, BotsListResponse
from app.services.bot_service import BotService

router = APIRouter(prefix="/bots", tags=["bots"])


@router.get("", response_model=BotsListResponse)
async def list_my_bots(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_write_session),
) -> BotsListResponse:
    """List bots owned by the authenticated user."""

    service = BotService(session=session)
    items = await service.list_my_bots(owner_id=user["id"])
    return BotsListResponse(items=[BotResponse(**item) for item in items])


@router.post("", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    payload: BotCreateRequest,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_write_session),
) -> BotResponse:
    """Create a new bot with token encrypted before storing."""

    service = BotService(session=session)
    bot = await service.create_bot(
        owner_id=user["id"],
        name=payload.name,
        token=payload.token,
        is_active=payload.is_active,
    )
    return BotResponse(**bot)


@router.delete("/{bot_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def delete_bot(
    bot_id: int,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_write_session),
) -> MessageResponse:
    """Delete bot only if it belongs to the authenticated owner."""

    service = BotService(session=session)
    await service.delete_bot(owner_id=user["id"], bot_id=bot_id)
    return MessageResponse(message="Bot deleted successfully")
