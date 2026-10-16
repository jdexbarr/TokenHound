"""Sources: produce the chunks of text the detectors scan (spec section 5, stage 1)."""

from collections.abc import Iterator
from typing import Protocol

from tokenhound.models import Chunk


class Source(Protocol):
    """Anything that yields :class:`Chunk` objects."""

    def iter_chunks(self) -> Iterator[Chunk]: ...
