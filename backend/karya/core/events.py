from __future__ import annotations

import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .ids import new_id


class Plane(str, Enum):
    INTERFACE = "interface"
    ORCHESTRATION = "orchestration"
    EXECUTION = "execution"
    TRUST = "trust"
    STATE = "state"


class Level(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARN = "warn"
    ERROR = "error"


class EventType(str, Enum):
    # interface / lifecycle
    GOAL_CREATED = "goal.created"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"

    # orchestration
    PLAN_PRODUCED = "plan.produced"
    PLAN_VALIDATED = "plan.validated"
    PLAN_REJECTED = "plan.rejected"
    NODE_STARTED = "node.started"
    NODE_COMPLETED = "node.completed"
    NODE_FAILED = "node.failed"
    REFLECT = "orchestration.reflect"

    # execution / routing
    ROUTED = "router.routed"
    MODEL_CALLED = "model.called"
    ESCALATED = "router.escalated"
    PRIOR_UPDATED = "router.prior_updated"
    CANDIDATE_SOURCED = "candidate.sourced"
    CANDIDATE_SCREENED = "candidate.screened"
    OUTREACH_DRAFTED = "outreach.drafted"
    OUTREACH_SENT = "outreach.sent"
    TOOL_CALLED = "tool.called"

    # trust
    EVIDENCE_RETRIEVED = "evidence.retrieved"
    CLAIM_PROPOSED = "claim.proposed"
    CLAIM_VERIFIED = "claim.verified"
    CLAIM_REJECTED = "claim.rejected"
    POLICY_DECISION = "policy.decision"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_DENIED = "approval.denied"
    IDEMPOTENT_SKIP = "idempotency.skip"

    # accounting
    COST_ACCRUED = "cost.accrued"


# Sensible default plane/level per event type so callers stay terse.
_DEFAULTS: dict[EventType, tuple[Plane, Level]] = {
    EventType.GOAL_CREATED: (Plane.INTERFACE, Level.INFO),
    EventType.RUN_COMPLETED: (Plane.INTERFACE, Level.SUCCESS),
    EventType.RUN_FAILED: (Plane.INTERFACE, Level.ERROR),
    EventType.PLAN_PRODUCED: (Plane.ORCHESTRATION, Level.INFO),
    EventType.PLAN_VALIDATED: (Plane.ORCHESTRATION, Level.SUCCESS),
    EventType.PLAN_REJECTED: (Plane.ORCHESTRATION, Level.ERROR),
    EventType.NODE_STARTED: (Plane.ORCHESTRATION, Level.INFO),
    EventType.NODE_COMPLETED: (Plane.ORCHESTRATION, Level.SUCCESS),
    EventType.NODE_FAILED: (Plane.ORCHESTRATION, Level.ERROR),
    EventType.REFLECT: (Plane.ORCHESTRATION, Level.WARN),
    EventType.ROUTED: (Plane.EXECUTION, Level.INFO),
    EventType.MODEL_CALLED: (Plane.EXECUTION, Level.INFO),
    EventType.ESCALATED: (Plane.EXECUTION, Level.WARN),
    EventType.PRIOR_UPDATED: (Plane.EXECUTION, Level.INFO),
    EventType.CANDIDATE_SOURCED: (Plane.EXECUTION, Level.INFO),
    EventType.CANDIDATE_SCREENED: (Plane.EXECUTION, Level.INFO),
    EventType.OUTREACH_DRAFTED: (Plane.EXECUTION, Level.INFO),
    EventType.OUTREACH_SENT: (Plane.EXECUTION, Level.SUCCESS),
    EventType.TOOL_CALLED: (Plane.EXECUTION, Level.INFO),
    EventType.EVIDENCE_RETRIEVED: (Plane.TRUST, Level.INFO),
    EventType.CLAIM_PROPOSED: (Plane.TRUST, Level.INFO),
    EventType.CLAIM_VERIFIED: (Plane.TRUST, Level.SUCCESS),
    EventType.CLAIM_REJECTED: (Plane.TRUST, Level.WARN),
    EventType.POLICY_DECISION: (Plane.TRUST, Level.INFO),
    EventType.APPROVAL_REQUESTED: (Plane.TRUST, Level.WARN),
    EventType.APPROVAL_GRANTED: (Plane.TRUST, Level.SUCCESS),
    EventType.APPROVAL_DENIED: (Plane.TRUST, Level.ERROR),
    EventType.IDEMPOTENT_SKIP: (Plane.TRUST, Level.WARN),
    EventType.COST_ACCRUED: (Plane.STATE, Level.INFO),
}


class Event(BaseModel):
    id: str = Field(default_factory=lambda: new_id("evt"))
    seq: int = 0  # assigned by the event log on append
    run_id: str
    ts: float = Field(default_factory=time.time)
    type: EventType
    plane: Plane
    level: Level
    title: str
    data: dict[str, Any] = Field(default_factory=dict)


def make_event(
    run_id: str,
    type: EventType,
    title: str,
    data: dict[str, Any] | None = None,
    *,
    plane: Plane | None = None,
    level: Level | None = None,
) -> Event:
    d_plane, d_level = _DEFAULTS.get(type, (Plane.EXECUTION, Level.INFO))
    return Event(
        run_id=run_id,
        type=type,
        plane=plane or d_plane,
        level=level or d_level,
        title=title,
        data=data or {},
    )
