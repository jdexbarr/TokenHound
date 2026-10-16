"""Cross-cutting security test (NFR-001): no full secret ever reaches any output.

One synthetic secret per built-in rule is planted in a temporary tree, in the priority file kinds
of spec section 7, then every output format and the verbose log are checked.
"""

import json
import random
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import random_token
from tests.test_rules import POSITIVES
from tokenhound.cli import EXIT_FINDINGS, app

runner = CliRunner()


def plant(root: Path, rng: random.Random) -> list[str]:
    secrets = [generators[0](rng) for generators in POSITIVES.values()]
    secrets.append(random_token(rng, 32))  # generic high-entropy value
    (root / ".cursor").mkdir()
    (root / ".cursor" / "mcp.json").write_text(
        json.dumps({"mcpServers": {"x": {"env": {f"KEY_{i}": s for i, s in enumerate(secrets)}}}})
    )
    (root / ".env").write_text("".join(f"SECRET_{i}={s!r}\n" for i, s in enumerate(secrets)))
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "metadata": {},
                "source": ["print(secrets)\n"],
                "outputs": [
                    {"output_type": "stream", "name": "stdout", "text": [f"{s}\n" for s in secrets]}
                ],
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (root / "explore.ipynb").write_text(json.dumps(notebook, indent=1))
    (root / "settings.py").write_text(f"password = '{secrets[-1]}'\n")
    return secrets


@pytest.mark.parametrize(
    "args",
    [[], ["--format", "json"], ["--verbose"], ["--format", "json", "--verbose"]],
    ids=["terminal", "json", "terminal-verbose", "json-verbose"],
)
def test_no_secret_in_any_output(tmp_path: Path, rng: random.Random, args: list[str]) -> None:
    secrets = plant(tmp_path, rng)

    result = runner.invoke(app, ["scan", str(tmp_path), *args])

    assert result.exit_code == EXIT_FINDINGS
    output = result.stdout + result.stderr
    for secret in secrets:
        assert secret not in output
        assert secret[4:-4] not in output


def test_every_planted_secret_is_reported(tmp_path: Path, rng: random.Random) -> None:
    plant(tmp_path, rng)

    result = runner.invoke(app, ["scan", str(tmp_path), "--format", "json"])

    found = {(f["file_path"], f["rule_id"]) for f in json.loads(result.stdout)["findings"]}
    for path in (".cursor/mcp.json", ".env", "explore.ipynb"):
        assert {rule for p, rule in found if p == path} >= set(POSITIVES), path
    assert ("settings.py", "generic-high-entropy") in found
