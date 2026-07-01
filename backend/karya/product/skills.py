"""The platform's catalogue of skills. Each skill is a goal-driven workflow that
runs on the same engine (router, verifier, approvals, state) but over a different
data pool, with its own vocabulary. Hiring and Sales are live; others are stubs
that prove the platform generalises."""

from __future__ import annotations

SKILLS: dict[str, dict] = {
    "hiring": {
        "id": "hiring",
        "name": "Hiring",
        "tagline": "Source, screen with proof, reach out, and book calls.",
        "active": True,
        "pool": "talent",
        "entity": "candidate",
        "entity_plural": "candidates",
        "spec": "role",
        "spec_plural": "roles",
        "accent": "mint",
        "stage_labels": {"screened": "Screened", "interview": "Interview", "offer": "Offer", "rejected": "Rejected"},
        "default_spec": {
            "title": "Backend Engineer", "location": "Pune", "headcount": 2,
            "must_have": ["Python", "Kubernetes"], "nice_to_have": ["Go", "payments", "PostgreSQL"],
            "seniority": "senior",
        },
    },
    "sales": {
        "id": "sales",
        "name": "Sales outreach",
        "tagline": "Find accounts that fit your ICP, qualify with proof, reach out.",
        "active": True,
        "pool": "prospects",
        "entity": "prospect",
        "entity_plural": "prospects",
        "spec": "campaign",
        "spec_plural": "campaigns",
        "accent": "sky",
        "stage_labels": {"screened": "Qualified", "interview": "Meeting", "offer": "Won", "rejected": "Disqualified"},
        "default_spec": {
            "title": "Fintech engineering leaders", "location": "Bengaluru", "headcount": 2,
            "must_have": ["fintech", "hiring"], "nice_to_have": ["AWS", "payments", "Series B"],
            "seniority": "decision-maker",
        },
    },
    "support": {
        "id": "support", "name": "Support triage", "tagline": "Resolve tickets with cited answers, escalate the rest.",
        "active": False, "pool": "tickets", "entity": "ticket", "entity_plural": "tickets",
        "spec": "queue", "spec_plural": "queues", "accent": "amber", "stage_labels": {}, "default_spec": {},
    },
    "research": {
        "id": "research", "name": "Research", "tagline": "Compile briefs from sources, every claim cited.",
        "active": False, "pool": "docs", "entity": "finding", "entity_plural": "findings",
        "spec": "brief", "spec_plural": "briefs", "accent": "slate", "stage_labels": {}, "default_spec": {},
    },
}


def skill(skill_id: str) -> dict:
    return SKILLS.get(skill_id, SKILLS["hiring"])


def list_skills() -> list[dict]:
    return list(SKILLS.values())


def goal_text(skill_id: str, title: str, headcount: int, location: str) -> str:
    plural = "s" if headcount != 1 else ""
    if skill_id == "sales":
        return f"Reach {headcount} prospect{plural} matching '{title}' in {location}"
    return f"Hire {headcount} {title}{plural} in {location}"
