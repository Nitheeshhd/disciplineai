from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

DomainEventHandler = Callable[["DomainEvent"], Awaitable[None]]


@dataclass(slots=True)
class DomainEvent:
    event_id: str
    event_name: str
    occurred_at: datetime
    payload: dict[str, Any]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[DomainEventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: DomainEventHandler) -> None:
        self._handlers[event_name].append(handler)

    async def publish(self, event_name: str, payload: dict[str, Any]) -> None:
        event = DomainEvent(
            event_id=str(uuid4()),
            event_name=event_name,
            occurred_at=datetime.now(timezone.utc),
            payload=payload,
        )
        for handler in self._handlers.get(event_name, []):
            await handler(event)


event_bus = EventBus()
