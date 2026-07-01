from __future__ import annotations

import json

from ...config import Settings, settings as default_settings
from ...core.events import EventType, Level
from ...core.models import (
    Candidate,
    Claim,
    ClaimStatus,
    Job,
    Language,
    OutreachDraft,
    ScreeningResult,
)
from ..state.store import StatePlane
from ..trust.verifier import TECH_VOCAB, Verifier
from .llm import LLMClient, LLMResult
from .router import CostAwareRouter
from .sandbox import ToolSandbox

_GREETING = {
    Language.EN: "Hi",
    Language.HI: "नमस्ते",
    Language.MR: "नमस्कार",
    Language.TE: "నమస్కారం",
}


def mock_confidence(language: Language, tier: int, fit: float) -> float:
    """Deterministic stand-in for a model's self-reported confidence.

    Falls with harder languages and rises with tier, so escalation actually buys
    accuracy - which is the whole reason the gate exists. Borderline fit also
    lowers certainty, producing the 'hard candidate escalates' case from the deck.
    """
    base = {Language.EN: 0.90, Language.HI: 0.84, Language.MR: 0.60, Language.TE: 0.60}[language]
    boost = {0: 0.0, 1: 0.12, 2: 0.22}[tier]
    penalty = max(0.0, 0.25 * (1 - 2 * abs(fit - 0.5)))
    return round(max(0.05, min(0.98, base + boost - penalty)), 3)


def _skill_in_claim(text: str) -> str | None:
    low = text.lower()
    for skill in sorted(TECH_VOCAB, key=len, reverse=True):
        if skill in low:
            return skill
    return None


class SourcingAgent:
    def __init__(self, state: StatePlane, sandbox: ToolSandbox) -> None:
        self.state = state
        self.sandbox = sandbox

    def source(self, run_id: str, job: Job, limit: int) -> list[Candidate]:
        candidates = self.sandbox.search_talent_pool(run_id, job, limit)
        for c in candidates:
            self.state.emit(
                run_id,
                EventType.CANDIDATE_SOURCED,
                f"sourced {c.name} - {c.headline}, {c.location} ({c.language.value})",
                {"candidate_id": c.id, "name": c.name, "location": c.location, "language": c.language.value},
            )
        return candidates


