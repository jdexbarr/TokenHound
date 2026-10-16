import json

from tokenhound import __version__
from tokenhound.models import Finding, Severity
from tokenhound.reporters import Reporter
from tokenhound.reporters.json_reporter import JsonReporter
from tokenhound.reporters.terminal import TerminalReporter, display_value, safe
from tokenhound.scanner import ScanResult


def make_finding(**overrides: object) -> Finding:
    fields: dict[str, object] = {
        "rule_id": "github-token",
        "file_path": ".cursor/mcp.json",
        "line_no": 5,
        "commit_sha": None,
        "masked_value": "tst_" + "*" * 12 + "wxyz",
        "fingerprint": "f" * 64,
        "score": 1.0,
        "severity": Severity.CRITICAL,
        "remediation": "Revoke the token.",
    }
    fields.update(overrides)
    return Finding(**fields)  # type: ignore[arg-type]


def make_result(*findings: Finding, files: int = 3, below: int = 0) -> ScanResult:
    return ScanResult(findings=findings, files_scanned=files, below_threshold=below, threshold=0.5)


RESULT = make_result(
    make_finding(),
    make_finding(
        rule_id="generic-high-entropy",
        file_path=".env",
        line_no=2,
        commit_sha="0123456789abcdef0123",
        severity=Severity.MEDIUM,
        score=0.75,
        remediation="Rotate it.",
    ),
)


def test_reporters_satisfy_the_protocol() -> None:
    reporters: list[Reporter] = [JsonReporter(), TerminalReporter()]

    assert all(r.render(RESULT) for r in reporters)


# --- JSON (FR-023) ---


def test_json_document_shape() -> None:
    document = json.loads(JsonReporter().render(RESULT))

    assert document["schema_version"] == 1
    assert document["tool"] == {"name": "tokenhound", "version": __version__}
    assert document["summary"] == {
        "files_scanned": 3,
        "findings": 2,
        "below_threshold": 0,
        "threshold": 0.5,
        "by_severity": {"critical": 1, "high": 0, "medium": 1, "low": 0},
    }
    assert document["findings"][1] == {
        "rule_id": "generic-high-entropy",
        "severity": "medium",
        "file_path": ".env",
        "line_no": 2,
        "commit_sha": "0123456789abcdef0123",
        "masked_value": "tst_" + "*" * 12 + "wxyz",
        "fingerprint": "f" * 64,
        "score": 0.75,
        "remediation": "Rotate it.",
    }


def test_json_with_no_findings() -> None:
    document = json.loads(JsonReporter().render(make_result()))

    assert document["findings"] == []
    assert document["summary"]["findings"] == 0


# --- terminal (FR-022) ---


def test_terminal_snapshot() -> None:
    output = TerminalReporter(width=100).render(RESULT)

    assert [line.rstrip() for line in output.splitlines()] == [
        "TokenHound findings",
        "┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓",
        "┃ Severity ┃ Rule                 ┃ Location              ┃ Value                ┃ Score ┃",  # noqa: E501
        "┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩",
        "│ CRITICAL │ github-token         │ .cursor/mcp.json:5    │ tst_************wxyz │  1.00 │",  # noqa: E501
        "│ MEDIUM   │ generic-high-entropy │ .env:2 @ 0123456789ab │ tst_************wxyz │  0.75 │",  # noqa: E501
        "└──────────┴──────────────────────┴───────────────────────┴──────────────────────┴───────┘",
        "Remediation",
        "  github-token: Revoke the token.",
        "  generic-high-entropy: Rotate it.",
        "",
        "2 findings in 3 files (1 critical, 1 medium).",
    ]


def test_terminal_no_findings() -> None:
    assert TerminalReporter().render(make_result(files=1)) == "No secrets found in 1 file.\n"


def test_terminal_mentions_candidates_below_threshold() -> None:
    output = TerminalReporter().render(make_result(make_finding(), files=1, below=2))

    assert output.endswith(
        "1 finding in 1 file (1 critical). 2 candidates below threshold 0.50 not shown.\n"
    )


def test_terminal_remediation_listed_once_per_rule() -> None:
    output = TerminalReporter().render(make_result(make_finding(), make_finding(line_no=9)))

    assert output.count("Revoke the token.") == 1


def test_terminal_color_uses_ansi_codes_only_when_enabled() -> None:
    assert "\x1b[" in TerminalReporter(color=True).render(RESULT)
    assert "\x1b[" not in TerminalReporter(color=False).render(RESULT)


def test_control_characters_in_paths_are_neutralised() -> None:
    evil = make_finding(file_path="a\x1b[2J\rb[bold]x[/bold].py")

    output = TerminalReporter(width=200).render(make_result(evil))

    assert "\x1b" not in output
    assert "\r" not in output
    assert "a�[2J�b[bold]x[/bold].py:5" in output


def test_safe_and_display_value() -> None:
    assert safe("ok\tno\x7f") == "ok�no�"
    assert display_value("a" * 40) == "a" * 40
    assert display_value("-----" + "*" * 300 + "-----") == "----********---- (310 chars)"
