from karya.core.models import Candidate, Claim, Language, ResumeLine
from karya.planes.state.evidence_store import EvidenceStore
from karya.planes.trust.verifier import Verifier


def _cand() -> Candidate:
    return Candidate(
        id="c1", name="Test", headline="Backend Engineer", location="Pune",
        language=Language.EN, years_experience=5, skills=["Python"],
        resume=[
            ResumeLine(n=1, text="Backend Engineer in Pune with 5 years of experience."),
            ResumeLine(n=2, text="Built REST APIs in Python and Django."),
        ],
    )


def _verifier(cand: Candidate) -> Verifier:
    store = EvidenceStore()
    store.ingest_candidate(cand)
    return Verifier(store)


def test_skill_claim_rejected_when_line_lacks_skill():
    cand = _cand()
    v = _verifier(cand)
    claim = Claim(subject_id="c1", text="Has hands-on experience with Python.", evidence_lines=[1])
    assert v.verify(cand, claim).ok is False  # line 1 never mentions Python


def test_skill_claim_verified_when_line_has_skill():
    cand = _cand()
    v = _verifier(cand)
    claim = Claim(subject_id="c1", text="Has hands-on experience with Python.", evidence_lines=[2])
    assert v.verify(cand, claim).ok is True  # line 2 says Python


def test_phantom_citation_rejected():
    cand = _cand()
    v = _verifier(cand)
    claim = Claim(subject_id="c1", text="Has hands-on experience with Python.", evidence_lines=[99])
    res = v.verify(cand, claim)
    assert res.ok is False and "phantom" in res.reason


def test_uncited_claim_rejected():
    cand = _cand()
    v = _verifier(cand)
    claim = Claim(subject_id="c1", text="Has hands-on experience with Python.", evidence_lines=[])
    assert v.verify(cand, claim).ok is False
