from __future__ import annotations

from collections import defaultdict
from typing import Any

from ...core.events import Event, EventType, Level, Plane, make_event
from .entity_store import EntityStore
from .event_log import EventLog
from .evidence_store import EvidenceStore


class CostLedger:
    """Running tally of spend, broken down by tier, for the economics story."""

    def __init__(self) -> None:
        self.total_usd = 0.0
        self.by_tier: dict[int, float] = defaultdict(float)
        self.calls_by_tier: dict[int, int] = defaultdict(int)

    def add(self, tier: int, usd: float) -> None:
        self.total_usd += usd
        self.by_tier[tier] += usd
        self.calls_by_tier[tier] += 1

    def snapshot(self) -> dict[str, Any]:
        return {
            "total_usd": round(self.total_usd, 4),
            "by_tier": {str(t): round(v, 4) for t, v in self.by_tier.items()},
            "calls_by_tier": dict(self.calls_by_tier),
        }


class StatePlane:
    """The bottom plane: nothing is real until it lands here."""

    def __init__(self) -> None:
        self.events = EventLog()
        self.evidence = EvidenceStore()
        self.entities = EntityStore()
        self.ledger = CostLedger()

    def emit(
        self,
        run_id: str,
        type: EventType,
        title: str,
        data: dict[str, Any] | None = None,
        *,
        plane: Plane | None = None,
        level: Level | None = None,
    ) -> Event:
        event = make_event(run_id, type, title, data, plane=plane, level=level)
        return self.events.append(event)

    def accrue_cost(self, run_id: str, tier: int, model: str, usd: float) -> None:
        self.ledger.add(tier, usd)
        self.emit(
            run_id,
            EventType.COST_ACCRUED,
            f"+${usd:.4f} on tier {tier} ({model})",
            {"tier": tier, "model": model, "usd": round(usd, 6), **self.ledger.snapshot()},
        )
