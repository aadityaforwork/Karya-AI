from __future__ import annotations

from typing import Awaitable, Callable

from ...config import Settings, settings as default_settings
from ...core.events import EventType
from ...core.models import LANGUAGE_PRIOR_ACCURACY, Language
from ..state.store import StatePlane
from .llm import LLMResult

# call(tier_number) -> LLMResult for that tier
CallFn = Callable[[int], Awaitable[LLMResult]]


class CostAwareRouter:
    """Runs the cheapest model that can be trusted for each task.

    Two levers, both from the deck:
      1. Language-aware start tier  - low cheap-model accuracy in a language means
         we *begin* on a smarter model instead of wasting a doomed cheap call.
      2. Confidence gate            - a tier's answer is accepted only if it clears
         tau; otherwise we escalate. The top tier has no gate.
    The verifier's outcomes feed back into the per-language priors over time.
    """

    def __init__(self, state: StatePlane, settings: Settings | None = None) -> None:
        self.state = state
        self.settings = settings or default_settings
        # (task_kind, language) -> learned cheap-model accuracy
        self.priors: dict[tuple[str, Language], float] = {}

    def _prior(self, task_kind: str, language: Language) -> float:
        key = (task_kind, language)
        if key not in self.priors:
            self.priors[key] = LANGUAGE_PRIOR_ACCURACY.get(language, 0.8)
        return self.priors[key]

    def _start_tier(self, accuracy: float) -> int:
        # Cheap model is only worth trying when it clears the bar often enough.
        if accuracy >= 0.70:
            return 0
        if accuracy >= 0.50:
            return 1
        return 1  # very low cheap accuracy still starts mid, can escalate to top

    async def route(
        self,
        run_id: str,
        task_kind: str,
        language: Language,
        call: CallFn,
        *,
        label: str = "",
    ) -> LLMResult:
        prior = self._prior(task_kind, language)
        start = self._start_tier(prior)
        tau = self.settings.gate_tau
        max_tier = len(self.settings.tiers) - 1

        self.state.emit(
            run_id,
            EventType.ROUTED,
            f"Route {label or task_kind} ({language.value}) - start tier {start}",
            {
                "task": task_kind,
                "language": language.value,
                "start_tier": start,
                "prior_accuracy": round(prior, 3),
                "tau": tau,
            },
        )

        result: LLMResult | None = None
        tier = start
        while tier <= max_tier:
            spec = self.settings.tier(tier)
            result = await call(tier)
            self.state.emit(
                run_id,
                EventType.MODEL_CALLED,
                f"Tier {tier} ({spec.model}) -> conf {result.confidence:.2f}, ${result.cost_usd:.4f}",
                {
                    "tier": tier,
                    "model": spec.model,
                    "confidence": round(result.confidence, 3),
                    "tokens_in": result.tokens_in,
                    "tokens_out": result.tokens_out,
                    "cost_usd": round(result.cost_usd, 6),
                    "mock": result.used_mock,
                },
            )
            self.state.accrue_cost(run_id, tier, spec.model, result.cost_usd)

            gated = spec.gated and tier < max_tier
            if gated and result.confidence < tau:
                self.state.emit(
                    run_id,
                    EventType.ESCALATED,
                    f"conf {result.confidence:.2f} < tau {tau} - escalate tier {tier} -> {tier + 1}",
                    {"from_tier": tier, "to_tier": tier + 1, "confidence": round(result.confidence, 3)},
                )
                tier += 1
                continue
            break

        assert result is not None
        self._update_prior(run_id, task_kind, language, accepted_tier=result.tier, start=start)
        return result

    def _update_prior(
        self, run_id: str, task_kind: str, language: Language, *, accepted_tier: int, start: int
    ) -> None:
        # Outcome log updates routing priors: cheap-tier success nudges accuracy up,
        # an escalation nudges it down. Only meaningful when we actually tried tier 0.
        if start > 0:
            return
        alpha = 0.2
        signal = 1.0 if accepted_tier == 0 else 0.0
        old = self._prior(task_kind, language)
        new = round(old * (1 - alpha) + signal * alpha, 3)
        self.priors[(task_kind, language)] = new
        self.state.emit(
            run_id,
            EventType.PRIOR_UPDATED,
            f"prior[{task_kind},{language.value}] {old} -> {new}",
            {"task": task_kind, "language": language.value, "old": old, "new": new},
        )
