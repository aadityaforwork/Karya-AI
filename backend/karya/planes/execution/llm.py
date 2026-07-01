from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ...config import Settings, TierSpec, settings as default_settings


@dataclass
class LLMResult:
    """Outcome of a single model call at one tier."""

    data: dict[str, Any]
    confidence: float
    tier: int
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    used_mock: bool
    raw_text: str = ""


# A mock handler answers a task deterministically given the tier it ran on.
MockFn = Callable[[int], tuple[dict[str, Any], float]]


def _estimate_tokens(text: str) -> int:
    # ~4 chars/token is good enough for cost accounting and demo numbers.
    return max(1, len(text) // 4)


class LLMClient:
    """One call surface over the whole tier ladder.

    `complete` runs exactly one tier. Escalation across tiers is the router's
    job. When no API key is configured (or mock is forced) the same call returns
    a deterministic result, so every other plane behaves identically offline.
    """

    SYSTEM_SUFFIX = (
        "\nReturn STRICT JSON only. Always include a numeric field "
        '"confidence" in [0,1] reflecting how sure you are.'
    )

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or default_settings
        self._clients: dict[int, object] = {}
        if not self.settings.use_mock:
            # One LangChain chat model per tier. Lazy import so mock mode never
            # needs langchain installed.
            from langchain_openai import ChatOpenAI

            for spec in self.settings.tiers:
                self._clients[spec.tier] = ChatOpenAI(
                    model=spec.model,
                    api_key=self.settings.openai_api_key,
                    temperature=0.2,
                    timeout=60,
                    max_retries=2,
                    model_kwargs={"response_format": {"type": "json_object"}},
                )

    @property
    def mock(self) -> bool:
        return self.settings.use_mock

    async def complete(
        self,
        tier: TierSpec,
        *,
        system: str,
        user: str,
        mock: MockFn,
        temperature: float = 0.2,
    ) -> LLMResult:
        if self.mock:
            return self._run_mock(tier, system=system, user=user, mock=mock)
        return await self._run_langchain(tier, system=system, user=user)

    # ----- real path (LangChain) -----

    async def _run_langchain(self, tier: TierSpec, *, system: str, user: str) -> LLMResult:
        from langchain_core.messages import HumanMessage, SystemMessage

        client = self._clients[tier.tier]
        resp = await client.ainvoke(  # type: ignore[attr-defined]
            [SystemMessage(content=system + self.SYSTEM_SUFFIX), HumanMessage(content=user)]
        )
        text = resp.content if isinstance(resp.content, str) else json.dumps(resp.content)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"_unparsed": text, "confidence": 0.3}
        confidence = float(data.get("confidence", 0.6))

        usage = getattr(resp, "usage_metadata", None) or {}
        tin = usage.get("input_tokens") or _estimate_tokens(system + user)
        tout = usage.get("output_tokens") or _estimate_tokens(text)
        return LLMResult(
            data=data,
            confidence=max(0.0, min(1.0, confidence)),
            tier=tier.tier,
            model=tier.model,
            tokens_in=tin,
            tokens_out=tout,
            cost_usd=self._cost(tier, tin, tout),
            used_mock=False,
            raw_text=text,
        )

    # ----- mock path -----

    def _run_mock(
        self, tier: TierSpec, *, system: str, user: str, mock: MockFn
    ) -> LLMResult:
        data, confidence = mock(tier.tier)
        text = json.dumps(data, ensure_ascii=False)
        tin = _estimate_tokens(system + user)
        tout = _estimate_tokens(text)
        return LLMResult(
            data=data,
            confidence=max(0.0, min(1.0, confidence)),
            tier=tier.tier,
            model=tier.model,
            tokens_in=tin,
            tokens_out=tout,
            cost_usd=self._cost(tier, tin, tout),
            used_mock=True,
            raw_text=text,
        )

    def _cost(self, tier: TierSpec, tokens_in: int, tokens_out: int) -> float:
        return (tokens_in / 1000) * tier.price_in + (tokens_out / 1000) * tier.price_out
