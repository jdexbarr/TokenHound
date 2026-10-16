import json
import logging
import os
import random
from pathlib import Path

import pytest

from tests.conftest import random_token
from tokenhound.errors import SourceError
from tokenhound.models import Chunk
from tokenhound.sources import Source
from tokenhound.sources.notebook import _has_json_string, notebook_chunks
from tokenhound.sources.working_tree import WorkingTreeSource


def chunks(root: Path, **kwargs: int) -> list[Chunk]:
    source: Source = WorkingTreeSource(root, **kwargs)
    return list(source.iter_chunks())


def write_notebook(path: Path, cells: list[dict[str, object]]) -> str:
    """Write a notebook the way Jupyter does (indent 1, sorted keys, UTF-8)."""
    raw = json.dumps(
        {"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5},
        indent=1,
        sort_keys=True,
        ensure_ascii=False,
    )
    path.write_text(raw + "\n", encoding="utf-8")
    return raw


def raw_line_of(raw: str, needle: str) -> int:
    return next(i for i, line in enumerate(raw.splitlines(), start=1) if needle in line)


def test_yields_text_files_with_relative_posix_paths(tmp_path: Path) -> None:
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "src" / "pkg" / "a.py").write_text("x = 1\n")
    (tmp_path / "README.md").write_text("hi\n")

    found = chunks(tmp_path)

    assert [(c.path, c.line_no, c.commit, c.text) for c in found] == [
        ("README.md", 1, None, "hi\n"),
        ("src/pkg/a.py", 1, None, "x = 1\n"),
    ]


def test_priority_files_come_first(tmp_path: Path) -> None:
    for name in ("a.py", "z.tf", ".env", "b.txt", "mcp.json"):
        (tmp_path / name).write_text("x\n")

    assert [c.path for c in chunks(tmp_path)] == [".env", "mcp.json", "z.tf", "a.py", "b.txt"]


def test_skips_git_directory_but_not_other_dot_dirs(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]\n")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("on: push\n")

    assert [c.path for c in chunks(tmp_path)] == [".github/workflows/ci.yml"]


