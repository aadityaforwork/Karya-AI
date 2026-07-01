from karya.core.models import Language
from karya.planes.execution.llm import LLMResult
from karya.planes.execution.router import CostAwareRouter
from karya.planes.state.store import StatePlane

from conftest import mock_settings


def _result(tier: int, conf: float) -> LLMResult:
    return LLMResult(
        data={}, confidence=conf, tier=tier, model=f"m{tier}",
        tokens_in=10, tokens_out=10, cost_usd=0.001 * (tier + 1), used_mock=True,
    )


async def test_english_stays_on_cheap_tier():
    state = StatePlane()
    router = CostAwareRouter(state, mock_settings())

    async def call(tier: int) -> LLMResult:
        return _result(tier, 0.9)  # confident at every tier

    res = await router.route("r1", "screen", Language.EN, call)
    assert res.tier == 0  # never had to escalate


async def test_marathi_starts_on_smarter_tier():
    state = StatePlane()
    router = CostAwareRouter(state, mock_settings())
    started: list[int] = []

    async def call(tier: int) -> LLMResult:
        started.append(tier)
        return _result(tier, 0.9)

    await router.route("r1", "screen", Language.MR, call)
    assert started[0] >= 1  # low cheap-model accuracy -> skip the doomed tier 0


async def test_low_confidence_escalates():
    state = StatePlane()
    router = CostAwareRouter(state, mock_settings())
    seen: list[int] = []

    async def call(tier: int) -> LLMResult:
        seen.append(tier)
        return _result(tier, 0.4)  # always under tau -> escalate to the top

    res = await router.route("r1", "screen", Language.EN, call)
    assert seen == [0, 1, 2] and res.tier == 2
