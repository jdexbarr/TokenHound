"""Generic detector: high-entropy values assigned to secret-looking names (spec section 7).

It catches secrets with no known format, e.g. ``db_password = "q8Zr...``. It is deliberately
permissive: the ML classifier (spec section 8) decides which of these candidates are real.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterator

from tokenhound.models import Candidate, Chunk, Severity

RULE_ID = "generic-high-entropy"
DEFAULT_MIN_LENGTH = 16
DEFAULT_MIN_ENTROPY = 3.5
REMEDIATION = (
    "If this value is a real credential, revoke or rotate it with its issuer, remove it from the "
    "code and load it from an environment variable or a secret manager instead."
)

# name (containing a secret-ish word) followed by = or : and a quoted or bare value. Name parts are
# length-bounded so a huge identifier cannot cause quadratic backtracking.
_ASSIGNMENT = re.compile(
    r"""
    (?<![\w.\-$])
    (?P<name>(?:[A-Za-z_$][\w.\-]{0,63}?)?
        (?:key|secret|token|passw(?:or)?d|pwd|credential|auth)
     [\w.\-]{0,64})
    ["']?\s*(?::=|=>|[:=])\s*
    (?:
        (?P<quote>["'`])(?P<quoted>[^\s"'`,;]+)(?P=quote)
      | # A bare value must end cleanly: ``self._keys[rule.id]`` or ``get(x)`` is code.
        (?P<bare>[^\s"'`,;()\[\]{}<>]+)(?=[\s,;"'`)\]}>]|$)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def shannon_entropy(value: str) -> float:
    """Shannon entropy of ``value`` in bits per character (0.0 for an empty string)."""
    if not value:
        return 0.0
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in Counter(value).values())


class EntropyDetector:
    """Flag assignments to key/secret/token/password-like names whose value looks random."""

    rule_id = RULE_ID

    def __init__(
        self,
        min_length: int = DEFAULT_MIN_LENGTH,
        min_entropy: float = DEFAULT_MIN_ENTROPY,
    ) -> None:
        if min_length < 1:
            raise ValueError("min_length must be positive")
        if min_entropy < 0:
            raise ValueError("min_entropy must not be negative")
        self.min_length = min_length
        self.min_entropy = min_entropy

    def detect(self, chunk: Chunk) -> Iterator[Candidate]:
        for match in _ASSIGNMENT.finditer(chunk.text):
            group = "quoted" if match.group("quoted") is not None else "bare"
            value = match.group(group)
            if len(value) < self.min_length or shannon_entropy(value) < self.min_entropy:
                continue
            yield Candidate(
                rule_id=RULE_ID,
                match=value,
                span=match.span(group),
                chunk=chunk,
                severity=Severity.MEDIUM,
                remediation=REMEDIATION,
            )
