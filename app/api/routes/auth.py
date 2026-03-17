from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_current_user
from app.core.config import Settings
from app.core.database import get_write_session
from app.core.exceptions import ApplicationError
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserMeResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_write_session),
    settings: Settings = Depends(get_app_settings),
) -> TokenPair:
    service = AuthService(session=session, settings=settings)
    try:
        tokens = await service.register_user(
            email=payload.email,
            password=payload.password,
            telegram_user_id=payload.telegram_user_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        return TokenPair(**tokens)
    except ApplicationError:
        await session.rollback()
        raise


@router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_write_session),
    settings: Settings = Depends(get_app_settings),
) -> TokenPair:
    service = AuthService(session=session, settings=settings)
    tokens = await service.login_user(
        email=payload.email,
        password=payload.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return TokenPair(**tokens)


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(
    payload: RefreshRequest,
    request: Request,
    session: AsyncSession = Depends(get_write_session),
    settings: Settings = Depends(get_app_settings),
) -> TokenPair:
    service = AuthService(session=session, settings=settings)
    tokens = await service.refresh_tokens(
        refresh_token=payload.refresh_token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return TokenPair(**tokens)


@router.get("/me", response_model=UserMeResponse)
async def me(user: dict = Depends(get_current_user)) -> UserMeResponse:
    return UserMeResponse(**user)
