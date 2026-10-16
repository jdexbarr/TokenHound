"""Working-tree source: the files on disk under a directory (spec section 5, FR-001).

What is skipped (A-09, D-008):

- the ``.git`` directory (history is the job of ``--history``);
- symbolic links, so a scan never reads files outside the scanned tree;
- binary files (a NUL byte in the first 8 KiB);
- files over ``max_file_size`` (1 MiB), or ``max_priority_file_size`` (20 MiB) for priority files
  such as notebooks, whose outputs easily exceed 1 MiB;
- files that cannot be read (logged, not fatal).

``.gitignore`` is not honoured: ignored files such as ``.env`` are exactly where secrets sit.
Priority files are scanned first. Text is decoded as UTF-8 with replacement characters, so an
unusual encoding cannot abort a scan.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from pathlib import Path

from tokenhound.errors import SourceError
from tokenhound.models import Chunk
from tokenhound.sources.notebook import notebook_chunks
from tokenhound.sources.priority import FileKind, classify

logger = logging.getLogger(__name__)

DEFAULT_MAX_FILE_SIZE = 1024 * 1024
DEFAULT_MAX_PRIORITY_FILE_SIZE = 20 * 1024 * 1024
BINARY_SNIFF_BYTES = 8192
SKIPPED_DIRS = frozenset({".git"})


class WorkingTreeSource:
    """Yield one chunk per text file under ``root`` (several per notebook)."""

    def __init__(
        self,
        root: Path,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
        max_priority_file_size: int = DEFAULT_MAX_PRIORITY_FILE_SIZE,
    ) -> None:
        if not root.exists():
            raise SourceError(f"{root}: no such file or directory")
        self.root = root
        self.max_file_size = max_file_size
        self.max_priority_file_size = max_priority_file_size

    def iter_chunks(self) -> Iterator[Chunk]:
        for path, relative in self._files():
            text = self._read(path, relative)
            if text is None:
                continue
            if classify(relative) is FileKind.NOTEBOOK:
                chunks = notebook_chunks(relative, text)
                if chunks is not None:
                    yield from chunks
                    continue
                logger.debug("%s: not a valid notebook, scanned as text", relative)
            yield Chunk(path=relative, commit=None, line_no=1, text=text)

    def _files(self) -> list[tuple[Path, str]]:
        """Every candidate file with its ``/``-separated path relative to the root."""
        if self.root.is_file():
            if self.root.is_symlink():
                logger.info("%s: skipped (symbolic link)", self.root)
                return []
            return [(self.root, self.root.name)]
        found: list[tuple[Path, str]] = []
        for directory, dirnames, filenames in os.walk(self.root, onerror=self._walk_error):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIPPED_DIRS)
            for name in sorted(filenames):
                path = Path(directory, name)
                relative = path.relative_to(self.root).as_posix()
                if path.is_symlink():
                    logger.info("%s: skipped (symbolic link)", relative)
                    continue
                found.append((path, relative))
        # Priority files first; the stable sort keeps name order within each group.
        found.sort(key=lambda item: not classify(item[1]).is_priority)
        return found

    def _read(self, path: Path, relative: str) -> str | None:
        limit = (
            self.max_priority_file_size if classify(relative).is_priority else self.max_file_size
        )
        try:
            size = path.stat().st_size
            if size > limit:
                logger.info("%s: skipped (%d bytes, limit %d)", relative, size, limit)
                return None
            data = path.read_bytes()
        except OSError as exc:
            logger.warning("%s: skipped (cannot read: %s)", relative, exc.strerror or exc)
            return None
        if b"\0" in data[:BINARY_SNIFF_BYTES]:
            logger.debug("%s: skipped (binary)", relative)
            return None
        return data.decode("utf-8", errors="replace")

    @staticmethod
    def _walk_error(error: OSError) -> None:
        logger.warning("%s: skipped (cannot list: %s)", error.filename, error.strerror or error)
