from __future__ import annotations

from datetime import date

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_status import DailyTaskStatus
from app.repositories.base import BaseRepository


class TaskStatusRepository(BaseRepository[DailyTaskStatus]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DailyTaskStatus)

    async def list_for_date(self, user_id: int, target_day: date) -> list[DailyTaskStatus]:
        stmt = (
            select(DailyTaskStatus)
            .where(
                and_(
                    DailyTaskStatus.user_id == user_id,
                    DailyTaskStatus.task_date == target_day,
                )
            )
            .order_by(DailyTaskStatus.task_name.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def ensure_tasks_for_date(
        self,
        user_id: int,
        target_day: date,
        task_names: list[str],
    ) -> list[DailyTaskStatus]:
        existing = await self.list_for_date(user_id=user_id, target_day=target_day)
        by_key = {row.task_name.strip().lower(): row for row in existing}

        for raw_name in task_names:
            task_name = raw_name.strip()
            key = task_name.lower()
            if not task_name or key in by_key:
                continue
            row = DailyTaskStatus(
                user_id=user_id,
                task_name=task_name,
                task_date=target_day,
                status=False,
            )
            self.session.add(row)
            by_key[key] = row

        await self.session.flush()
        return list(by_key.values())

    async def set_status(
        self,
        user_id: int,
        task_name: str,
        target_day: date,
        status: bool,
    ) -> DailyTaskStatus:
        stmt = (
            select(DailyTaskStatus)
            .where(
                and_(
                    DailyTaskStatus.user_id == user_id,
                    DailyTaskStatus.task_date == target_day,
                    func.lower(DailyTaskStatus.task_name) == task_name.strip().lower(),
                )
            )
            .limit(1)
        )
        row = (await self.session.execute(stmt)).scalar_one_or_none()
        if row is None:
            row = DailyTaskStatus(
                user_id=user_id,
                task_name=task_name.strip(),
                task_date=target_day,
                status=bool(status),
            )
            self.session.add(row)
        else:
            row.status = bool(status)

        await self.session.flush()
        return row

    async def daily_completion_counts(
        self,
        user_id: int,
        start_day: date,
        end_day: date,
    ) -> dict[date, dict[str, int]]:
        completed_expr = case((DailyTaskStatus.status.is_(True), 1), else_=0)
        stmt = (
            select(
                DailyTaskStatus.task_date,
                func.count(DailyTaskStatus.id).label("total_tasks"),
                func.sum(completed_expr).label("completed_tasks"),
            )
            .where(
                and_(
                    DailyTaskStatus.user_id == user_id,
                    DailyTaskStatus.task_date >= start_day,
                    DailyTaskStatus.task_date <= end_day,
                )
            )
            .group_by(DailyTaskStatus.task_date)
            .order_by(DailyTaskStatus.task_date.asc())
        )
        rows = (await self.session.execute(stmt)).all()

        payload: dict[date, dict[str, int]] = {}
        for task_date, total_tasks, completed_tasks in rows:
            payload[task_date] = {
                "total_tasks": int(total_tasks or 0),
                "completed_tasks": int(completed_tasks or 0),
            }
        return payload
