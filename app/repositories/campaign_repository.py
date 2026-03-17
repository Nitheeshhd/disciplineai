from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.repositories.base import BaseRepository


class CampaignRepository(BaseRepository[Campaign]):
    """Repository for user-owned UTM campaign persistence operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Campaign)

    async def create_campaign(
        self,
        user_id: int,
        base_url: str,
        utm_source: str,
        utm_medium: str,
        utm_campaign: str,
        full_url: str,
    ) -> Campaign:
        """Create and flush a campaign row."""

        row = Campaign(
            user_id=user_id,
            base_url=base_url,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            full_url=full_url,
            clicks=0,
        )
        await self.add(row)
        return row

    async def list_by_user(self, user_id: int) -> list[Campaign]:
        """Return campaigns for a user ordered by newest first."""

        stmt = select(Campaign).where(Campaign.user_id == user_id).order_by(Campaign.created_at.desc())
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())

    async def get_by_id_for_user(self, campaign_id: int, user_id: int) -> Campaign | None:
        """Get one campaign by id in owner scope."""

        stmt = select(Campaign).where(and_(Campaign.id == campaign_id, Campaign.user_id == user_id))
        row = await self.session.execute(stmt)
        return row.scalar_one_or_none()

    async def increment_click_for_user(self, campaign_id: int, user_id: int) -> Campaign | None:
        """Increment click count for an owner-scoped campaign."""

        row = await self.get_by_id_for_user(campaign_id=campaign_id, user_id=user_id)
        if row is None:
            return None
        row.clicks += 1
        await self.session.flush()
        return row

