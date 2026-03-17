from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.repositories.error_log_repository import ErrorLogRepository


class ErrorLogService:
    """Service for querying persisted bot error logs."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ErrorLogRepository(session)

    async def list_errors(self) -> list[dict]:
        """Return all error logs ordered by latest first."""

        try:
            rows = await self.repo.list_all()
        except SQLAlchemyError as exc:
            raise ApplicationError(
                message="Failed to fetch error logs",
                code="error_logs_fetch_failed",
                status_code=500,
            ) from exc
        return [self._serialize(row) for row in rows]

    async def list_recent_errors(self, limit: int = 20) -> list[dict]:
        """Return most recent error logs."""

        try:
            rows = await self.repo.list_recent(limit=limit)
        except SQLAlchemyError as exc:
            raise ApplicationError(
                message="Failed to fetch recent error logs",
                code="recent_error_logs_fetch_failed",
                status_code=500,
            ) from exc
        return [self._serialize(row) for row in rows]

    def _serialize(self, row) -> dict:
        return {
            "id": row.id,
            "user_id": row.user_id,
            "command": row.command,
            "error_message": row.error_message,
            "stack_trace": row.stack_trace,
            "created_at": row.created_at,
        }

