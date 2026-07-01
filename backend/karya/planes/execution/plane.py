from __future__ import annotations

from ...config import Settings
from ..state.store import StatePlane
from ..trust.plane import TrustPlane
from .agents import OutreachAgent, ScreeningAgent, SourcingAgent
from .conversation import ConversationAgent
from .llm import LLMClient
from .router import CostAwareRouter
from .sandbox import ToolSandbox


class ExecutionPlane:
    """Specialist workers, all behind one cost-aware router and the trust gate."""

    def __init__(
        self, state: StatePlane, trust: TrustPlane, settings: Settings | None = None
    ) -> None:
        self.llm = LLMClient(settings)
        self.router = CostAwareRouter(state, settings)
        self.sandbox = ToolSandbox(state, trust.idempotency)
        self.sourcing = SourcingAgent(state, self.sandbox)
        self.screening = ScreeningAgent(state, self.router, self.llm, trust.verifier, settings)
        self.outreach = OutreachAgent(state, self.router, self.llm, settings)
        self.conversation = ConversationAgent(state, self.router, self.llm, settings)