def test_ignores_gitignore(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text(".env\n")
    (tmp_path / ".env").write_text("A=1\n")

    assert ".env" in [c.path for c in chunks(tmp_path)]


def test_skips_binary_files(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\0\0\0")
    caplog.set_level(logging.DEBUG)

    assert chunks(tmp_path) == []
    assert "image.png: skipped (binary)" in caplog.text


def test_size_limits_are_larger_for_priority_files(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    (tmp_path / "big.txt").write_text("a" * 101)
    (tmp_path / "ok.txt").write_text("a" * 100)
    (tmp_path / ".env").write_text("a" * 150)
    (tmp_path / "huge.tf").write_text("a" * 201)
    caplog.set_level(logging.INFO)

    found = chunks(tmp_path, max_file_size=100, max_priority_file_size=200)

    assert [c.path for c in found] == [".env", "ok.txt"]
    assert "big.txt: skipped (101 bytes, limit 100)" in caplog.text
    assert "huge.tf: skipped (201 bytes, limit 200)" in caplog.text


def test_invalid_utf8_is_replaced_not_fatal(tmp_path: Path) -> None:
    (tmp_path / "latin1.txt").write_bytes("contraseña = 'x'\n".encode("latin-1"))

    [chunk] = chunks(tmp_path)

    assert chunk.text == "contrase�a = 'x'\n"


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="needs symlinks")
def test_symlinks_are_not_followed(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("x\n")
    root = tmp_path / "repo"
    root.mkdir()
    (root / "link.txt").symlink_to(outside / "secret.txt")
    (root / "linkdir").symlink_to(outside, target_is_directory=True)

    assert chunks(root) == []
    assert chunks(root / "link.txt") == []


def test_unreadable_file_is_skipped(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    locked = tmp_path / "locked.txt"
    locked.write_text("x\n")
    (tmp_path / "ok.txt").write_text("y\n")
    locked.chmod(0)
    try:
        if os.access(locked, os.R_OK):
            pytest.skip("running with privileges that ignore file permissions")
        assert [c.path for c in chunks(tmp_path)] == ["ok.txt"]
        assert "locked.txt: skipped (cannot read" in caplog.text
    finally:
        locked.chmod(0o600)


def test_single_file_root(tmp_path: Path) -> None:
    target = tmp_path / "config.py"
    target.write_text("x = 1\n")

    assert [c.path for c in chunks(target)] == ["config.py"]


def test_missing_root_raises_source_error(tmp_path: Path) -> None:
    with pytest.raises(SourceError, match="no such file"):
        WorkingTreeSource(tmp_path / "missing")


# --- notebooks (spec section 7: cell outputs are scanned) ---


def test_notebook_sources_and_outputs_are_chunks_with_file_line_numbers(
    tmp_path: Path, rng: random.Random
) -> None:
    printed = "hf_" + random_token(rng, 34)
    raw = write_notebook(
        tmp_path / "explore.ipynb",
        [
            {"cell_type": "markdown", "metadata": {}, "source": ["# Título\n", "intro"]},
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [
                    {"name": "stdout", "output_type": "stream", "text": ["ok\n", printed + "\n"]}
                ],
                "source": ["import os\n", "print(os.environ['HF'])\n"],
            },
        ],
    )

    found = chunks(tmp_path)

    texts = {c.text: c.line_no for c in found}
    assert texts == {
        "# Título\nintro": raw_line_of(raw, "Título"),
        f"ok\n{printed}\n": raw_line_of(raw, '"ok\\n"'),
        "import os\nprint(os.environ['HF'])\n": raw_line_of(raw, "import os"),
    }
    output = next(c for c in found if printed in c.text)
    secret_line = output.line_no + output.text.count("\n", 0, output.text.index(printed))
    assert secret_line == raw_line_of(raw, printed)


def test_notebook_rich_outputs_and_tracebacks(tmp_path: Path) -> None:
    write_notebook(
        tmp_path / "nb.ipynb",
        [
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "source": "x",
                "outputs": [
                    {
                        "output_type": "execute_result",
                        "execution_count": 1,
                        "metadata": {},
                        "data": {
                            "text/plain": ["'plain'"],
                            "text/html": ["<b>html</b>"],
                            "image/png": "iVBORw0KGgo=",
                            "application/json": {"token": "json-value"},
                        },
                    },
                    {"output_type": "error", "ename": "E", "evalue": "", "traceback": ["tb1"]},
                ],
            }
        ],
    )

    texts = [c.text for c in chunks(tmp_path)]

    assert "'plain'" in texts
    assert "<b>html</b>" in texts
    assert "tb1\n" in texts
    assert any('"token": "json-value"' in t for t in texts)
    assert not any("iVBORw0KGgo" in t for t in texts)


def test_notebook_string_fields_keep_one_line_number(tmp_path: Path) -> None:
    raw = write_notebook(
        tmp_path / "nb.ipynb",
        [{"cell_type": "code", "metadata": {}, "outputs": [], "source": "a = 1\nkey = 2\n"}],
    )

    found = chunks(tmp_path)

    line = raw_line_of(raw, "a = 1")
    assert [(c.text, c.line_no) for c in found] == [("a = 1\n", line), ("key = 2\n", line)]


@pytest.mark.parametrize("content", ["not json", "[1, 2]", '{"cells": 3}'])
def test_invalid_notebook_is_scanned_as_text(tmp_path: Path, content: str) -> None:
    (tmp_path / "broken.ipynb").write_text(content)

    assert [(c.text, c.line_no) for c in chunks(tmp_path)] == [(content, 1)]


def test_notebook_tolerates_malformed_cells() -> None:
    raw = json.dumps(
        {"cells": [1, {"source": None, "outputs": [2, {"text": 3}]}, {"outputs": "x"}]}
    )

    result = notebook_chunks("nb.ipynb", raw)

    assert result is not None
    assert list(result) == []


def test_notebook_line_not_found_falls_back_to_cell_position() -> None:
    # Hand-written JSON with escaped unicode that Jupyter would not produce.
    raw = '{"cells": [{"source": ["\\u0061bc\\n"]}]}'

    result = notebook_chunks("nb.ipynb", raw)

    assert result is not None
    assert [(c.text, c.line_no) for c in result] == [("abc\n", 1)]


def test_read_error_is_logged_and_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    (tmp_path / "locked.txt").write_text("x\n")
    (tmp_path / "ok.txt").write_text("y\n")
    original = Path.read_bytes

    def read_bytes(self: Path) -> bytes:
        if self.name == "locked.txt":
            raise PermissionError(13, "Permission denied")
        return original(self)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)

    assert [c.path for c in chunks(tmp_path)] == ["ok.txt"]
    assert "locked.txt: skipped (cannot read: Permission denied)" in caplog.text


def test_walk_error_is_logged(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    WorkingTreeSource._walk_error(PermissionError(13, "Permission denied", str(tmp_path / "d")))

    assert "d: skipped (cannot list: Permission denied)" in caplog.text


def test_escaped_quote_does_not_count_as_a_json_string_start() -> None:
    assert not _has_json_string('"print(\\"abc\\")\\n"', '"abc')
    assert _has_json_string('  "abc\\n",', '"abc')
