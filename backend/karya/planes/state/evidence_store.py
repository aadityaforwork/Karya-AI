from __future__ import annotations

from ...core.models import Candidate, ResumeLine


class EvidenceStore:
    """Holds the only thing a claim is allowed to cite: real source lines.

    A claim that points at a line not in here cannot be verified, so the
    verifier has no way to "believe" a fabricated citation.
    """

    def __init__(self) -> None:
        # candidate_id -> {line_no -> ResumeLine}
        self._lines: dict[str, dict[int, ResumeLine]] = {}

    def ingest_candidate(self, candidate: Candidate) -> None:
        self._lines[candidate.id] = {line.n: line for line in candidate.resume}

    def get(self, subject_id: str, line_no: int) -> ResumeLine | None:
        return self._lines.get(subject_id, {}).get(line_no)

    def lines(self, subject_id: str) -> list[ResumeLine]:
        return sorted(self._lines.get(subject_id, {}).values(), key=lambda l: l.n)

    def search(self, subject_id: str, terms: list[str]) -> list[ResumeLine]:
        """Cheap lexical retrieval over a candidate's resume lines."""
        needles = [t.lower() for t in terms if t.strip()]
        hits: list[tuple[int, ResumeLine]] = []
        for line in self.lines(subject_id):
            score = sum(1 for t in needles if t in line.text.lower())
            if score:
                hits.append((score, line))
        hits.sort(key=lambda x: (-x[0], x[1].n))
        return [line for _, line in hits]
