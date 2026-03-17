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
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, str(redirect_uri))

@router.get("/callback")
async def auth_callback(request: Request, db: AsyncSession = Depends(get_write_session)):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        if not user_info:
            return RedirectResponse(url="/?error=oauth_failed")
        
        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')

        # Check if user exists
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # Create new user
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
            # Update user info if changed
            user.full_name = name
            user.name = name
            user.picture = picture
            await db.commit()

        # Persist the signed-in user in the session cookie.
        session_user = {
            'id': user.id,
            'email': user.email,
            'name': user.name or user.full_name,
            'picture': user.picture
        }
        request.session["user"] = session_user
        print("SESSION SET:", request.session)
        
        return RedirectResponse(
            url="/dashboard",
            status_code=302
        )
    except Exception as e:
        logger.error(f"Auth callback failed: {str(e)}")
        return RedirectResponse(url="/?error=auth_error")

@router.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url="/")
