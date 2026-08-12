from __future__ import annotations

import time

from ...core.events import EventType, Level
from ...core.models import Candidate, Job, OutreachDraft
from ..state.store import StatePlane
from ..trust.idempotency import IdempotencyGuard

# Cities the pool spells more than one way. Without this a "Bengaluru" campaign
# scores every Bangalore profile as out-of-town.
_PLACE_ALIAS = {"bengaluru": "bangalore", "bombay": "mumbai", "gurugram": "gurgaon"}


def _norm_place(name: str) -> str:
    key = name.strip().lower()
    return _PLACE_ALIAS.get(key, key)


def _same_place(a: str, b: str) -> bool:
    return _norm_place(a) == _norm_place(b)


class ToolSandbox:
    """The only place execution touches the outside world. Deterministic tools,
    every call logged, side effects guarded for idempotency.
    """

    def __init__(self, state: StatePlane, idempotency: IdempotencyGuard) -> None:
        self.state = state
        self.idempotency = idempotency

    def search_talent_pool(self, run_id: str, job: Job, limit: int) -> list[Candidate]:
        """Find pool members who actually match the spec.

        A skill overlap is required to qualify: being in the right city is a
        ranking signal, never a reason to source someone. Previously the
        location bonus alone cleared the bar, so a spec the pool could not serve
        still returned a full shortlist of unrelated people - who were then
        screened, had every claim rejected, and left the run reporting success
        with nothing to show for it.
        """
        wanted = {s.lower() for s in (job.must_have + job.nice_to_have)}
        must = {s.lower() for s in job.must_have}
        in_pool = [c for c in self.state.entities.all_candidates() if c.pool == job.pool]

        scored: list[tuple[float, float, Candidate]] = []
        for c in in_pool:
            skills = {s.lower() for s in c.skills}
            overlap = skills & wanted
            if not overlap:
                continue
            must_hits = len(skills & must)
            loc_bonus = 1.5 if _same_place(c.location, job.location) else 0.0
            scored.append((must_hits * 2 + len(overlap) + loc_bonus, must_hits, c))

        scored.sort(key=lambda x: (-x[0], x[2].id))
        picked = [c for _, _, c in scored[:limit]]

        if not picked:
            # A dead spec is the single most confusing outcome in the product, so
            # say exactly why, and what the pool could actually match.
            available = sorted({s for c in in_pool for s in c.skills})
            self.state.emit(
                run_id,
                EventType.TOOL_CALLED,
                f"search_talent_pool -> no match for {', '.join(job.must_have + job.nice_to_have) or 'this spec'} "
                f"in the {job.pool} pool ({len(in_pool)} profiles)",
                {
                    "tool": "search_talent_pool", "returned": 0, "limit": limit,
                    "no_match": True, "pool": job.pool, "pool_size": len(in_pool),
                    "requested": job.must_have + job.nice_to_have,
                    "available_skills": available,
                },
                level=Level.WARN,
            )
            return []

        self.state.emit(
            run_id,
            EventType.TOOL_CALLED,
            f"search_talent_pool -> {len(picked)} candidates (of {len(in_pool)} in the {job.pool} pool)",
            {"tool": "search_talent_pool", "returned": len(picked), "limit": limit,
             "pool": job.pool, "pool_size": len(in_pool)},
        )
        return picked

    def send_message(self, run_id: str, draft: OutreachDraft) -> dict:
        key = f"send:{run_id}:{draft.candidate_id}"
        if not self.idempotency.run_once(key):
            self.state.emit(
                run_id,
                EventType.IDEMPOTENT_SKIP,
                f"duplicate send to {draft.candidate_id} skipped",
                {"candidate_id": draft.candidate_id, "key": key},
            )
            return {"sent": False, "reason": "duplicate"}

        draft.sent = True
        receipt = {
            "sent": True,
            "candidate_id": draft.candidate_id,
            "channel": draft.channel,
            "at": time.time(),
        }
        self.state.emit(
            run_id,
            EventType.OUTREACH_SENT,
            f"sent {draft.channel} to {draft.candidate_id} ({draft.language.value})",
            {"tool": "send_message", **receipt},
        )
        return receipt
