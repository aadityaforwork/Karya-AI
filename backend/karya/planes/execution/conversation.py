from __future__ import annotations

import re

from ...config import Settings, settings as default_settings
from ...core.models import Language
from ..state.store import StatePlane
from ..trust.verifier import TECH_VOCAB
from .llm import LLMClient, LLMResult
from .router import CostAwareRouter

_GREETING = {
    Language.EN: "Hi",
    Language.HI: "नमस्ते",
    Language.MR: "नमस्कार",
    Language.TE: "నమస్కారం",
}

_TOKEN = re.compile(r"[a-zA-Z][a-zA-Z0-9+#]*(?:\.[a-zA-Z0-9+#]+)*")

# Tokens that are real skills in the verifier vocab but also ordinary English
# words ("the rest", "we're hiring", "let's go"). The conversation guardrail must
# not flag those, or it cries wolf on every other sentence.
_AMBIGUOUS = {
    "go", "rest", "node", "ai", "ml", "series", "retail", "hiring", "b2b", "b2c",
    "saas", "crm", "cloud", "analytics", "lending", "logistics", "express", "bootstrapped",
}
# What the guardrail actually polices: concrete, unmistakable skill claims.
_GUARD_VOCAB = TECH_VOCAB - _AMBIGUOUS

INTENTS = ("interested", "question", "objection", "not_now", "opt_out")

# stage the pipeline should move to once the human sends the suggested reply
STAGE_HINT = {
    "interested": "interview",
    "question": "replied",
    "objection": "replied",
    "not_now": "replied",
    "opt_out": "rejected",
}


def _terms(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN.findall(text)}


def detect_intent(text: str) -> str:
    low = text.lower()
    if any(k in low for k in ("unsubscribe", "not interested", "no thanks", "stop contacting", "remove me", "opt out")):
        return "opt_out"
    if any(k in low for k in ("not right now", "not now", "later", "busy", "next quarter", "circle back", "reach out in")):
        return "not_now"
    if "?" in text or any(k in low for k in ("confirm", "what ", "which ", "does ", "do you", "is it", "is there", "how ", "can you tell")):
        return "question"
    if any(k in low for k in ("but ", "concern", "worried", "only work", "too ", "not sure", "hesitant")):
        return "objection"
    return "interested"


