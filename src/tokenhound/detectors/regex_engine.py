"""Regex detector driven by YAML rules."""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from tokenhound.detectors.rule_schema import Rule
from tokenhound.models import Candidate, Chunk


class RegexDetector:
    """Run every rule's regex over a chunk.

    Rules with ``keywords`` are skipped unless one keyword appears in the chunk
    (case-insensitive). That cheap substring test avoids most regex work on large scans.
    """

    def __init__(self, rules: Sequence[Rule]) -> None:
        self._rules = tuple(rules)
        self._keywords = {
            rule.id: tuple(keyword.lower() for keyword in rule.keywords) for rule in self._rules
        }

    @property
    def rules(self) -> tuple[Rule, ...]:
        return self._rules

    def detect(self, chunk: Chunk) -> Iterator[Candidate]:
        lowered = chunk.text.lower()
        for rule in self._rules:
            keywords = self._keywords[rule.id]
            if keywords and not any(keyword in lowered for keyword in keywords):
                continue
            for match in rule.pattern.finditer(chunk.text):
                secret = match.group(rule.secret_group)
                if not secret:
                    continue
                yield Candidate(
                    rule_id=rule.id,
                    match=secret,
                    span=match.span(rule.secret_group),
                    chunk=chunk,
                    severity=rule.severity,
                    remediation=rule.remediation,
                )
