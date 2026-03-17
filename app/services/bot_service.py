from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.repositories.bot_repository import BotRepository
from app.utils.crypto import encrypt_secret


class BotService:
    """Service layer for owner-scoped bot management workflows."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.bots = BotRepository(session)

    async def list_my_bots(self, owner_id: int) -> list[dict]:
        """Return bots owned by the authenticated user."""

        try:
            rows = await self.bots.list_by_owner(owner_id=owner_id)
        except SQLAlchemyError as exc:
            raise ApplicationError(
                message="Failed to fetch bots",
                code="bots_list_failed",
                status_code=500,
            ) from exc
        return [
            {
                "id": row.id,
                "name": row.name,
                "owner_id": row.owner_id,
                "created_at": row.created_at,
                "is_active": row.is_active,
            }
            for row in rows
        ]

    async def create_bot(self, owner_id: int, name: str, token: str, is_active: bool) -> dict:
        """Create bot for owner, encrypting token before persistence."""

        if not token.strip():
            raise ApplicationError(
                message="Bot token cannot be empty",
                code="invalid_bot_token",
                status_code=400,
            )
        try:
            owner_exists = await self.bots.owner_exists(owner_id=owner_id)
            if not owner_exists:
                raise ApplicationError(
                    message="Owner user not found",
                    code="owner_not_found",
                    status_code=404,
                )

            encrypted = encrypt_secret(token.strip())
            bot = await self.bots.create_for_owner(
                owner_id=owner_id,
                name=name,
                token=encrypted,
                is_active=is_active,
            )
            await self.session.commit()
        except ApplicationError:
            await self.session.rollback()
            raise
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise ApplicationError(
                message="Failed to create bot",
                code="bot_create_failed",
                status_code=500,
            ) from exc
        except Exception as exc:
            await self.session.rollback()
            raise ApplicationError(
                message="Failed to encrypt bot token",
                code="bot_token_encryption_failed",
                status_code=500,
            ) from exc

        return {
            "id": bot.id,
            "name": bot.name,
            "owner_id": bot.owner_id,
            "created_at": bot.created_at,
            "is_active": bot.is_active,
        }

    async def delete_bot(self, owner_id: int, bot_id: int) -> None:
        """Delete bot if and only if it belongs to current owner."""

        try:
            deleted = await self.bots.soft_delete_for_owner(bot_id=bot_id, owner_id=owner_id)
            if not deleted:
                raise ApplicationError(
                    message="Bot not found for owner",
                    code="bot_not_found",
                    status_code=404,
                )
            await self.session.commit()
        except ApplicationError:
            await self.session.rollback()
            raise
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise ApplicationError(
                message="Failed to delete bot",
                code="bot_delete_failed",
                status_code=500,
            ) from exc
