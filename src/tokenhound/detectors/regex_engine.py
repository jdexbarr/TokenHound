"""Regex detector driven by YAML rules."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence

from tokenhound.detectors.jwt import jwt_severity
from tokenhound.detectors.rule_schema import Rule
from tokenhound.models import Candidate, Chunk, Severity

# Rules whose severity depends on the matched value, keyed by rule id.
SEVERITY_ADJUSTERS: dict[str, Callable[[str, Severity], Severity]] = {"jwt": jwt_severity}


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
                adjust = SEVERITY_ADJUSTERS.get(rule.id)
                severity = adjust(secret, rule.severity) if adjust else rule.severity
                yield Candidate(
                    rule_id=rule.id,
                    match=secret,
                    span=match.span(rule.secret_group),
                    chunk=chunk,
                    severity=severity,
                    remediation=rule.remediation,
                )
