from __future__ import annotations

from ...core.events import EventType
from ...core.models import PlanNode
from ..state.store import StatePlane


class Reflector:
    """Decides what to do when a step misbehaves: retry once, then give up.

    Kept deliberately small - its presence is what lets the scheduler stay dumb
    and the run stay self-healing for transient faults.
    """

    MAX_RETRIES = 1

    def reflect(
        self, run_id: str, node: PlanNode, error: Exception, attempt: int, state: StatePlane
    ) -> str:
        if attempt < self.MAX_RETRIES:
            state.emit(
                run_id,
                EventType.REFLECT,
                f"{node.id} failed ({error}) - retrying ({attempt + 1}/{self.MAX_RETRIES})",
                {"node": node.id, "error": str(error), "decision": "retry"},
            )
            return "retry"
        state.emit(
            run_id,
            EventType.REFLECT,
            f"{node.id} failed ({error}) - giving up",
            {"node": node.id, "error": str(error), "decision": "abort"},
        )
        return "abort"
