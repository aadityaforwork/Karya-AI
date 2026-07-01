from __future__ import annotations

from ..state.store import StatePlane
from .dag import DagValidator
from .planner import Planner
from .reflector import Reflector
from .scheduler import Scheduler


class OrchestrationPlane:
    """Plans the work and drives it to completion."""

    def __init__(self, state: StatePlane) -> None:
        self.planner = Planner()
        self.dag = DagValidator()
        self.reflector = Reflector()
        self.scheduler = Scheduler(state, self.reflector)
