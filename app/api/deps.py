from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_write_session
from app.core.exceptions import ApplicationError
from app.services.auth_service import AuthService

security = HTTPBearer(auto_error=False)


def get_app_settings() -> Settings:
    return get_settings()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_write_session),
    settings: Settings = Depends(get_app_settings),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    service = AuthService(session=session, settings=settings)
    try:
        user = await service.get_user_from_access_token(credentials.credentials)
    except ApplicationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return user


def require_roles(*required_roles: str):
    async def dependency(user: dict = Depends(get_current_user)) -> dict:
        user_roles = set(user.get("roles", []))
        if not user_roles.intersection(required_roles):
            raise HTTPException(status_code=403, detail="Insufficient role permissions")
        return user

    return dependency
