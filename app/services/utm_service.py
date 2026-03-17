from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.repositories.campaign_repository import CampaignRepository


class UtmService:
    """Service layer for UTM campaign generation and click tracking."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.campaigns = CampaignRepository(session)

    async def generate_campaign(
        self,
        user_id: int,
        base_url: str,
        utm_source: str,
        utm_medium: str,
        utm_campaign: str,
    ) -> dict:
        """Create a new campaign and return the generated tracking URL."""

        normalized_url = self._normalize_and_validate_url(base_url)
        generated_url = self._build_utm_url(
            base_url=normalized_url,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
        )

        try:
            row = await self.campaigns.create_campaign(
                user_id=user_id,
                base_url=normalized_url,
                utm_source=utm_source.strip(),
                utm_medium=utm_medium.strip(),
                utm_campaign=utm_campaign.strip(),
                full_url=generated_url,
            )
            await self.session.commit()
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise ApplicationError(
                message="Failed to create UTM campaign",
                code="utm_generate_failed",
                status_code=500,
            ) from exc

        return self._to_payload(row)

    async def list_campaigns(self, user_id: int) -> list[dict]:
        """List all campaigns for the authenticated owner."""

        try:
            rows = await self.campaigns.list_by_user(user_id=user_id)
        except SQLAlchemyError as exc:
            raise ApplicationError(
                message="Failed to fetch UTM campaigns",
                code="utm_list_failed",
                status_code=500,
            ) from exc
        return [self._to_payload(row) for row in rows]

    async def track_click(self, user_id: int, campaign_id: int) -> dict:
        """Increment campaign click count in owner scope."""

        try:
            row = await self.campaigns.increment_click_for_user(campaign_id=campaign_id, user_id=user_id)
            if row is None:
                raise ApplicationError(
                    message="Campaign not found for owner",
                    code="campaign_not_found",
                    status_code=404,
                )
            await self.session.commit()
        except ApplicationError:
            await self.session.rollback()
            raise
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise ApplicationError(
                message="Failed to track campaign click",
                code="utm_click_track_failed",
                status_code=500,
            ) from exc

        return self._to_payload(row)

    def _normalize_and_validate_url(self, raw_url: str) -> str:
        """Ensure URL is absolute and uses HTTP/HTTPS."""

        value = raw_url.strip()
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ApplicationError(
                message="Invalid URL. Use absolute http/https URL",
                code="invalid_base_url",
                status_code=422,
            )
        return value

    def _build_utm_url(
        self,
        base_url: str,
        utm_source: str,
        utm_medium: str,
        utm_campaign: str,
    ) -> str:
        """Build full URL by merging existing query params with UTM params."""

        parsed = urlparse(base_url)
        existing = dict(parse_qsl(parsed.query, keep_blank_values=True))
        existing["utm_source"] = utm_source.strip()
        existing["utm_medium"] = utm_medium.strip()
        existing["utm_campaign"] = utm_campaign.strip()
        query = urlencode(existing, doseq=True)
        return urlunparse(parsed._replace(query=query))

    def _to_payload(self, row) -> dict:
        return {
            "id": row.id,
            "user_id": row.user_id,
            "base_url": row.base_url,
            "utm_source": row.utm_source,
            "utm_medium": row.utm_medium,
            "utm_campaign": row.utm_campaign,
            "full_url": row.full_url,
            "clicks": row.clicks,
            "created_at": row.created_at,
        }

