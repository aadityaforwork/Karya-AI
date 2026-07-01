from __future__ import annotations

import asyncio
from collections import defaultdict

from ...core.events import Event


class EventLog:
    """Append-only log and the single source of truth for the activity feed.

    Every appended event is fanned out to live subscribers (the SSE feed) and
    retained so a late subscriber can replay the run from the start.
    """

    def __init__(self) -> None:
        self._events: list[Event] = []
        self._by_run: dict[str, list[Event]] = defaultdict(list)
        self._subscribers: dict[str, set[asyncio.Queue[Event]]] = defaultdict(set)
        self._seq = 0

    def append(self, event: Event) -> Event:
        self._seq += 1
        event.seq = self._seq
        self._events.append(event)
        self._by_run[event.run_id].append(event)
        for q in list(self._subscribers.get(event.run_id, ())):
            q.put_nowait(event)
        return event

    def history(self, run_id: str) -> list[Event]:
        return list(self._by_run.get(run_id, []))

    def all(self) -> list[Event]:
        return list(self._events)

    def subscribe(self, run_id: str) -> asyncio.Queue[Event]:
        q: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers[run_id].add(q)
        return q

    def unsubscribe(self, run_id: str, q: asyncio.Queue[Event]) -> None:
        self._subscribers.get(run_id, set()).discard(q)
