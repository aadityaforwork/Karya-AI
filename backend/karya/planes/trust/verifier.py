from __future__ import annotations

import re
from dataclasses import dataclass

from ...core.models import Candidate, Claim, ClaimStatus
from ..state.evidence_store import EvidenceStore

# Skills/companies the verifier treats as "salient": if a claim names one, the
# cited evidence must actually contain it. Tech tokens stay in Latin script even
# inside Hindi/Marathi/Telugu resumes, so this entailment works across languages.
TECH_VOCAB = {
    # engineering signals (hiring)
    "python", "go", "golang", "java", "rust", "node.js", "node", "django",
    "spring", "kafka", "kubernetes", "k8s", "docker", "aws", "gcp", "azure",
    "postgresql", "postgres", "mysql", "mongodb", "redis", "grpc", "rest",
    "react", "typescript", "microservices", "payments", "upi", "razorpay",
    "distributed-systems", "express",
    # business signals (sales)
    "fintech", "healthtech", "ecommerce", "saas", "b2b", "b2c", "lending",
    "logistics", "retail", "hiring", "series", "ai", "ml", "crm", "cloud",
    "analytics", "bootstrapped",
}

# A token is a word, optionally with internal dots/plus/hash (node.js, c++, c#),
# but a trailing period (sentence punctuation) is NOT consumed.
_TOKEN = re.compile(r"[a-zA-Z][a-zA-Z0-9+#]*(?:\.[a-zA-Z0-9+#]+)*")

# Words too generic to count as evidence of anything in the overlap fallback.
_STOPWORDS = {
    "has", "have", "with", "and", "the", "experience", "hands", "exposure",
    "worked", "using", "built", "for", "from", "this", "that", "candidate",
}


@dataclass
class VerifyResult:
    ok: bool
    reason: str


class Verifier:
    """Rejects any claim not entailed by real, cited evidence.

    This is the mechanism behind "it physically can't make things up": a worker's
    claim is dropped unless the exact lines it points to actually support it.
    """

    def __init__(self, evidence: EvidenceStore) -> None:
        self.evidence = evidence

    def verify(self, candidate: Candidate, claim: Claim) -> VerifyResult:
        if not claim.evidence_lines:
            return VerifyResult(False, "no citation")

        cited_tokens: set[str] = set()
        for n in claim.evidence_lines:
            line = self.evidence.get(candidate.id, n)
            if line is None:
                return VerifyResult(False, f"phantom citation: line {n} does not exist")
            cited_tokens |= {t.lower() for t in _TOKEN.findall(line.text)}

        claim_terms = {t.lower() for t in _TOKEN.findall(claim.text)}
        salient = claim_terms & TECH_VOCAB
        if salient:
            missing = [t for t in salient if t not in cited_tokens]
            if missing:
                return VerifyResult(
                    False, f"not entailed: {', '.join(sorted(missing))} absent from cited lines"
                )
            return VerifyResult(True, f"entailed by line(s) {claim.evidence_lines}")

        # No vocab term to anchor on: fall back to overlap of meaningful words.
        content = {t for t in claim_terms if len(t) > 3 and t not in _STOPWORDS}
        if not content:
            return VerifyResult(True, f"trivially grounded in line(s) {claim.evidence_lines}")
        overlap = len(content & cited_tokens) / len(content)
        if overlap >= 0.5:
            return VerifyResult(True, f"supported ({overlap:.0%} overlap)")
        return VerifyResult(False, f"weak support ({overlap:.0%} overlap)")

    def apply(self, candidate: Candidate, claim: Claim) -> Claim:
        """Stamp the claim verified/rejected in place and return it."""
        result = self.verify(candidate, claim)
        claim.status = ClaimStatus.VERIFIED if result.ok else ClaimStatus.REJECTED
        claim.reason = result.reason
        return claim
