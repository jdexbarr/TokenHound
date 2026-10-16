"""Core data model shared by every pipeline stage (spec section 5).

Only :class:`Candidate` holds a raw secret, and only in memory. :class:`Finding` is built from a
candidate by masking the value and hashing it, so reporters never see the full secret.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from tokenhound.utils.fingerprint import fingerprint
from tokenhound.utils.masking import mask


class Severity(StrEnum):
    """How bad a leak of this secret type is, as declared by its rule."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def rank(self) -> int:
        """Numeric order for sorting: higher is more severe."""
        return _SEVERITY_RANK[self]


_SEVERITY_RANK = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2, Severity.CRITICAL: 3}


@dataclass(frozen=True, slots=True)
class Chunk:
    """A piece of text to scan.

    ``line_no`` is the 1-based line number of the first line of ``text`` within ``path``.
    ``commit`` is ``None`` when the text comes from the working tree.
    """

    path: str
    commit: str | None
    line_no: int
    text: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class Candidate:
    """A possible secret produced by a detector.

    ``match`` is the raw secret value and ``span`` its ``(start, end)`` offsets within
    ``chunk.text``. Both are excluded from ``repr`` so a stray log line cannot leak them.
    ``severity`` and ``remediation`` come from the rule that fired (the detector may raise the
    severity, e.g. for privileged JWTs).
    """

    rule_id: str
    match: str = field(repr=False)
    span: tuple[int, int]
    chunk: Chunk
    severity: Severity
    remediation: str = field(repr=False)

    @property
    def line_no(self) -> int:
        """1-based line number of the start of the match within the file."""
        return self.chunk.line_no + self.chunk.text.count("\n", 0, self.span[0])


@dataclass(frozen=True, slots=True)
class Finding:
    """A reported secret. Never contains the full value (spec section 5, p.5)."""

    rule_id: str
    file_path: str
    line_no: int
    commit_sha: str | None
    masked_value: str
    fingerprint: str
    score: float
    severity: Severity
    remediation: str

    @classmethod
    def from_candidate(cls, candidate: Candidate, score: float) -> Finding:
        """Mask and fingerprint a candidate. ``score`` is the classifier confidence in [0, 1]."""
        if not 0.0 <= score <= 1.0:
            raise ValueError(f"score must be within [0, 1], got {score}")
        return cls(
            rule_id=candidate.rule_id,
            file_path=candidate.chunk.path,
            line_no=candidate.line_no,
            commit_sha=candidate.chunk.commit,
            masked_value=mask(candidate.match),
            fingerprint=fingerprint(candidate.match, candidate.chunk.path),
            score=score,
            severity=candidate.severity,
            remediation=candidate.remediation,
        )
