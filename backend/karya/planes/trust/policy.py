from __future__ import annotations

from dataclasses import dataclass

from ...core.models import NodeType, PlanNode


@dataclass
class PolicyDecision:
    risk_tier: int  # 0 autonomous, 1 notify, 2 block-and-approve
    requires_approval: bool
    summary: str


class PolicyEngine:
    """Decides what Karya may do on its own and what waits for a human.

    The rule from the deck: the boring 95% runs autonomously; anything with real,
    irreversible consequences (an external send) blocks for one-tap approval.
    """

    # Node types whose effects leave the system and reach a real person.
    EXTERNAL_EFFECT = {NodeType.SEND_OUTREACH}

    def assess(self, node: PlanNode) -> PolicyDecision:
        if node.type in self.EXTERNAL_EFFECT:
            n = len(node.params.get("candidate_ids", [])) or node.params.get("count", 0)
            return PolicyDecision(
                risk_tier=2,
                requires_approval=True,
                summary=f"External send to {n} recipient(s) needs your approval.",
            )
        return PolicyDecision(
            risk_tier=0,
            requires_approval=False,
            summary=f"{node.type.value} runs autonomously.",
        )
