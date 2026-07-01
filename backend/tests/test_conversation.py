import asyncio

from karya.config import Settings
from karya.engine import KaryaEngine
from karya.planes.execution.conversation import detect_intent


def mock_engine() -> KaryaEngine:
    s = Settings()
    s.openai_api_key = ""
    s.force_mock = True
    return KaryaEngine(s)


ROLE = {
    "title": "Backend Engineer", "location": "Pune",
    "must_have": ["Python", "Kubernetes"], "nice_to_have": ["Go", "payments"],
    "seniority": "senior",
}
PROVEN = ["Has hands-on experience with Python.", "Has hands-on experience with Kubernetes."]


def _suggest(inbound: str) -> dict:
    eng = mock_engine()
    return asyncio.run(
        eng.suggest_reply(
            pc_id="pc1", name="Priya Sharma", language="en",
            proven_facts=PROVEN, role_facts=ROLE, history=[], inbound=inbound,
        )
    )


def test_intent_detection():
    assert detect_intent("Please unsubscribe me") == "opt_out"
    assert detect_intent("Does this role use Kubernetes?") == "question"
    assert detect_intent("Yes, happy to talk") == "interested"
    assert detect_intent("Let's circle back next quarter") == "not_now"


def test_confirms_only_facts_in_the_role_spec():
    s = _suggest("Does this role use Kubernetes, and is there any Rust on the team?")
    body = s["body"].lower()
    # Kubernetes is in the spec -> confirmed and grounded
    assert "kubernetes" in s["grounded_on"]
    assert "kubernetes" in body
    # Rust is not in the spec -> openly refused, never asserted
    assert "rust" not in s["grounded_on"]
    assert "can't confirm rust" in body or "cannot confirm rust" in body


def test_guardrail_has_no_false_positives_on_plain_english():
    # "the rest", "we're hiring" must not be reported as unproven skill claims
    s = _suggest("Does this role use Kubernetes day to day?")
    assert s["dropped"] == []


def test_interested_advances_to_interview():
    s = _suggest("Yes, I'd be open to a quick call this week.")
    assert s["intent"] == "interested"
    assert s["stage_hint"] == "interview"


def test_optout_routes_to_rejected():
    s = _suggest("Not interested, please remove me.")
    assert s["intent"] == "opt_out"
    assert s["stage_hint"] == "rejected"
