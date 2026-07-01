from __future__ import annotations

import time

from ...core.events import EventType
from ...core.models import Candidate, Job, OutreachDraft
from ..state.store import StatePlane
from ..trust.idempotency import IdempotencyGuard


class ToolSandbox:
    """The only place execution touches the outside world. Deterministic tools,
    every call logged, side effects guarded for idempotency.
    """

    def __init__(self, state: StatePlane, idempotency: IdempotencyGuard) -> None:
        self.state = state
        self.idempotency = idempotency

    def search_talent_pool(self, run_id: str, job: Job, limit: int) -> list[Candidate]:
        scored: list[tuple[float, Candidate]] = []
        wanted = {s.lower() for s in (job.must_have + job.nice_to_have)}
        for c in self.state.entities.all_candidates():
            if c.pool != job.pool:
                continue
            skills = {s.lower() for s in c.skills}
            skill_overlap = len(skills & wanted)
            loc_bonus = 1.5 if c.location.lower() == job.location.lower() else 0.0
            score = skill_overlap + loc_bonus
            if score > 0:
                scored.append((score, c))
        scored.sort(key=lambda x: (-x[0], x[1].id))
        picked = [c for _, c in scored[:limit]]
        self.state.emit(
            run_id,
            EventType.TOOL_CALLED,
            f"search_talent_pool -> {len(picked)} candidates (of {len(self.state.entities.candidates)})",
            {"tool": "search_talent_pool", "returned": len(picked), "limit": limit},
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
