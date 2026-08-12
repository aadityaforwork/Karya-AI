from __future__ import annotations

import re
import unicodedata
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

# Any run of digits, in any script (5, ५, ౫).
_NUMBER = re.compile(r"\d+", re.UNICODE)


def _is_word_char(ch: str) -> bool:
    """Whether a character belongs inside a word, in any script.

    `\\w` is not enough: Devanagari and Telugu vowel signs are combining marks
    (category M), so `\\w` splits तयार into तय and र. Tokenising that way left
    non-Latin claims with no words long enough to check, which is how they
    slipped past verification entirely.
    """
    if ch in "+#":  # c++, c#
        return True
    return unicodedata.category(ch)[0] in "LNM"


def _tokenize(text: str) -> list[str]:
    """Words in any script, keeping tech spellings (node.js) in one piece.

    A dot is kept only between word characters, so a sentence-ending period is
    never swallowed into the token before it.
    """
    out: list[str] = []
    cur: list[str] = []
    for i, ch in enumerate(text):
        if _is_word_char(ch):
            cur.append(ch)
        elif ch == "." and cur and i + 1 < len(text) and _is_word_char(text[i + 1]):
            cur.append(ch)
        elif cur:
            out.append("".join(cur))
            cur = []
    if cur:
        out.append("".join(cur))
    return out

# Words too generic to count as evidence of anything in the overlap fallback.
# The Devanagari/Telugu entries are the equivalents of and/in/with/of.
_STOPWORDS = {
    "has", "have", "with", "and", "the", "experience", "hands", "exposure",
    "worked", "using", "built", "for", "from", "this", "that", "candidate",
    "आणि", "और", "में", "मध्ये", "साठी", "करून", "वापरून", "का", "की", "के",
    "మరియు", "కోసం", "తో", "లో",
}


def _ascii_digits(text: str) -> str:
    """Fold every Unicode decimal digit to its ASCII form so ५ and 5 compare equal."""
    return "".join(str(unicodedata.digit(ch)) if ch.isdigit() else ch for ch in text)


def _words(text: str) -> set[str]:
    """Lowercased word tokens, in any script, excluding bare numbers."""
    return {t.lower() for t in _tokenize(text) if not t.isdigit()}


def _numbers(text: str) -> set[str]:
    """Quantities asserted by a piece of text, script-normalised."""
    return set(_NUMBER.findall(_ascii_digits(text)))


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
        cited_numbers: set[str] = set()
        for n in claim.evidence_lines:
            line = self.evidence.get(candidate.id, n)
            if line is None:
                return VerifyResult(False, f"phantom citation: line {n} does not exist")
            cited_tokens |= _words(line.text)
            cited_numbers |= _numbers(line.text)

        # Quantities first, and regardless of which path below applies: a claim
        # may name a skill the evidence really does support while inflating the
        # number attached to it ("10 years of Kubernetes" over a line that says
        # six). Checking the skill alone let that through.
        invented = _numbers(claim.text) - cited_numbers
        if invented:
            return VerifyResult(
                False,
                f"not entailed: {', '.join(sorted(invented, key=int))} not supported by cited lines",
            )

        claim_terms = _words(claim.text)
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
            # Nothing checkable. This used to return verified ("trivially
            # grounded"), which is how a fabricated non-Latin claim passed: it
            # tokenised to nothing, so nothing was ever compared.
            return VerifyResult(False, "nothing verifiable in the claim")
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
