from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import ApplicationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.utils.crypto import sha256_hexdigest
from app.utils.datetime import utc_now


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings
        self.users = UserRepository(session)

    async def bootstrap_roles(self) -> None:
        admin = await self.users.ensure_role("admin", "Platform administrator")
        await self.users.ensure_role("analyst", "Analytics read access")
        await self.users.ensure_role("user", "Standard user")
        await self.session.commit()

    async def register_user(
        self,
        email: str,
        password: str,
        telegram_user_id: int,
        first_name: str | None,
        last_name: str | None,
    ) -> dict:
        existing = await self.users.get_by_email(email)
        if existing:
            raise ApplicationError("Email already registered", code="email_exists", status_code=409)

        hashed_password = hash_password(password)
        user = await self.users.create_user(
            email=email,
            hashed_password=hashed_password,
            telegram_user_id=telegram_user_id,
            first_name=first_name,
            last_name=last_name,
        )
        user_role = await self.users.ensure_role("user", "Standard user")
        await self.users.assign_role(user.id, user_role.id)
        await self.session.commit()

        return await self._issue_tokens(
            user_id=user.id,
            email=user.email,
            role_names=["user"],
            ip_address=None,
            user_agent=None,
        )

    async def login_user(self, email: str, password: str, ip_address: str | None, user_agent: str | None) -> dict:
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise ApplicationError("Invalid email or password", code="invalid_credentials", status_code=401)
        if not user.is_active:
            raise ApplicationError("User account inactive", code="inactive_user", status_code=403)

        role_names = [role.name for role in user.roles if not role.is_deleted]
        tokens = await self._issue_tokens(
            user_id=user.id,
            email=user.email,
            role_names=role_names,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.session.commit()
        return tokens

    async def refresh_tokens(self, refresh_token: str, ip_address: str | None, user_agent: str | None) -> dict:
        try:
            payload = decode_refresh_token(refresh_token, self.settings)
        except Exception as exc:  # pragma: no cover
            raise ApplicationError("Invalid refresh token", code="invalid_refresh_token", status_code=401) from exc

        if payload.get("type") != "refresh":
            raise ApplicationError("Invalid refresh token type", code="invalid_refresh_token", status_code=401)

        jti = payload.get("jti")
        sub = payload.get("sub")
        if not jti or not sub:
            raise ApplicationError("Refresh token missing claims", code="invalid_refresh_token", status_code=401)

        session_entry = await self.users.get_session_by_jti(jti)
        if session_entry is None:
            raise ApplicationError("Refresh session expired", code="session_not_found", status_code=401)

        refresh_hash = sha256_hexdigest(refresh_token)
        if session_entry.refresh_token_hash != refresh_hash:
            raise ApplicationError("Refresh session mismatch", code="session_mismatch", status_code=401)

        if session_entry.expires_at <= utc_now():
            raise ApplicationError("Refresh token expired", code="session_expired", status_code=401)

        user = await self.users.get_with_roles(session_entry.user_id)
        if user is None:
            raise ApplicationError("User not found", code="user_not_found", status_code=404)

        session_entry.revoked_at = utc_now()
        role_names = [role.name for role in user.roles if not role.is_deleted]
        tokens = await self._issue_tokens(
            user_id=user.id,
            email=user.email,
            role_names=role_names,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.session.commit()
        return tokens

    async def get_user_from_access_token(self, access_token: str) -> dict:
        try:
            payload = decode_access_token(access_token, self.settings)
        except Exception as exc:  # pragma: no cover
            raise ApplicationError("Invalid access token", code="invalid_access_token", status_code=401) from exc

        user_id = payload.get("uid")
        if user_id is None:
            raise ApplicationError("Invalid token claims", code="invalid_access_token", status_code=401)

        user = await self.users.get_with_roles(int(user_id))
        if user is None or user.is_deleted:
            raise ApplicationError("User not found", code="user_not_found", status_code=404)
        return {
            "id": user.id,
            "email": user.email,
            "telegram_user_id": user.telegram_user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "roles": [role.name for role in user.roles if not role.is_deleted],
            "is_premium": user.is_premium,
            "created_at": user.created_at,
        }

    async def _issue_tokens(
        self,
        user_id: int,
        email: str,
        role_names: list[str],
        ip_address: str | None,
        user_agent: str | None,
    ) -> dict:
        claims = {"uid": user_id, "email": email, "roles": role_names}
        access_token = create_access_token(subject=email, settings=self.settings, additional_claims=claims)
        refresh_token = create_refresh_token(subject=email, settings=self.settings, additional_claims=claims)
        refresh_payload = decode_refresh_token(refresh_token, self.settings)
        refresh_jti = refresh_payload["jti"]

        expires_at = utc_now() + timedelta(days=self.settings.jwt_refresh_token_expire_days)
        await self.users.create_session(
            user_id=user_id,
            refresh_token_jti=refresh_jti,
            refresh_token_hash=sha256_hexdigest(refresh_token),
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.settings.jwt_access_token_expire_minutes * 60,
        }
