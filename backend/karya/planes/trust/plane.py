from __future__ import annotations

from ..state.store import StatePlane
from .idempotency import IdempotencyGuard
from .policy import PolicyEngine
from .verifier import Verifier


class TrustPlane:
    """Nothing reaches state or a human except through here."""

    def __init__(self, state: StatePlane) -> None:
        self.verifier = Verifier(state.evidence)
        self.policy = PolicyEngine()
        self.idempotency = IdempotencyGuard()
