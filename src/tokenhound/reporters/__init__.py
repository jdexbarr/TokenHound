"""Reporters: render scan results (spec section 5, stage 5).

Reporters only ever receive :class:`~tokenhound.models.Finding` objects, which hold masked values,
so no output format can print a full secret.
"""

from typing import Protocol

from tokenhound.scanner import ScanResult


class Reporter(Protocol):
    """Turn a scan result into text for stdout or a file."""

    def render(self, result: ScanResult) -> str: ...