class ConversationAgent:
    """Runs the follow-up conversation on the same trust engine as the first touch.

    Reads an inbound reply, classifies intent, and drafts the next message using
    ONLY facts it can prove: the role spec the user defined and the recipient's
    own verified claims. Anything it cannot ground is dropped before the human
    ever sees it, the same rule the screening verifier enforces, so a conversation
    can never drift into invented commitments.
    """

    def __init__(
        self,
        state: StatePlane,
        router: CostAwareRouter,
        llm: LLMClient,
        settings: Settings | None = None,
    ) -> None:
        self.state = state
        self.router = router
        self.llm = llm
        self.settings = settings or default_settings

    def _allowed(self, role_facts: dict, proven_facts: list[str]) -> set[str]:
        bag = " ".join(
            [role_facts.get("title", ""), role_facts.get("location", "")]
            + role_facts.get("must_have", [])
            + role_facts.get("nice_to_have", [])
            + proven_facts
        )
        return _terms(bag) & TECH_VOCAB

    async def respond(
        self,
        run_id: str,
        *,
        name: str,
        language: Language,
        proven_facts: list[str],
        role_facts: dict,
        history: list[dict],
        inbound: str,
    ) -> dict:
        intent = detect_intent(inbound)
        allowed = self._allowed(role_facts, proven_facts)
        system, user = self._prompt(name, proven_facts, role_facts, history, inbound, intent, allowed)

        async def call(tier_number: int) -> LLMResult:
            spec = self.settings.tier(tier_number)
            return await self.llm.complete(
                spec,
                system=system,
                user=user,
                mock=lambda t: self._mock(name, language, proven_facts, role_facts, inbound, intent, allowed, t),
            )

        result = await self.router.route(run_id, "reply", language, call, label=name)

        body = str(result.data.get("body", "")).strip()
        grounded = [g for g in result.data.get("grounded_on", []) if g]

        # guardrail: a concrete skill the draft asserts that we cannot prove from the
        # role spec or the recipient's verified claims gets flagged. Terms the
        # recipient raised themselves are fine to echo back (including to decline them).
        raised = _terms(inbound)
        dropped = sorted(
            {
                t
                for t in (_terms(body) & _GUARD_VOCAB)
                if t not in allowed and t not in grounded and t not in raised
            }
        )

        return {
            "intent": intent,
            "body": body,
            "grounded_on": grounded,
            "dropped": dropped,
            "stage_hint": STAGE_HINT.get(intent, "replied"),
            "requires_approval": True,
            "confidence": round(result.confidence, 3),
            "tier": result.tier,
            "model": result.model,
            "cost_usd": round(result.cost_usd, 6),
            "mock": result.used_mock,
        }

    # ----- prompt + mock -----

    def _prompt(
        self, name: str, proven_facts: list[str], role_facts: dict,
        history: list[dict], inbound: str, intent: str, allowed: set[str],
    ) -> tuple[str, str]:
        system = (
            "You are a conversation worker handling a reply from a candidate or prospect. "
            "Write the next message in the recipient's language. You may reference ONLY two "
            "sources of truth: the role facts and the recipient's verified facts provided below. "
            "If they ask about anything not in those sources, say plainly that you cannot confirm "
            "it yet and will check, never guess or invent details. Be warm and short. "
            'Output JSON: {intent, body, grounded_on:[strings you relied on], confidence:0..1}.'
        )
        thread = "\n".join(f"{m.get('sender')}: {m.get('body')}" for m in history[-6:])
        user = (
            f"ROLE FACTS: title={role_facts.get('title')}, location={role_facts.get('location')}, "
            f"must_have={role_facts.get('must_have')}, nice_to_have={role_facts.get('nice_to_have')}, "
            f"seniority={role_facts.get('seniority')}.\n"
            f"RECIPIENT: {name}.\n"
            f"VERIFIED FACTS ABOUT THEM: {proven_facts or '(none)'}.\n"
            f"CONVERSATION SO FAR:\n{thread}\n"
            f"THEIR LATEST MESSAGE: {inbound}\n"
            f"DETECTED INTENT: {intent}."
        )
        return system, user

    def _mock(
        self, name: str, language: Language, proven_facts: list[str], role_facts: dict,
        inbound: str, intent: str, allowed: set[str], tier: int,
    ) -> tuple[dict, float]:
        first = name.split()[0] if name else "there"
        greet = _GREETING.get(language, "Hi")
        title = role_facts.get("title") or "the role"
        must = role_facts.get("must_have", [])
        grounded: list[str] = []

        if intent == "opt_out":
            body = f"{greet} {first}, understood. I'll close this out and won't follow up. Thanks for letting me know."
        elif intent == "not_now":
            body = f"{greet} {first}, no problem at all. I'll check back later. If the timing changes, just reply here and we'll pick it up."
        elif intent == "question":
            asked = sorted(_terms(inbound) & TECH_VOCAB)
            confirm = [t for t in asked if t in allowed]
            deny = [t for t in asked if t not in allowed]
            parts: list[str] = []
            if confirm:
                grounded += confirm
                verb = "is" if len(confirm) == 1 else "are"
                parts.append(f"yes, {', '.join(confirm)} {verb} part of this role, it's in the spec we're hiring against.")
            if deny:
                parts.append(f"I can't confirm {', '.join(deny)} is in scope, so I won't claim it: let me check with the team and come back to you.")
            if not confirm and not deny:
                lead = f"this is a {title} role" + (f" centred on {', '.join(must[:2])}" if must else "")
                parts.append(f"{lead}.")
                grounded += [m.lower() for m in must[:2]]
            parts.append("Want to grab 15 minutes this week to go through the rest?")
            body = f"{greet} {first}, " + " ".join(parts)
        elif intent == "objection":
            anchor = proven_facts[0] if proven_facts else f"what we saw in your profile for {title}"
            grounded += [anchor]
            body = (
                f"{greet} {first}, fair point. I'm only reaching out because of something concrete: "
                f"{anchor.rstrip('.').lower()}. If a short call still isn't useful, no pressure at all."
            )
        else:
            grounded += [f"{title} in {role_facts.get('location', '')}".strip()]
            body = (
                f"{greet} {first}, great to hear. Tuesday or Thursday afternoon works on my side: "
                f"I'll send a calendar invite for the {title} conversation. Looking forward to it."
            )

        conf = 0.9 if intent in ("interested", "opt_out", "not_now") else 0.79
        return {"intent": intent, "body": body, "grounded_on": grounded, "confidence": conf}, conf
