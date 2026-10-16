"""Split a Jupyter notebook into chunks: cell sources and text outputs (spec section 7).

Keys often end up in printed cell outputs, so outputs are scanned as well as code. Each chunk is
the decoded text of one field, which lets the detectors see ``api_key = "..."`` instead of the
JSON-escaped form. Line numbers point into the ``.ipynb`` file itself: Jupyter writes each line of a
multi-line field as its own JSON string on its own line, so the first line of a field is located by
searching for its JSON encoding.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from tokenhound.models import Chunk

TEXT_MIME_PREFIXES = ("text/",)
JSON_MIME_TYPES = frozenset({"application/json"})


def notebook_chunks(path: str, raw: str) -> Iterator[Chunk] | None:
    """Return chunks for a notebook, or ``None`` if ``raw`` is not a notebook JSON document."""
    try:
        document = json.loads(raw)
    except (ValueError, RecursionError):
        return None
    if not isinstance(document, dict) or not isinstance(document.get("cells"), list):
        return None
    return _iter_chunks(path, document["cells"], raw.splitlines())


def _iter_chunks(path: str, cells: list[Any], raw_lines: list[str]) -> Iterator[Chunk]:
    base = 0  # raw line index where the current cell can start
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        furthest = base
        for field in _cell_fields(cell):
            lines = _as_lines(field)
            if not lines:
                continue
            found = _locate(raw_lines, lines[0], base)
            line_no = (found if found is not None else base) + 1
            furthest = max(furthest, found if found is not None else base)
            if isinstance(field, list):
                # One JSON string per raw line: newline offsets inside the chunk map to raw lines.
                yield Chunk(path=path, commit=None, line_no=line_no, text="".join(lines))
            else:
                # The whole field sits on one raw line; keep every logical line on that line number.
                for line in lines:
                    yield Chunk(path=path, commit=None, line_no=line_no, text=line)
        base = furthest


def _cell_fields(cell: dict[str, Any]) -> Iterator[object]:
    yield cell.get("source")
    outputs = cell.get("outputs")
    if not isinstance(outputs, list):
        return
    for output in outputs:
        if not isinstance(output, dict):
            continue
        yield output.get("text")
        traceback = output.get("traceback")
        if isinstance(traceback, list):
            yield [f"{line}\n" for line in traceback if isinstance(line, str)]
        data = output.get("data")
        if isinstance(data, dict):
            for mime, value in data.items():
                if mime.startswith(TEXT_MIME_PREFIXES):
                    yield value
                elif mime in JSON_MIME_TYPES:
                    yield json.dumps(value, indent=1)


def _as_lines(field: object) -> list[str]:
    if isinstance(field, str):
        return field.splitlines(keepends=True)
    if isinstance(field, list):
        return [line for line in field if isinstance(line, str)]
    return []


def _locate(raw_lines: list[str], first_line: str, start: int) -> int | None:
    """Index of the raw line holding the JSON string that begins with ``first_line``."""
    needles = {
        '"' + json.dumps(first_line, ensure_ascii=ascii_only)[1:-1] for ascii_only in (False, True)
    }
    for index in range(start, len(raw_lines)):
        if any(_has_json_string(raw_lines[index], needle) for needle in needles):
            return index
    return None


def _has_json_string(raw_line: str, needle: str) -> bool:
    """True if ``needle`` (a quote plus an encoded prefix) opens a JSON string in ``raw_line``."""
    position = raw_line.find(needle)
    while position != -1:
        if position == 0 or raw_line[position - 1] != "\\":
            return True
        position = raw_line.find(needle, position + 1)
    return False