class ScreeningAgent:
    """Scores a candidate against a job and grounds every claim in evidence."""

    def __init__(
        self,
        state: StatePlane,
        router: CostAwareRouter,
        llm: LLMClient,
        verifier: Verifier,
        settings: Settings | None = None,
    ) -> None:
        self.state = state
        self.router = router
        self.llm = llm
        self.verifier = verifier
        self.settings = settings or default_settings

    async def screen(self, run_id: str, candidate: Candidate, job: Job) -> ScreeningResult:
        system, user = self._prompt(candidate, job)

        async def call(tier_number: int) -> LLMResult:
            spec = self.settings.tier(tier_number)
            return await self.llm.complete(
                spec,
                system=system,
                user=user,
                mock=lambda t: self._mock(candidate, job, t),
            )

        result = await self.router.route(
            run_id, "screen", candidate.language, call, label=candidate.name
        )

        verified = self._ground_claims(run_id, candidate, result.data.get("claims", []))
        fit, verdict = self._score(candidate, job, verified)
        screening = ScreeningResult(
            candidate_id=candidate.id,
            fit_score=fit,
            verdict=verdict,
            claims=verified,
            rationale=result.data.get("rationale", ""),
        )
        self.state.entities.set_screening(screening)
        self.state.emit(
            run_id,
            EventType.CANDIDATE_SCREENED,
            f"screened {candidate.name}: fit {fit:.0%}, {verdict} ({len([c for c in verified if c.status==ClaimStatus.VERIFIED])} proven claims)",
            {
                "candidate_id": candidate.id,
                "fit_score": round(fit, 3),
                "verdict": verdict,
                "verified": [c.text for c in verified if c.status == ClaimStatus.VERIFIED],
                "rejected": [c.text for c in verified if c.status == ClaimStatus.REJECTED],
            },
            level=Level.SUCCESS if verdict == "advance" else Level.INFO,
        )
        return screening

    def _ground_claims(self, run_id: str, candidate: Candidate, raw_claims: list[dict]) -> list[Claim]:
        out: list[Claim] = []
        for rc in raw_claims:
            claim = Claim(
                subject_id=candidate.id,
                text=rc.get("text", ""),
                evidence_lines=list(rc.get("evidence_lines", [])),
            )
            self.state.emit(
                run_id,
                EventType.CLAIM_PROPOSED,
                f"claim: {claim.text} (cites line {claim.evidence_lines})",
                {"candidate_id": candidate.id, "claim": claim.text, "lines": claim.evidence_lines},
            )
            res = self.verifier.verify(candidate, claim)
            if not res.ok:
                # bounce: try to re-retrieve the right evidence and resubmit once
                skill = _skill_in_claim(claim.text)
                hits = self.state.evidence.search(candidate.id, [skill]) if skill else []
                if hits and hits[0].n not in claim.evidence_lines:
                    self.state.emit(
                        run_id,
                        EventType.EVIDENCE_RETRIEVED,
                        f"bounced ({res.reason}) - re-retrieved line {hits[0].n} for '{skill}'",
                        {"candidate_id": candidate.id, "claim": claim.text, "line": hits[0].n},
                    )
                    claim.evidence_lines = [hits[0].n]
                    res = self.verifier.verify(candidate, claim)

            claim.status = ClaimStatus.VERIFIED if res.ok else ClaimStatus.REJECTED
            claim.reason = res.reason
            if res.ok:
                self.state.emit(
                    run_id,
                    EventType.CLAIM_VERIFIED,
                    f"verified: {claim.text} <- {res.reason}",
                    {"candidate_id": candidate.id, "claim": claim.text, "lines": claim.evidence_lines},
                )
            else:
                self.state.emit(
                    run_id,
                    EventType.CLAIM_REJECTED,
                    f"rejected: {claim.text} <- {res.reason}",
                    {"candidate_id": candidate.id, "claim": claim.text, "reason": res.reason},
                )
            out.append(claim)
        return out

    def _score(self, candidate: Candidate, job: Job, claims: list[Claim]) -> tuple[float, str]:
        proven = {
            _skill_in_claim(c.text)
            for c in claims
            if c.status == ClaimStatus.VERIFIED and _skill_in_claim(c.text)
        }
        must = {s.lower() for s in job.must_have}
        nice = {s.lower() for s in job.nice_to_have}
        must_hit = len(must & proven) / max(1, len(must))
        nice_hit = len(nice & proven) / len(nice) if nice else 0.0
        loc = 1.0 if candidate.location.lower() == job.location.lower() else 0.0
        fit = 0.6 * must_hit + 0.25 * nice_hit + 0.15 * loc
        verdict = "advance" if fit >= 0.6 else "hold" if fit >= 0.4 else "reject"
        return round(fit, 3), verdict

    # ----- prompt + mock for the screen task -----

    def _prompt(self, candidate: Candidate, job: Job) -> tuple[str, str]:
        system = (
            "You are a screening worker. Assess the candidate against the job. "
            "For each required/nice-to-have skill, emit a claim citing the resume "
            "line numbers that prove it. Never cite a line that does not support the "
            "claim. Output JSON: {claims:[{text, evidence_lines:[int]}], fit_score:0..1, "
            "verdict:'advance'|'hold'|'reject', rationale, confidence:0..1}."
        )
        resume = "\n".join(f"[{l.n}] {l.text}" for l in candidate.resume)
        user = (
            f"JOB: {job.title} in {job.location}; must-have={job.must_have}; "
            f"nice-to-have={job.nice_to_have}.\n"
            f"CANDIDATE: {candidate.name}, {candidate.location}, lang={candidate.language.value}.\n"
            f"RESUME:\n{resume}"
        )
        return system, user

    def _mock(self, candidate: Candidate, job: Job, tier: int) -> tuple[dict, float]:
        is_sales = job.pool == "prospects"
        must_tpl = "Operates in {s}." if is_sales else "Has hands-on experience with {s}."
        nice_tpl = "Shows signal: {s}." if is_sales else "Has exposure to {s}."
        claims: list[dict] = []
        # First-pass citations are naive (line 1) so the verifier has to ground them.
        for skill in job.must_have:
            claims.append({"text": must_tpl.format(s=skill), "evidence_lines": [1]})
        for skill in job.nice_to_have:
            hits = self.state.evidence.search(candidate.id, [skill])
            claims.append(
                {"text": nice_tpl.format(s=skill), "evidence_lines": [hits[0].n if hits else 1]}
            )
        have = {s.lower() for s in candidate.skills}
        must = {s.lower() for s in job.must_have}
        prov_fit = 0.7 * (len(must & have) / max(1, len(must))) + (
            0.3 if candidate.location.lower() == job.location.lower() else 0.0
        )
        conf = mock_confidence(candidate.language, tier, prov_fit)
        return (
            {
                "claims": claims,
                "fit_score": round(prov_fit, 3),
                "verdict": "advance" if prov_fit >= 0.6 else "hold",
                "rationale": f"{len(must & have)}/{len(must)} must-have skills present.",
                "confidence": conf,
            },
            conf,
        )


