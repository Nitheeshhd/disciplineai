from __future__ import annotations

from app.core.events import DomainEvent, event_bus

from .events import HABIT_LOGGED_EVENT


async def handle_habit_logged(event: DomainEvent) -> None:
    from app.workers.tasks import project_daily_analytics_task
    from app.core.metrics import habit_logged_events_total

    metric_date = event.payload.get("log_date")
    if metric_date:
        try:
            project_daily_analytics_task.delay(metric_date)
            habit_logged_events_total.inc()
        except Exception:
            # Avoid impacting write path if broker is temporarily unavailable.
            pass


def register_analytics_event_handlers() -> None:
    event_bus.subscribe(HABIT_LOGGED_EVENT, handle_habit_logged)
