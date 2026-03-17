from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bot import Bot
from app.models.user import User
from app.repositories.base import BaseRepository
from app.utils.datetime import utc_now


class BotRepository(BaseRepository[Bot]):
    """Repository for owner-scoped bot persistence operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Bot)

    async def owner_exists(self, owner_id: int) -> bool:
        """Return True if an active non-deleted owner user exists."""

        stmt = select(User.id).where(and_(User.id == owner_id, User.is_deleted.is_(False)))
        row = (await self.session.execute(stmt)).first()
        return row is not None

    async def list_by_owner(self, owner_id: int) -> list[Bot]:
        """List all active bot records for the owner."""

        stmt = (
            select(Bot)
            .where(and_(Bot.owner_id == owner_id, Bot.is_deleted.is_(False)))
            .order_by(Bot.created_at.desc())
        )
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())

    async def create_for_owner(
        self,
        owner_id: int,
        name: str,
        token: str,
        is_active: bool,
    ) -> Bot:
        """Persist a new encrypted bot credential row."""

        bot = Bot(
            owner_id=owner_id,
            name=name.strip(),
            token=token,
            is_active=is_active,
        )
        await self.add(bot)
        return bot

    async def get_by_id_for_owner(self, bot_id: int, owner_id: int) -> Bot | None:
        """Fetch bot by id, enforcing owner scope and soft-delete rules."""

        stmt = select(Bot).where(
            and_(
                Bot.id == bot_id,
                Bot.owner_id == owner_id,
                Bot.is_deleted.is_(False),
            )
        )
        row = await self.session.execute(stmt)
        return row.scalar_one_or_none()

    async def soft_delete_for_owner(self, bot_id: int, owner_id: int) -> bool:
        """Soft delete bot only if it belongs to owner."""

        bot = await self.get_by_id_for_owner(bot_id=bot_id, owner_id=owner_id)
        if bot is None:
            return False
        bot.is_deleted = True
        bot.deleted_at = utc_now()
        await self.session.flush()
        return True
