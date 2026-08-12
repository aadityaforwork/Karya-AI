from karya.core.models import Candidate, Claim, Language, ResumeLine
from karya.planes.state.evidence_store import EvidenceStore
from karya.planes.trust.verifier import Verifier, _numbers, _tokenize


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


# ----- quantities -----


def test_inflated_years_rejected():
    """The skill is real; the number attached to it is not."""
    cand = _cand()
    v = _verifier(cand)
    claim = Claim(subject_id="c1", text="Has 10 years of experience.", evidence_lines=[1])
    res = v.verify(cand, claim)
    assert res.ok is False and "10" in res.reason


def test_inflated_years_rejected_even_when_the_skill_checks_out():
    """Line 2 really does say Python, which used to be enough to pass the claim
    whole - number included."""
    cand = _cand()
    v = _verifier(cand)
    claim = Claim(subject_id="c1", text="Has 10 years of Python.", evidence_lines=[2])
    assert v.verify(cand, claim).ok is False


def test_honest_number_verified():
    cand = _cand()
    v = _verifier(cand)
    claim = Claim(subject_id="c1", text="Has 5 years of experience.", evidence_lines=[1])
    assert v.verify(cand, claim).ok is True


# ----- non-Latin scripts -----


def _mr_cand() -> Candidate:
    return Candidate(
        id="c_mr", name="Rohit Deshmukh", headline="Backend Engineer", location="Pune",
        language=Language.MR, years_experience=6, skills=["Java", "Spring"],
        resume=[
            ResumeLine(n=1, text="पुण्यात राहणारा बॅकएंड अभियंता, ६ वर्षांचा अनुभव."),
            ResumeLine(n=2, text="Java आणि Spring Boot वापरून मायक्रोसर्व्हिसेस तयार केले."),
        ],
    )


def _te_cand() -> Candidate:
    return Candidate(
        id="c_te", name="Lakshmi Reddy", headline="Backend Engineer", location="Pune",
        language=Language.TE, years_experience=5, skills=["Python", "Django"],
        resume=[
            ResumeLine(n=1, text="పూణేలో ఉంటున్న బ్యాకెండ్ ఇంజనీర్, 5 సంవత్సరాల అనుభవం."),
            ResumeLine(n=2, text="Python మరియు Django తో REST APIలను నిర్మించారు."),
        ],
    )


def test_fabricated_marathi_claim_rejected():
    """The whole multilingual story lived in this gap: a Devanagari claim
    tokenised to nothing, so nothing was ever compared and it passed."""
    cand = _mr_cand()
    v = _verifier(cand)
    claim = Claim(subject_id="c_mr", text="आर्थिक क्षेत्रात काम केले आहे.", evidence_lines=[2])
    assert v.verify(cand, claim).ok is False


def test_genuine_marathi_claim_verified():
    cand = _mr_cand()
    v = _verifier(cand)
    claim = Claim(subject_id="c_mr", text="मायक्रोसर्व्हिसेस तयार केले.", evidence_lines=[2])
    assert v.verify(cand, claim).ok is True


def test_fabricated_telugu_claim_rejected():
    cand = _te_cand()
    v = _verifier(cand)
    claim = Claim(subject_id="c_te", text="ఆర్థిక రంగంలో పనిచేశారు.", evidence_lines=[2])
    assert v.verify(cand, claim).ok is False


def test_genuine_telugu_claim_verified():
    cand = _te_cand()
    v = _verifier(cand)
    claim = Claim(subject_id="c_te", text="5 సంవత్సరాల అనుభవం.", evidence_lines=[1])
    assert v.verify(cand, claim).ok is True


def test_latin_skill_inside_devanagari_resume_still_grounds():
    """Tech tokens stay Latin inside Indic resumes - that must keep working."""
    cand = _mr_cand()
    v = _verifier(cand)
    assert v.verify(cand, Claim(subject_id="c_mr", text="Has hands-on experience with Java.", evidence_lines=[2])).ok
    assert not v.verify(cand, Claim(subject_id="c_mr", text="Has hands-on experience with Kafka.", evidence_lines=[2])).ok


def test_devanagari_digits_compare_with_ascii():
    """Line 1 says ६; a claim saying 6 means the same thing, 8 does not."""
    cand = _mr_cand()
    v = _verifier(cand)
    assert v.verify(cand, Claim(subject_id="c_mr", text="६ वर्षांचा अनुभव.", evidence_lines=[1])).ok
    assert not v.verify(cand, Claim(subject_id="c_mr", text="८ वर्षांचा अनुभव.", evidence_lines=[1])).ok
    assert "6" in _numbers("६ वर्षांचा अनुभव")


def test_contentless_claim_no_longer_auto_passes():
    cand = _cand()
    v = _verifier(cand)
    claim = Claim(subject_id="c1", text="Has experience.", evidence_lines=[1])
    assert v.verify(cand, claim).ok is False


# ----- tokenizer -----


def test_tokenizer_keeps_words_whole_across_scripts():
    # \w splits these on the combining vowel signs; the category-based scan does not
    assert _tokenize("तयार केले") == ["तयार", "केले"]
    assert _tokenize("సంవత్సరాల అనుభవం") == ["సంవత్సరాల", "అనుభవం"]


def test_tokenizer_preserves_tech_spellings():
    assert _tokenize("node.js and Python.") == ["node.js", "and", "Python"]
    assert _tokenize("c++ / c#") == ["c++", "c#"]
