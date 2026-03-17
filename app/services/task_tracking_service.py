from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.badge_repository import BadgeRepository
from app.repositories.task_status_repository import TaskStatusRepository
from app.repositories.user_repository import UserRepository

DEFAULT_HABITS: tuple[str, ...] = (
    "Meditation",
    "Deep Work",
    "Reading",
    "Workout",
)

DEFAULT_TASKS: tuple[str, ...] = (
    *DEFAULT_HABITS,
    "Finalize client roadmap",
    "Write product update",
    "Review weekly analytics",
)

REMINDER_START_HOUR = 21
REMINDER_REPEAT_MINUTES = 30
REMINDER_MESSAGE = "Your task is still pending. Go crack it now!"
LEVEL_MILESTONES: tuple[tuple[str, int], ...] = (
    ("Achiever", 1),
    ("Consistent", 7),
    ("Warrior", 30),
    ("Elite", 67),
    ("Master", 120),
    ("Pro", 200),
)


class TaskTrackingService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TaskStatusRepository(session)
        self.user_repo = UserRepository(session)
        self.badge_repo = BadgeRepository(session)

    @staticmethod
    def _key(task_name: str) -> str:
        return task_name.strip().lower()

    def _task_catalog(self) -> list[dict[str, str | bool]]:
        habit_keys = {self._key(item) for item in DEFAULT_HABITS}
        return [
            {
                "task_name": task_name,
                "is_habit": self._key(task_name) in habit_keys,
            }
            for task_name in DEFAULT_TASKS
        ]

    def _resolve_task_name(self, task_name: str) -> str:
        normalized = self._key(task_name)
        for candidate in DEFAULT_TASKS:
            if self._key(candidate) == normalized:
                return candidate
        raise ValueError(f"Unknown task name: {task_name}")

    def _resolve_level_details(self, streak_days: int) -> tuple[dict[str, str | int], dict[str, str | int] | None]:
        current = {"name": LEVEL_MILESTONES[0][0], "requirement": LEVEL_MILESTONES[0][1]}
        if streak_days < int(LEVEL_MILESTONES[0][1]):
            if len(LEVEL_MILESTONES) > 1:
                return current, {
                    "name": LEVEL_MILESTONES[1][0],
                    "requirement": LEVEL_MILESTONES[1][1],
                }
            return current, None

        upcoming: dict[str, str | int] | None = None
        for level_name, requirement in LEVEL_MILESTONES:
            if streak_days >= requirement:
                current = {"name": level_name, "requirement": requirement}
                continue
            upcoming = {"name": level_name, "requirement": requirement}
            break
        return current, upcoming

    async def _refresh_profile_metrics(self, user_id: int, reference_day: date) -> dict:
        user = await self.user_repo.get_by_id(user_id)
        if user is None or user.is_deleted:
            raise ValueError("User not found")

        default_total = len(DEFAULT_TASKS)
        lookback_start = reference_day - timedelta(days=3650)
        historical_counts = await self.repo.daily_completion_counts(
            user_id=user_id,
            start_day=lookback_start,
            end_day=reference_day,
        )

        streak_days = 0
        for offset in range(3651):
            check_day = reference_day - timedelta(days=offset)
            counts = historical_counts.get(check_day)
            completed = int(counts["completed_tasks"]) if counts else 0
            if completed >= default_total:
                streak_days += 1
                continue
            break

        highest_score = 0.0
        for counts in historical_counts.values():
            completed = int(counts["completed_tasks"])
            score = min(completed / default_total, 1.0) if default_total else 0.0
            if score > highest_score:
                highest_score = score

        highest_score = round(max(float(user.highest_productivity_score or 0.0), highest_score), 4)
        current_level, next_level = self._resolve_level_details(streak_days=streak_days)
        next_requirement = int(next_level["requirement"]) if next_level else int(current_level["requirement"])
        progress_value = streak_days if next_level else next_requirement
        progress_ratio = (
            min(progress_value / next_requirement, 1.0) if next_requirement > 0 else 1.0
        )

        profile_changed = False
        resolved_name = (user.name or user.full_name or user.first_name or "").strip()
        if resolved_name and user.name != resolved_name:
            user.name = resolved_name
            profile_changed = True
        if user.level != str(current_level["name"]):
            user.level = str(current_level["name"])
            profile_changed = True
        if int(user.streak_days or 0) != streak_days:
            user.streak_days = streak_days
            profile_changed = True
        if float(user.highest_productivity_score or 0.0) != highest_score:
            user.highest_productivity_score = highest_score
            profile_changed = True

        earned = await self.badge_repo.list_by_user_id(user_id=user_id)
        earned_names = {badge.badge_name for badge in earned}
        badge_changed = False
        for badge_name, milestone in LEVEL_MILESTONES:
            if streak_days >= milestone and badge_name not in earned_names:
                await self.badge_repo.ensure_badge(
                    user_id=user_id,
                    badge_name=badge_name,
                    date_earned=reference_day,
                )
                badge_changed = True
                earned_names.add(badge_name)

        if badge_changed:
            earned = await self.badge_repo.list_by_user_id(user_id=user_id)

        if profile_changed or badge_changed:
            await self.session.commit()

        return {
            "user_name": user.name or user.full_name or user.first_name or "Creator",
            "phone": user.phone,
            "age": user.age,
            "current_level": str(current_level["name"]),
            "current_streak": streak_days,
            "highest_productivity_score": highest_score,
            "earned_badges": [badge.badge_name for badge in earned],
            "next_level": {
                "name": str(next_level["name"]) if next_level else str(current_level["name"]),
                "requirement": next_requirement,
            },
            "progress": {
                "value": progress_value,
                "max": next_requirement,
                "ratio": round(progress_ratio, 4),
            },
        }

    async def build_state(self, user_id: int, target_day: date | None = None, days: int = 7) -> dict:
        day = target_day or date.today()
        catalog = self._task_catalog()
        catalog_names = [item["task_name"] for item in catalog]

        await self.repo.ensure_tasks_for_date(
            user_id=user_id,
            target_day=day,
            task_names=[str(name) for name in catalog_names],
        )
        profile = await self._refresh_profile_metrics(user_id=user_id, reference_day=day)

        rows = await self.repo.list_for_date(user_id=user_id, target_day=day)
        rows_by_name = {self._key(row.task_name): row for row in rows}

        tasks: list[dict[str, str | bool]] = []
        for item in catalog:
            task_name = str(item["task_name"])
            row = rows_by_name.get(self._key(task_name))
            tasks.append(
                {
                    "task_name": task_name,
                    "status": bool(row.status) if row else False,
                    "is_habit": bool(item["is_habit"]),
                    "date": day.isoformat(),
                }
            )

        habits = [task for task in tasks if bool(task["is_habit"])]
        completed_today = sum(1 for task in tasks if bool(task["status"]))
        total_today = len(tasks)
        productivity_today = (completed_today / total_today) if total_today else 0.0

        start_day = day - timedelta(days=max(days, 1) - 1)
        daily_counts = await self.repo.daily_completion_counts(
            user_id=user_id,
            start_day=start_day,
            end_day=day,
        )

        trend: list[dict[str, str | float | int]] = []
        default_total = len(DEFAULT_TASKS)
        for offset in range(max(days, 1)):
            current_day = start_day + timedelta(days=offset)
            counts = daily_counts.get(current_day)
            completed_tasks = int(counts["completed_tasks"]) if counts else 0
            total_tasks = default_total
            score = (completed_tasks / total_tasks) if total_tasks else 0.0
            trend.append(
                {
                    "date": current_day.isoformat(),
                    "label": current_day.strftime("%b %d"),
                    "completed_tasks": completed_tasks,
                    "total_tasks": total_tasks,
                    "score": round(score, 4),
                }
            )

        pending_tasks = [str(task["task_name"]) for task in tasks if not bool(task["status"])]

        return {
            "today": {
                "date": day.isoformat(),
                "tasks": tasks,
                "habits": habits,
                "completed_tasks": completed_today,
                "total_tasks": total_today,
                "productivity_score": round(productivity_today, 4),
            },
            "trend": trend,
            "pending_tasks": pending_tasks,
            "reminder": {
                "enabled": True,
                "start_hour": REMINDER_START_HOUR,
                "repeat_minutes": REMINDER_REPEAT_MINUTES,
                "message": REMINDER_MESSAGE,
            },
            "profile": profile,
        }

    async def update_task_status(
        self,
        user_id: int,
        task_name: str,
        status: bool,
        target_day: date | None = None,
    ) -> dict:
        day = target_day or date.today()
        canonical_name = self._resolve_task_name(task_name)

        await self.repo.ensure_tasks_for_date(
            user_id=user_id,
            target_day=day,
            task_names=list(DEFAULT_TASKS),
        )
        await self.repo.set_status(
            user_id=user_id,
            task_name=canonical_name,
            target_day=day,
            status=status,
        )
        await self.session.commit()
        return await self.build_state(user_id=user_id, target_day=day)

    async def update_profile_settings(
        self,
        user_id: int,
        *,
        name: str | None = None,
        phone: str | None = None,
        age: int | None = None,
    ) -> dict:
        user = await self.user_repo.get_by_id(user_id)
        if user is None or user.is_deleted:
            raise ValueError("User not found")

        if name is not None:
            normalized_name = name.strip()
            user.name = normalized_name or user.name
            user.full_name = normalized_name or user.full_name
        if phone is not None:
            normalized_phone = phone.strip()
            user.phone = normalized_phone or None
        if age is not None:
            user.age = age

        await self.session.commit()
        return await self.build_state(user_id=user_id, target_day=date.today())

    async def build_live_stats(
        self,
        user_id: int,
        *,
        focus_time_today: int = 0,
        target_day: date | None = None,
    ) -> dict[str, int]:
        state = await self.build_state(
            user_id=user_id,
            target_day=target_day or date.today(),
            days=1,
        )
        today = state.get("today", {})
        habits = today.get("habits", [])
        profile = state.get("profile", {})

        return {
            "focus_time_today": max(int(focus_time_today or 0), 0),
            "tasks_completed": int(today.get("completed_tasks", 0) or 0),
            "habits_completed": sum(1 for habit in habits if bool(habit.get("status"))),
            "current_streak": int(profile.get("current_streak", 0) or 0),
        }
