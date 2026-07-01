"""Drive one full goal end-to-end from the terminal, no server needed.

Prints the live event feed and auto-approves the outreach send so the whole
pipeline runs unattended. Defaults to the deterministic mock engine.

    python demo.py "Hire 2 backend engineers in Pune"
"""

import asyncio
import sys

from karya.core.models import ApprovalStatus, GoalStatus
from karya.engine import KaryaEngine

_ICON = {"info": "  ", "success": "[ok]", "warn": "[~]", "error": "[x]"}


async def main(goal_text: str, auto_approve: bool = True) -> None:
    engine = KaryaEngine()
    log = engine.state.events
    goal = engine.start_goal(goal_text)
    q = log.subscribe(goal.id)
    seen = 0

    while True:
        for ev in log.history(goal.id):
            if ev.seq <= seen:
                continue
            seen = ev.seq
            _print(ev)

        if auto_approve:
            for ap in engine.state.entities.pending_approvals(goal.id):
                if ap.status == ApprovalStatus.PENDING:
                    engine.approve(ap.id, True)

        if goal.status in (GoalStatus.DONE, GoalStatus.FAILED):
            for ev in log.history(goal.id):
                if ev.seq > seen:
                    seen = ev.seq
                    _print(ev)
            break
        await asyncio.sleep(0.02)

    print("\n--- cost ---")
    print(engine.state.ledger.snapshot())


def _print(ev) -> None:
    icon = _ICON.get(ev.level.value, "  ")
    print(f"{icon} [{ev.plane.value:<13}] {ev.title}")


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "Hire 2 backend engineers in Pune"
    asyncio.run(main(text))