class OutreachAgent:
    """Drafts a personalised message that cites only proven facts."""

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

    async def draft(
        self, run_id: str, candidate: Candidate, job: Job, proven: list[Claim]
    ) -> OutreachDraft:
        system, user = self._prompt(candidate, job, proven)

        async def call(tier_number: int) -> LLMResult:
            spec = self.settings.tier(tier_number)
            return await self.llm.complete(
                spec,
                system=system,
                user=user,
                mock=lambda t: self._mock(candidate, job, proven, t),
            )

        result = await self.router.route(
            run_id, "draft", candidate.language, call, label=candidate.name
        )
        draft = OutreachDraft(
            candidate_id=candidate.id,
            language=candidate.language,
            subject=result.data.get("subject", f"{job.title} opportunity"),
            body=result.data.get("body", ""),
            cited_claims=[c for c in proven if c.status == ClaimStatus.VERIFIED],
        )
        self.state.entities.add_draft(draft)
        self.state.emit(
            run_id,
            EventType.OUTREACH_DRAFTED,
            f"drafted {draft.language.value} message to {candidate.name} ({len(draft.cited_claims)} cited facts)",
            {
                "candidate_id": candidate.id,
                "subject": draft.subject,
                "body": draft.body,
                "cited_facts": [c.text for c in draft.cited_claims],
            },
        )
        return draft

    def _prompt(self, candidate: Candidate, job: Job, proven: list[Claim]) -> tuple[str, str]:
        facts = "; ".join(c.text for c in proven if c.status == ClaimStatus.VERIFIED)
        system = (
            "You are an outreach worker. Write a short, warm outreach message in the "
            "recipient's language. Reference ONLY the proven facts provided; invent nothing. "
            "Output JSON: {subject, body, confidence:0..1}."
        )
        user = (
            f"CANDIDATE: {candidate.name}, lang={candidate.language.value}.\n"
            f"ROLE: {job.title} in {job.location}.\n"
            f"PROVEN FACTS: {facts or '(none)'}"
        )
        return system, user

    def _mock(
        self, candidate: Candidate, job: Job, proven: list[Claim], tier: int
    ) -> tuple[dict, float]:
        verified = [c for c in proven if c.status == ClaimStatus.VERIFIED]
        signals = [s for c in verified if (s := _skill_in_claim(c.text))][:3]
        proof = ", ".join(dict.fromkeys(signals)) or "your work"
        first = candidate.name.split()[0]
        greet = _GREETING[candidate.language]
        if job.pool == "prospects":
            subject = f"{job.title} - quick intro?"
            body = (
                f"{greet} {first}, we came across your team and noticed your work in {proof}. "
                f"We work with similar teams and thought there might be a strong fit. "
                f"Open to a 15-min call this week?"
            )
        else:
            subject = f"{job.title} role - quick chat?"
            body = (
                f"{greet} {first}, we're hiring a {job.title} in {job.location}. "
                f"Your profile shows strong {proof}, exactly what we need. "
                f"Open to a 15-min call this week?"
            )
        conf = mock_confidence(candidate.language, tier, 0.8)
        return {"subject": subject, "body": body, "confidence": conf}, conf
