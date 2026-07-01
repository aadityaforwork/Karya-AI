from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from ..core.ids import new_id


class Stage(str, Enum):
    SOURCED = "sourced"
    SCREENED = "screened"
    CONTACTED = "contacted"
    REPLIED = "replied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


# The order candidates advance through (rejected is terminal, off to the side).
FUNNEL: list[Stage] = [
    Stage.SOURCED,
    Stage.SCREENED,
    Stage.CONTACTED,
    Stage.REPLIED,
    Stage.INTERVIEW,
    Stage.OFFER,
]


class User(BaseModel):
    id: str = Field(default_factory=lambda: new_id("usr"))
    email: str
    name: str = ""
    password_hash: str = ""
    salt: str = ""
    plan: str = "free"
    created_at: float = 0.0

    def public(self) -> dict:
        return {"id": self.id, "email": self.email, "name": self.name, "plan": self.plan}


class RoleStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class Role(BaseModel):
    """A workspace: an instance of a skill. A 'role' for hiring, a 'campaign' for sales."""

    id: str = Field(default_factory=lambda: new_id("ws"))
    user_id: str = ""
    skill: str = "hiring"
    title: str
    location: str
    headcount: int = 1
    must_have: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    seniority: str = "mid"
    status: RoleStatus = RoleStatus.OPEN
    created_at: float = 0.0


class PipelineCandidate(BaseModel):
    id: str = Field(default_factory=lambda: new_id("pc"))
    user_id: str = ""
    role_id: str
    candidate_id: str
    name: str
    language: str = "en"
    location: str = ""
    fit: float = 0.0
    verdict: str = ""
    stage: Stage = Stage.SOURCED
    claims: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[dict[str, Any]] = Field(default_factory=list)
    run_id: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0


class Message(BaseModel):
    id: str = Field(default_factory=lambda: new_id("msg"))
    pipeline_id: str
    sender: str  # "karya" | "candidate" | "system"
    channel: str = "email"
    language: str = "en"
    body: str = ""
    created_at: float = 0.0


class RunRecord(BaseModel):
    id: str
    user_id: str = ""
    role_id: str
    goal: str
    status: str
    sourced: int = 0
    screened: int = 0
    sent: int = 0
    cost_usd: float = 0.0
    frontier_only_usd: float = 0.0
    savings_x: float | None = None
    claims_verified: int = 0
    claims_rejected: int = 0
    by_tier: dict[str, Any] = Field(default_factory=dict)
    created_at: float = 0.0
