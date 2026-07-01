import asyncio

from karya.config import Settings
from karya.core.models import ApprovalStatus, GoalStatus
from karya.engine import KaryaEngine

_TERMINAL = {GoalStatus.DONE, GoalStatus.FAILED}


def mock_settings(**over) -> Settings:
    s = Settings()
    s.openai_api_key = ""
    s.force_mock = True
    for k, v in over.items():
        setattr(s, k, v)
    return s


async def run_to_completion(engine: KaryaEngine, text: str, *, approve: bool = True) -> str:
    """Start a goal and drive it (auto-approving sends) until it terminates."""
    goal = engine.start_goal(text)
    for _ in range(1000):
        for ap in engine.state.entities.pending_approvals(goal.id):
            if ap.status == ApprovalStatus.PENDING:
                engine.approve(ap.id, approve)
        if goal.status in _TERMINAL:
            return goal.id
        await asyncio.sleep(0.005)
    raise AssertionError("run did not complete in time")
