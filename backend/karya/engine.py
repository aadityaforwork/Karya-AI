from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field

from .config import Settings, settings as default_settings
from .core.events import EventType, Level
from .core.models import (
    Approval,
    ApprovalStatus,
    Candidate,
    ClaimStatus,
    Goal,
    GoalStatus,
    Job,
    Language,
    NodeStatus,
    NodeType,
    OutreachDraft,
    PlanNode,
    ScreeningResult,
)
from .planes.execution.plane import ExecutionPlane
from .planes.orchestration.plane import OrchestrationPlane
from .planes.state.store import StatePlane
from .planes.trust.plane import TrustPlane

from data.seed import build_campaigns, build_candidates, build_jobs, build_prospects  # noqa: E402


@dataclass
class RunContext:
    goal: Goal
    created_at: float = field(default_factory=time.time)
    job: Job | None = None
    sourced: list[Candidate] = field(default_factory=list)
    screenings: list[ScreeningResult] = field(default_factory=list)
    finalists: list[Candidate] = field(default_factory=list)
    drafts: list[OutreachDraft] = field(default_factory=list)
    report: dict = field(default_factory=dict)
    # Set when sourcing matched nobody, so the report can say why.
    no_match: dict | None = None


class KaryaEngine:
    """The runtime: one place that wires the five planes and runs a goal end to end."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or default_settings
        self.state = StatePlane()
        self.trust = TrustPlane(self.state)
        self.execution = ExecutionPlane(self.state, self.trust, self.settings)
        self.orchestration = OrchestrationPlane(self.state)

        self._runs: dict[str, RunContext] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._approval_gates: dict[str, asyncio.Event] = {}
        self._approval_decisions: dict[str, bool] = {}
        # How long a blocked send waits for a human before giving up (see _await_approval).
        self.approval_timeout_s = float(os.getenv("KARYA_APPROVAL_TIMEOUT_S", 30 * 60))

        self._load_seed()

    def _load_seed(self) -> None:
        for c in build_candidates() + build_prospects():
            self.state.entities.add_candidate(c)
            self.state.evidence.ingest_candidate(c)
        for j in build_jobs() + build_campaigns():
            self.state.entities.add_job(j)

    # ----- public api used by the interface plane -----

    def start_goal(self, text: str) -> Goal:
        goal = Goal(text=text, status=GoalStatus.PARSING)
        self.state.entities.add_goal(goal)
        ctx = RunContext(goal=goal)
        self._runs[goal.id] = ctx
        self.state.emit(goal.id, EventType.GOAL_CREATED, f'goal received: "{text}"', {"goal_id": goal.id})
        self._tasks[goal.id] = asyncio.create_task(self._run(ctx))
        return goal

    def approve(self, approval_id: str, decision: bool) -> Approval | None:
        approval = self.state.entities.approval(approval_id)
        if approval is None or approval.status != ApprovalStatus.PENDING:
            return approval
        approval.status = ApprovalStatus.APPROVED if decision else ApprovalStatus.DENIED
        self._approval_decisions[approval_id] = decision
        self.state.emit(
            approval.run_id,
            EventType.APPROVAL_GRANTED if decision else EventType.APPROVAL_DENIED,
            f"human {'approved' if decision else 'declined'}: {approval.summary}",
            {"approval_id": approval_id},
        )
        gate = self._approval_gates.get(approval_id)
        if gate:
            gate.set()
        return approval

    def approval_is_live(self, approval_id: str) -> bool:
        """True when a run in *this* process is still awaiting this approval.

        A pending approval whose gate is gone (server restarted mid-run) can be
        stamped approved, but no run will ever act on it. The interface plane
        checks this so the user gets told, instead of tapping Approve and
        watching nothing happen.
        """
        return approval_id in self._approval_gates

    def run_context(self, run_id: str) -> RunContext | None:
        return self._runs.get(run_id)

    def is_run_active(self, run_id: str) -> bool:
        task = self._tasks.get(run_id)
        return task is not None and not task.done()

    def task(self, run_id: str) -> asyncio.Task | None:
        return self._tasks.get(run_id)

    def start_goal_for_job(self, text: str, job: Job) -> Goal:
        """Like start_goal, but skips goal parsing and uses a known job spec."""
        goal = Goal(text=text, job=job, status=GoalStatus.PLANNING)
        self.state.entities.add_goal(goal)
        ctx = RunContext(goal=goal, job=job)
        self._runs[goal.id] = ctx
        self.state.emit(goal.id, EventType.GOAL_CREATED, f'goal received: "{text}"', {"goal_id": goal.id})
        self._tasks[goal.id] = asyncio.create_task(self._run(ctx, parse=False))
        return goal

    def list_runs(self) -> list[dict]:
        out = []
        for ctx in self._runs.values():
            out.append(
                {
                    "run_id": ctx.goal.id,
                    "goal": ctx.goal.text,
                    "status": ctx.goal.status.value,
                    "created_at": ctx.created_at,
                    "job_title": ctx.job.title if ctx.job else None,
                    "location": ctx.job.location if ctx.job else None,
                    "sourced": len(ctx.sourced),
                    "finalists": [c.name for c in ctx.finalists],
                    "sent": sum(1 for d in ctx.drafts if d.sent),
                    "cost_usd": ctx.report.get("cost", {}).get("total_usd"),
                }
            )
        return sorted(out, key=lambda r: r["created_at"], reverse=True)

    def talent(self, pool: str = "talent") -> list[dict]:
        return [
            {
                "id": c.id,
                "name": c.name,
                "headline": c.headline,
                "location": c.location,
                "language": c.language.value,
                "years_experience": c.years_experience,
                "skills": c.skills,
                "resume_lines": len(c.resume),
                "pool": c.pool,
            }
            for c in self.state.entities.all_candidates()
            if c.pool == pool
        ]

    def pool_facets(self, pool: str = "talent") -> dict:
        """What a pool can actually be asked for: its skills and its locations.

        The workspace form used to take free-text skills with no hint of what
        the pool held, so a plausible spec could quietly match nobody.
        """
        members = [c for c in self.state.entities.all_candidates() if c.pool == pool]
        skills: dict[str, int] = {}
        places: dict[str, int] = {}
        for c in members:
            for s in c.skills:
                skills[s] = skills.get(s, 0) + 1
            places[c.location] = places.get(c.location, 0) + 1
        return {
            "pool": pool,
            "size": len(members),
            "skills": [{"name": s, "count": n} for s, n in sorted(skills.items(), key=lambda kv: (-kv[1], kv[0]))],
            "locations": [{"name": p, "count": n} for p, n in sorted(places.items(), key=lambda kv: (-kv[1], kv[0]))],
        }

    def candidate(self, candidate_id: str) -> dict | None:
        c = self.state.entities.candidates.get(candidate_id)
        if c is None:
            return None
        data = c.model_dump()
        data["language"] = c.language.value
        return data

    def run_candidates(self, run_id: str) -> list[dict] | None:
        ctx = self._runs.get(run_id)
        if ctx is None:
            return None
        by_id = {c.id: c for c in ctx.sourced}
        out = []
        for s in sorted(ctx.screenings, key=lambda x: x.fit_score, reverse=True):
            cand = by_id.get(s.candidate_id)
            out.append(
                {
                    "candidate_id": s.candidate_id,
                    "name": cand.name if cand else s.candidate_id,
                    "language": cand.language.value if cand else "",
                    "location": cand.location if cand else "",
                    "fit_score": s.fit_score,
                    "verdict": s.verdict,
                    "is_finalist": any(f.id == s.candidate_id for f in ctx.finalists),
                    "claims": [
                        {
                            "text": cl.text,
                            "status": cl.status.value,
                            "reason": cl.reason,
                            "evidence": [
                                {"n": n, "text": (line.text if (line := self.state.evidence.get(s.candidate_id, n)) else "")}
                                for n in cl.evidence_lines
                            ],
                        }
                        for cl in s.claims
                    ],
                }
            )
        return out

    async def suggest_reply(
        self,
        *,
        pc_id: str,
        name: str,
        language: str,
        proven_facts: list[str],
        role_facts: dict,
        history: list[dict],
        inbound: str,
    ) -> dict:
        """Grounded follow-up for an inbound reply, routed like every other task."""
        try:
            lang = Language(language)
        except ValueError:
            lang = Language.EN
        return await self.execution.conversation.respond(
            f"conv-{pc_id}",
            name=name,
            language=lang,
            proven_facts=proven_facts,
            role_facts=role_facts,
            history=history,
            inbound=inbound,
        )

    # ----- the run -----

    async def _run(self, ctx: RunContext, parse: bool = True) -> None:
        goal = ctx.goal
        try:
            goal.status = GoalStatus.PLANNING
            if parse:
                ctx.job = self.orchestration.planner.parse_goal(goal.id, goal, self.state)
                goal.job = ctx.job
            plan = self.orchestration.planner.plan(goal.id, goal, ctx.job, self.state)
            validation = self.orchestration.dag.validate(goal.id, plan, self.state)
            if not validation.ok:
                goal.status = GoalStatus.FAILED
                self.state.emit(goal.id, EventType.RUN_FAILED, "invalid plan", {})
                return

            goal.status = GoalStatus.RUNNING
            ok = await self.orchestration.scheduler.run(
                goal.id, plan, validation.order, lambda node: self._execute(ctx, node)
            )
            if ok:
                goal.status = GoalStatus.DONE
                if ctx.no_match:
                    note = ctx.no_match
                    title = (
                        f"no match: nothing in the {note['pool']} pool "
                        f"({note['pool_size']} profiles) has {', '.join(note['requested']) or 'this spec'}"
                    )
                    level = Level.WARN
                else:
                    title = (
                        f"done: {ctx.report.get('sent', 0)} sent, "
                        f"{ctx.report.get('claims', {}).get('verified', 0)} proven / "
                        f"{ctx.report.get('claims', {}).get('rejected', 0)} rejected claims, "
                        f"${ctx.report.get('cost', {}).get('total_usd', 0)}"
                    )
                    level = Level.SUCCESS
                self.state.emit(goal.id, EventType.RUN_COMPLETED, title, ctx.report, level=level)
            else:
                goal.status = GoalStatus.FAILED
                self.state.emit(goal.id, EventType.RUN_FAILED, "run stopped before completion", {})
        except Exception as error:  # noqa: BLE001
            goal.status = GoalStatus.FAILED
            self.state.emit(goal.id, EventType.RUN_FAILED, f"run errored: {error}", {"error": str(error)})

    async def _execute(self, ctx: RunContext, node: PlanNode) -> None:
        handlers = {
            NodeType.SOURCE: self._do_source,
            NodeType.SCREEN: self._do_screen,
            NodeType.DRAFT_OUTREACH: self._do_draft,
            NodeType.SEND_OUTREACH: self._do_send,
            NodeType.REPORT: self._do_report,
        }
        await handlers[node.type](ctx, node)

    async def _do_source(self, ctx: RunContext, node: PlanNode) -> None:
        ctx.sourced = self.execution.sourcing.source(ctx.goal.id, ctx.job, node.params.get("limit", 8))
        if not ctx.sourced:
            ctx.no_match = self._no_match_note(ctx.job)
        node.result = {"sourced": len(ctx.sourced)}

    def _no_match_note(self, job: Job | None) -> dict:
        """Why a spec found nobody, and what the pool could match instead.

        A run that sources nothing is not a failure, but it is useless without
        this: the user needs to know their spec, not the system, is the problem.
        """
        pool = job.pool if job else "talent"
        members = [c for c in self.state.entities.all_candidates() if c.pool == pool]
        counts: dict[str, int] = {}
        for c in members:
            for s in c.skills:
                counts[s] = counts.get(s, 0) + 1
        top = sorted(counts, key=lambda s: (-counts[s], s))[:12]
        return {
            "pool": pool,
            "pool_size": len(members),
            "requested": (job.must_have + job.nice_to_have) if job else [],
            "location": job.location if job else "",
            "available_skills": top,
        }

    async def _do_screen(self, ctx: RunContext, node: PlanNode) -> None:
        for cand in ctx.sourced:
            screening = await self.execution.screening.screen(ctx.goal.id, cand, ctx.job)
            ctx.screenings.append(screening)
        ranked = sorted(ctx.screenings, key=lambda s: s.fit_score, reverse=True)
        keep = [s for s in ranked if s.verdict in ("advance", "hold")][: ctx.job.headcount]
        by_id = {c.id: c for c in ctx.sourced}
        ctx.finalists = [by_id[s.candidate_id] for s in keep]
        node.result = {"screened": len(ctx.screenings), "finalists": [c.name for c in ctx.finalists]}

    async def _do_draft(self, ctx: RunContext, node: PlanNode) -> None:
        for cand in ctx.finalists:
            screening = next((s for s in ctx.screenings if s.candidate_id == cand.id), None)
            proven = screening.claims if screening else []
            draft = await self.execution.outreach.draft(ctx.goal.id, cand, ctx.job, proven)
            ctx.drafts.append(draft)
        node.result = {"drafts": len(ctx.drafts)}

    async def _do_send(self, ctx: RunContext, node: PlanNode) -> None:
        if not ctx.drafts:
            self.state.emit(ctx.goal.id, EventType.POLICY_DECISION, "nothing to send", {})
            node.result = {"sent": 0}
            return

        decision = self.trust.policy.assess(
            PlanNode(id=node.id, type=node.type, title=node.title,
                     params={"candidate_ids": [d.candidate_id for d in ctx.drafts]})
        )
        self.state.emit(
            ctx.goal.id, EventType.POLICY_DECISION,
            f"policy: risk tier {decision.risk_tier} - {decision.summary}",
            {"risk_tier": decision.risk_tier, "requires_approval": decision.requires_approval},
        )

        if decision.requires_approval:
            approved = await self._await_approval(ctx, node, decision.summary)
            if not approved:
                node.status = NodeStatus.DONE
                node.result = {"sent": 0, "declined": True}
                return

        sent = 0
        for draft in ctx.drafts:
            receipt = self.execution.sandbox.send_message(ctx.goal.id, draft)
            sent += 1 if receipt.get("sent") else 0
        node.result = {"sent": sent}

    async def _do_report(self, ctx: RunContext, node: PlanNode) -> None:
        verified = sum(
            len([c for c in s.claims if c.status == ClaimStatus.VERIFIED]) for s in ctx.screenings
        )
        rejected = sum(
            len([c for c in s.claims if c.status == ClaimStatus.REJECTED]) for s in ctx.screenings
        )
        ledger = self.state.ledger.snapshot(ctx.goal.id)
        calls = sum(ledger["calls_by_tier"].values())
        # A run that made no model calls has no economics to report; quoting a
        # multiple there produced nonsense like "0.2x cheaper" on a $0.00 run.
        frontier_only = self._frontier_only_estimate(verified + rejected) if calls else 0.0
        ctx.report = {
            "goal": ctx.goal.text,
            "job": ctx.job.model_dump() if ctx.job else {},
            "sourced": len(ctx.sourced),
            "screened": len(ctx.screenings),
            "finalists": [
                {
                    "name": c.name,
                    "language": c.language.value,
                    "fit": next((s.fit_score for s in ctx.screenings if s.candidate_id == c.id), 0),
                    "proven_facts": [
                        cl.text
                        for s in ctx.screenings
                        if s.candidate_id == c.id
                        for cl in s.claims
                        if cl.status == ClaimStatus.VERIFIED
                    ],
                }
                for c in ctx.finalists
            ],
            "sent": sum(1 for d in ctx.drafts if d.sent),
            "no_match": ctx.no_match,
            "claims": {"verified": verified, "rejected": rejected},
            "cost": ledger,
            "cost_comparison": {
                "karya_usd": ledger["total_usd"],
                "frontier_only_usd": frontier_only if calls else None,
                "savings_x": round(frontier_only / ledger["total_usd"], 1) if ledger["total_usd"] else None,
            },
        }
        node.result = {"report": True}

    def _frontier_only_estimate(self, calls: int) -> float:
        top = self.settings.tier(len(self.settings.tiers) - 1)
        # Same calls, but every one billed at the top tier (rough token assumption).
        per_call = (250 / 1000) * top.price_in + (180 / 1000) * top.price_out
        return round(max(calls, 1) * per_call, 4)

    async def _await_approval(self, ctx: RunContext, node: PlanNode, summary: str) -> bool:
        """Block the run until a human decides - but never forever.

        An abandoned tab used to leave this task awaiting an Event that nothing
        would ever set: the run hung, and the workspace that was waiting on its
        results stayed empty with no explanation. Timing out turns that into an
        ordinary declined send, so the run still finishes and reports.
        """
        approval = Approval(
            run_id=ctx.goal.id, node_id=node.id, risk_tier=2, summary=summary,
            payload={
                "drafts": [
                    {"candidate_id": d.candidate_id, "subject": d.subject, "body": d.body,
                     "language": d.language.value, "cited_facts": [c.text for c in d.cited_claims]}
                    for d in ctx.drafts
                ]
            },
        )
        self.state.entities.add_approval(approval)
        gate = asyncio.Event()
        self._approval_gates[approval.id] = gate
        node.status = NodeStatus.BLOCKED
        ctx.goal.status = GoalStatus.AWAITING_APPROVAL
        self.state.emit(
            ctx.goal.id, EventType.APPROVAL_REQUESTED,
            f"approval needed: {summary}",
            {"approval_id": approval.id, "summary": summary, "drafts": approval.payload["drafts"]},
        )
        try:
            await asyncio.wait_for(gate.wait(), timeout=self.approval_timeout_s)
        except asyncio.TimeoutError:
            approval.status = ApprovalStatus.EXPIRED
            self.state.emit(
                ctx.goal.id, EventType.APPROVAL_DENIED,
                f"approval expired after {int(self.approval_timeout_s / 60)} min without a decision",
                {"approval_id": approval.id, "expired": True}, level=Level.WARN,
            )
            return False
        finally:
            self._approval_gates.pop(approval.id, None)
            ctx.goal.status = GoalStatus.RUNNING
        return self._approval_decisions.get(approval.id, False)
