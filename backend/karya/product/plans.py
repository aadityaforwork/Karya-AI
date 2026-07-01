"""Subscription plans. Limits are enforced (workspaces, skills); usage is tracked
and shown. Payment is mocked - subscribing just sets the plan - but the shape is
ready for a real processor (Stripe) to slot in behind /api/billing/subscribe."""

from __future__ import annotations

PLANS: dict[str, dict] = {
    "free": {
        "id": "free", "name": "Free", "price_usd": 0, "price_inr": 0,
        "tagline": "Try the workforce on one role.",
        "workspaces": 1, "runs_per_month": 10, "skills": ["hiring"],
        "features": [
            "1 workspace", "Hiring skill", "Evidence-grounded screening",
            "Cost-aware routing", "Human approval gate", "Community support",
        ],
    },
    "pro": {
        "id": "pro", "name": "Pro", "price_usd": 49, "price_inr": 3999,
        "tagline": "For recruiters and SDRs running many goals.",
        "workspaces": 10, "runs_per_month": 300, "skills": ["hiring", "sales"],
        "features": [
            "10 workspaces", "Hiring + Sales outreach", "Full pipeline + inbox",
            "Language-aware routing", "Priority model tiers", "Email support",
        ],
    },
    "business": {
        "id": "business", "name": "Business", "price_usd": 199, "price_inr": 15999,
        "tagline": "For teams running the whole funnel on autopilot.",
        "workspaces": -1, "runs_per_month": -1, "skills": ["hiring", "sales", "support", "research"],
        "features": [
            "Unlimited workspaces", "All skills incl. Support + Research",
            "Unlimited runs", "Team seats", "Audit export", "Dedicated support",
        ],
    },
}

ORDER = ["free", "pro", "business"]


def plan(plan_id: str) -> dict:
    return PLANS.get(plan_id, PLANS["free"])


def skill_allowed(plan_id: str, skill_id: str) -> bool:
    return skill_id in plan(plan_id)["skills"]


def workspace_limit(plan_id: str) -> int:
    return plan(plan_id)["workspaces"]


def can_add_workspace(plan_id: str, current_count: int) -> bool:
    limit = workspace_limit(plan_id)
    return limit < 0 or current_count < limit
