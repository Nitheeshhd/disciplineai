from __future__ import annotations

import json

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_log import ErrorLog


class ErrorLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int | None,
        command: str,
        trace_id: str,
        path: str,
        method: str,
        status_code: int,
        error_type: str,
        error_message: str,
        stack_trace: str | None = None,
        metadata: dict | None = None,
    ) -> ErrorLog:
        entry = ErrorLog(
            user_id=user_id,
            command=command,
            trace_id=trace_id,
            path=path,
            method=method,
            status_code=status_code,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=True),
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_all(self) -> list[ErrorLog]:
        stmt = select(ErrorLog).order_by(desc(ErrorLog.created_at))
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())

    async def list_recent(self, limit: int = 20) -> list[ErrorLog]:
        stmt = select(ErrorLog).order_by(desc(ErrorLog.created_at)).limit(limit)
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())
