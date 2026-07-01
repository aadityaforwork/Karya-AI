from __future__ import annotations

from dataclasses import dataclass

from ...core.events import EventType
from ...core.models import Plan
from ..state.store import StatePlane


@dataclass
class Validation:
    ok: bool
    order: list[str]
    error: str = ""


class DagValidator:
    """A plan only runs if it is a well-formed DAG. Catches dangling deps and
    cycles before any model is called or any action is taken.
    """

    def validate(self, run_id: str, plan: Plan, state: StatePlane) -> Validation:
        ids = {n.id for n in plan.nodes}
        for n in plan.nodes:
            for dep in n.depends_on:
                if dep not in ids:
                    return self._reject(run_id, plan, state, f"node {n.id} depends on unknown {dep}")

        order = self._toposort(plan)
        if order is None:
            return self._reject(run_id, plan, state, "plan contains a cycle")

        state.emit(
            run_id,
            EventType.PLAN_VALIDATED,
            f"plan valid - execution order: {' -> '.join(order)}",
            {"order": order},
        )
        return Validation(True, order)

    def _toposort(self, plan: Plan) -> list[str] | None:
        indeg = {n.id: 0 for n in plan.nodes}
        adj: dict[str, list[str]] = {n.id: [] for n in plan.nodes}
        for n in plan.nodes:
            for dep in n.depends_on:
                adj[dep].append(n.id)
                indeg[n.id] += 1
        ready = [nid for nid, d in indeg.items() if d == 0]
        order: list[str] = []
        while ready:
            ready.sort()
            cur = ready.pop(0)
            order.append(cur)
            for nxt in adj[cur]:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    ready.append(nxt)
        return order if len(order) == len(plan.nodes) else None

    def _reject(self, run_id: str, plan: Plan, state: StatePlane, error: str) -> Validation:
        state.emit(run_id, EventType.PLAN_REJECTED, f"plan rejected: {error}", {"error": error})
        return Validation(False, [], error)
