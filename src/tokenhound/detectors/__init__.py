"""Detectors: turn chunks of text into secret candidates (spec section 5, stage 2)."""

from collections.abc import Iterator
from typing import Protocol

from tokenhound.models import Candidate, Chunk


class Detector(Protocol):
    """Anything that finds candidates in a chunk."""

    def detect(self, chunk: Chunk) -> Iterator[Candidate]: ...
