import json
import random
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import random_token
from tokenhound import __version__, cli
from tokenhound.cli import EXIT_CLEAN, EXIT_ERROR, EXIT_FINDINGS, app
from tokenhound.detectors.rule_schema import RuleLoadError

runner = CliRunner()


def test_version_prints_installed_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"tokenhound {__version__}"


def test_no_arguments_shows_help() -> None:
    result = runner.invoke(app, [])

    assert "version" in result.output
    assert "scan" in result.output
    assert "Usage" in result.output


def test_unknown_command_fails() -> None:
    result = runner.invoke(app, ["does-not-exist"])

    assert result.exit_code != 0


# --- scan (FR-001, FR-039) ---


@pytest.fixture
def repo(tmp_path: Path, rng: random.Random) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(
        "import os\n\nclient = Client(token='ghp_" + random_token(rng, 36) + "')\n"
    )
    (tmp_path / "README.md").write_text("# demo\n")
    return tmp_path


def test_scan_reports_findings_with_file_and_line(repo: Path) -> None:
    result = runner.invoke(app, ["scan", str(repo)])

    assert result.exit_code == EXIT_FINDINGS
    assert "src/app.py:3" in result.stdout
    assert "github-token" in result.stdout
    assert "1 finding in 2 files (1 critical)." in result.stdout


def test_scan_clean_tree_exits_zero(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("print('hello')\n")

    result = runner.invoke(app, ["scan", str(tmp_path)])

    assert result.exit_code == EXIT_CLEAN
    assert "No secrets found in 1 file." in result.stdout


def test_scan_defaults_to_current_directory(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["scan"])

    assert result.exit_code == EXIT_FINDINGS
    assert "src/app.py:3" in result.stdout


def test_scan_json_output(repo: Path) -> None:
    result = runner.invoke(app, ["scan", str(repo), "--format", "json"])

    assert result.exit_code == EXIT_FINDINGS
    document = json.loads(result.stdout)
    [finding] = document["findings"]
    assert (finding["file_path"], finding["line_no"], finding["rule_id"]) == (
        "src/app.py",
        3,
        "github-token",
    )


def test_scan_missing_path_is_a_usage_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["scan", str(tmp_path / "missing")])

    assert result.exit_code == EXIT_ERROR


@pytest.mark.parametrize("value", ["-0.1", "1.5", "abc"])
def test_scan_threshold_must_be_a_probability(repo: Path, value: str) -> None:
    result = runner.invoke(app, ["scan", str(repo), "--threshold", value])

    assert result.exit_code == EXIT_ERROR


def test_scan_threshold_is_passed_to_the_scanner(repo: Path) -> None:
    result = runner.invoke(app, ["scan", str(repo), "-f", "json", "--threshold", "0.9"])

    assert json.loads(result.stdout)["summary"]["threshold"] == 0.9


def test_scan_rule_errors_exit_two(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken() -> None:
        raise RuleLoadError("rules/x.yaml: invalid regex")

    monkeypatch.setattr(cli, "default_detectors", broken)

    result = runner.invoke(app, ["scan", str(repo)])

    assert result.exit_code == EXIT_ERROR
    assert "error: rules/x.yaml: invalid regex" in result.stderr


def test_unexpected_errors_exit_two_without_their_message(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken() -> None:
        raise RuntimeError("text that might quote scanned content")

    monkeypatch.setattr(cli, "default_detectors", broken)

    result = runner.invoke(app, ["scan", str(repo)])

    assert result.exit_code == EXIT_ERROR
    assert "unexpected RuntimeError" in result.stderr
    assert "scanned content" not in result.stderr


def test_verbose_logs_skipped_files_to_stderr(repo: Path) -> None:
    (repo / "logo.png").write_bytes(b"\x89PNG\0\0")

    result = runner.invoke(app, ["scan", str(repo), "--verbose"])

    assert "logo.png: skipped (binary)" in result.stderr
    assert "logo.png" not in result.stdout


def test_quiet_by_default(repo: Path) -> None:
    (repo / "logo.png").write_bytes(b"\x89PNG\0\0")

    result = runner.invoke(app, ["scan", str(repo)])

    assert result.stderr == ""
