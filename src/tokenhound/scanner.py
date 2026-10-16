"""Orchestrator: wires sources, detectors, scoring and filtering into one scan (A-14).

Until the classifier lands (milestone H8) every candidate gets the pass-through score 1.0 (A-06).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from tokenhound.detectors import Detector, entropy
from tokenhound.detectors.entropy import EntropyDetector
from tokenhound.detectors.regex_engine import RegexDetector
from tokenhound.detectors.rule_schema import Rule, load_rules
from tokenhound.models import Candidate, Chunk, Finding
from tokenhound.sources import Source

Scorer = Callable[[Candidate], float]

# Detectors that only know "this looks random". A candidate from a provider rule covering the same
# characters is more specific, so the generic one is dropped.
GENERIC_RULE_IDS = frozenset({entropy.RULE_ID})


def pass_through_score(candidate: Candidate) -> float:
    """Score used before the ML classifier exists: every candidate is reported."""
    return 1.0


@dataclass(frozen=True, slots=True)
class ScanResult:
    """Findings at or above the threshold, sorted most severe first, plus scan statistics."""

    findings: tuple[Finding, ...]
    files_scanned: int
    below_threshold: int
    threshold: float


def default_detectors(rules: Sequence[Rule] | None = None) -> list[Detector]:
    """The built-in rule set plus the generic entropy detector."""
    return [RegexDetector(load_rules() if rules is None else rules), EntropyDetector()]


def detect_chunk(chunk: Chunk, detectors: Iterable[Detector]) -> list[Candidate]:
    """Run every detector on ``chunk`` and drop generic candidates that overlap specific ones."""
    candidates = [candidate for detector in detectors for candidate in detector.detect(chunk)]
    specific = [c.span for c in candidates if c.rule_id not in GENERIC_RULE_IDS]
    return [
        c
        for c in candidates
        if c.rule_id not in GENERIC_RULE_IDS or not any(_overlaps(c.span, s) for s in specific)
    ]


def scan(
    source: Source,
    detectors: Sequence[Detector],
    *,
    threshold: float = 0.5,
    scorer: Scorer = pass_through_score,
) -> ScanResult:
    """Scan every chunk of ``source``; keep findings whose score is at least ``threshold``."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"threshold must be within [0, 1], got {threshold}")
    findings: list[Finding] = []
    paths: set[str] = set()
    below = 0
    for chunk in source.iter_chunks():
        paths.add(chunk.path)
        for candidate in detect_chunk(chunk, detectors):
            finding = Finding.from_candidate(candidate, scorer(candidate))
            if finding.score >= threshold:
                findings.append(finding)
            else:
                below += 1
    findings.sort(key=lambda f: (-f.severity.rank, f.file_path, f.line_no, f.rule_id))
    return ScanResult(
        findings=tuple(findings),
        files_scanned=len(paths),
        below_threshold=below,
        threshold=threshold,
    )


def _overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]
