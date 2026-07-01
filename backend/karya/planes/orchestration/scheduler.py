from __future__ import annotations

from typing import Awaitable, Callable

from ...core.events import EventType
from ...core.models import NodeStatus, Plan
from ..state.store import StatePlane
from .reflector import Reflector

ExecuteFn = Callable[["PlanNode"], Awaitable[None]]  # noqa: F821


class Scheduler:
    """Walks the validated DAG in dependency order and runs each node.

    Pausing for human approval happens *inside* a node's handler (it simply
    awaits), so the scheduler itself stays a plain ordered walk.
    """

    def __init__(self, state: StatePlane, reflector: Reflector) -> None:
        self.state = state
        self.reflector = reflector

    async def run(self, run_id: str, plan: Plan, order: list[str], execute: ExecuteFn) -> bool:
        for nid in order:
            node = plan.node(nid)
            if node is None:
                continue
            node.status = NodeStatus.RUNNING
            self.state.emit(
                run_id, EventType.NODE_STARTED, f"start {node.id}: {node.title}",
                {"node": node.id, "type": node.type.value},
            )
            attempt = 0
            while True:
                try:
                    await execute(node)
                    node.status = NodeStatus.DONE
                    self.state.emit(
                        run_id, EventType.NODE_COMPLETED, f"done {node.id}",
                        {"node": node.id, "result": node.result},
                    )
                    break
                except Exception as error:  # noqa: BLE001
                    decision = self.reflector.reflect(run_id, node, error, attempt, self.state)
                    if decision == "retry":
                        attempt += 1
                        continue
                    node.status = NodeStatus.FAILED
                    self.state.emit(
                        run_id, EventType.NODE_FAILED, f"failed {node.id}: {error}",
                        {"node": node.id, "error": str(error)},
                    )
                    return False
        return True
