from __future__ import annotations

from typing import Optional

from ...core.models import (
    Approval,
    Candidate,
    Goal,
    Job,
    OutreachDraft,
    Plan,
    ScreeningResult,
)


class EntityStore:
    """Working memory for the durable nouns of a run."""

    def __init__(self) -> None:
        self.candidates: dict[str, Candidate] = {}
        self.jobs: dict[str, Job] = {}
        self.goals: dict[str, Goal] = {}
        self.plans: dict[str, Plan] = {}
        self.screenings: dict[str, ScreeningResult] = {}  # candidate_id -> result
        self.drafts: dict[str, OutreachDraft] = {}
        self.approvals: dict[str, Approval] = {}

    # candidates / jobs (seeded talent pool)
    def add_candidate(self, c: Candidate) -> None:
        self.candidates[c.id] = c

    def add_job(self, j: Job) -> None:
        self.jobs[j.id] = j

    def all_candidates(self) -> list[Candidate]:
        return list(self.candidates.values())

    # run artifacts
    def add_goal(self, g: Goal) -> None:
        self.goals[g.id] = g

    def add_plan(self, p: Plan) -> None:
        self.plans[p.id] = p

    def set_screening(self, r: ScreeningResult) -> None:
        self.screenings[r.candidate_id] = r

    def add_draft(self, d: OutreachDraft) -> None:
        self.drafts[d.id] = d

    def add_approval(self, a: Approval) -> None:
        self.approvals[a.id] = a

    def approval(self, approval_id: str) -> Optional[Approval]:
        return self.approvals.get(approval_id)

    def pending_approvals(self, run_id: str) -> list[Approval]:
        return [
            a
            for a in self.approvals.values()
            if a.run_id == run_id and a.status.value == "pending"
        ]
