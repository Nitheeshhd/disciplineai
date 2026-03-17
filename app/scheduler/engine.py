from apscheduler.schedulers.asyncio import AsyncIOScheduler


def build_scheduler(timezone: str) -> AsyncIOScheduler:
    return AsyncIOScheduler(timezone=timezone)
