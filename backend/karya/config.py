import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class TierSpec:
    """One rung of the cost-aware ladder."""

    tier: int
    model: str
    # USD per 1K tokens (input, output). Rough public list prices; used for cost accounting.
    price_in: float
    price_out: float
    # Whether the confidence gate applies. The top tier has no gate (nothing above it).
    gated: bool


@dataclass
class Settings:
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    force_mock: bool = field(default_factory=lambda: _bool("KARYA_FORCE_MOCK", False))
    gate_tau: float = field(default_factory=lambda: float(os.getenv("KARYA_GATE_TAU", "0.72")))

    tier0_model: str = field(default_factory=lambda: os.getenv("KARYA_TIER0_MODEL", "gpt-4o-mini"))
    tier1_model: str = field(default_factory=lambda: os.getenv("KARYA_TIER1_MODEL", "gpt-4o"))
    tier2_model: str = field(default_factory=lambda: os.getenv("KARYA_TIER2_MODEL", "gpt-4o"))

    @property
    def use_mock(self) -> bool:
        return self.force_mock or not self.openai_api_key

    @property
    def tiers(self) -> list[TierSpec]:
        return [
            TierSpec(0, self.tier0_model, price_in=0.00015, price_out=0.0006, gated=True),
            TierSpec(1, self.tier1_model, price_in=0.0025, price_out=0.01, gated=True),
            TierSpec(2, self.tier2_model, price_in=0.0025, price_out=0.01, gated=False),
        ]

    def tier(self, n: int) -> TierSpec:
        return self.tiers[max(0, min(n, len(self.tiers) - 1))]


settings = Settings()
