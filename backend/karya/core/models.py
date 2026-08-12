from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from .ids import new_id


class Language(str, Enum):
    EN = "en"
    HI = "hi"
    MR = "mr"
    TE = "te"


# Cheap-model (tier 0) accuracy per language, learned by the fact-checker over time.
# Seeded from the deck: English 88, Hindi 72, Marathi/Telugu 40.
LANGUAGE_PRIOR_ACCURACY: dict[Language, float] = {
    Language.EN: 0.88,
    Language.HI: 0.72,
    Language.MR: 0.40,
    Language.TE: 0.40,
}


# ----- talent pool entities -----


class ResumeLine(BaseModel):
    """One citable line of a resume. `n` is the evidence anchor used by claims."""

    n: int
    text: str


class Candidate(BaseModel):
    """A subject the workers reason about. In hiring it's a person; in sales it's a
    prospect/account. Same shape: a profile of citable lines + signals (skills)."""

    id: str
    name: str
    headline: str
    location: str
    language: Language
    years_experience: float
    skills: list[str] = Field(default_factory=list)
    resume: list[ResumeLine] = Field(default_factory=list)
    pool: str = "talent"  # which data pool: "talent" (hiring) | "prospects" (sales)

    def line(self, n: int) -> Optional[ResumeLine]:
        return next((l for l in self.resume if l.n == n), None)


class Job(BaseModel):
    """A target spec. In hiring it's a role; in sales it's an ICP. Same shape:
    required signals (must_have) and nice-to-haves, scoped to a pool."""

    id: str
    title: str
    location: str
    headcount: int = 1
    must_have: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    seniority: str = "mid"
    pool: str = "talent"


# ----- claims & evidence (the trust substrate) -----


class ClaimStatus(str, Enum):
    PROPOSED = "proposed"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Claim(BaseModel):
    """A factual assertion a worker makes. It is worthless until grounded."""

    id: str = Field(default_factory=lambda: new_id("clm"))
    subject_id: str  # candidate id this claim is about
    text: str
    evidence_lines: list[int] = Field(default_factory=list)  # cited resume line numbers
    status: ClaimStatus = ClaimStatus.PROPOSED
    reason: str = ""  # why verified / rejected


class ScreeningResult(BaseModel):
    candidate_id: str
    fit_score: float  # 0..1
    verdict: str  # "advance" | "hold" | "reject"
    claims: list[Claim] = Field(default_factory=list)
    rationale: str = ""


class OutreachDraft(BaseModel):
    id: str = Field(default_factory=lambda: new_id("out"))
    candidate_id: str
    channel: str = "email"
    language: Language = Language.EN
    subject: str = ""
    body: str = ""
    cited_claims: list[Claim] = Field(default_factory=list)
    sent: bool = False


# ----- orchestration entities -----


class NodeType(str, Enum):
    SOURCE = "SOURCE"
    SCREEN = "SCREEN"
    DRAFT_OUTREACH = "DRAFT_OUTREACH"
    SEND_OUTREACH = "SEND_OUTREACH"
    REPORT = "REPORT"


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    BLOCKED = "blocked"  # waiting on human approval
    DONE = "done"
    FAILED = "failed"


class PlanNode(BaseModel):
    id: str
    type: NodeType
    title: str
    depends_on: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)
    status: NodeStatus = NodeStatus.PENDING
    result: dict[str, Any] = Field(default_factory=dict)


class Plan(BaseModel):
    id: str = Field(default_factory=lambda: new_id("plan"))
    goal_id: str
    nodes: list[PlanNode] = Field(default_factory=list)

    def node(self, node_id: str) -> Optional[PlanNode]:
        return next((n for n in self.nodes if n.id == node_id), None)


class GoalStatus(str, Enum):
    PARSING = "parsing"
    PLANNING = "planning"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    DONE = "done"
    FAILED = "failed"


class Goal(BaseModel):
    id: str = Field(default_factory=lambda: new_id("goal"))
    text: str
    job: Optional[Job] = None
    status: GoalStatus = GoalStatus.PARSING


# ----- approvals (human-in-the-loop) -----


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class Approval(BaseModel):
    id: str = Field(default_factory=lambda: new_id("apr"))
    run_id: str
    node_id: str
    risk_tier: int  # 0 = autonomous, 1 = notify, 2 = block-and-approve
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
