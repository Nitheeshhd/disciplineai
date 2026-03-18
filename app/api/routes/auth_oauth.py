from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from app.auth.oauth import oauth
from app.core.database import get_write_session
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/login")
async def login(request: Request):
    redirect_uri = "https://disciplineai.onrender.com/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/callback")
async def auth_callback(request: Request, db: AsyncSession = Depends(get_write_session)):
    try:
        token = await oauth.google.authorize_access_token(request)

        resp = await oauth.google.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            token=token
        )
        user_info = resp.json()

        if not user_info:
            return RedirectResponse(url="/?error=oauth_failed")

        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')

        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email=email,
                full_name=name,
                name=name,
                picture=picture,
                is_active=True,
                is_verified=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            user.full_name = name
            user.name = name
            user.picture = picture
            await db.commit()

        request.session["user"] = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture
        }

        return RedirectResponse(url="/dashboard", status_code=302)

    except Exception as e:
        logger.exception("Auth callback failed: %s", e)
        return RedirectResponse(url=f"/?error={str(e)}", status_code=302)

@router.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url="/")
