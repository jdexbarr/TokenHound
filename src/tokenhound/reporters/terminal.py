"""Rich terminal output (FR-022, UI-003): a findings table, remediation per rule and a summary."""

from __future__ import annotations

import re
from io import StringIO

from rich.console import Console
from rich.table import Table
from rich.text import Text

from tokenhound.models import Finding, Severity
from tokenhound.scanner import ScanResult

SEVERITY_STYLES = {
    Severity.CRITICAL: "bold white on red",
    Severity.HIGH: "bold red",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "cyan",
}

# File names come from the scanned repository; control characters in them could move the cursor or
# rewrite earlier output, so they are replaced before printing.
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def safe(value: str) -> str:
    """Replace control characters with U+FFFD."""
    return _CONTROL.sub("\N{REPLACEMENT CHARACTER}", value)


MAX_VALUE_WIDTH = 40


def display_value(masked: str) -> str:
    """Shorten long masked values (a PEM block is hundreds of ``*``) for the table."""
    if len(masked) <= MAX_VALUE_WIDTH:
        return masked
    return f"{masked[:4]}********{masked[-4:]} ({len(masked)} chars)"


class TerminalReporter:
    def __init__(self, color: bool = False, width: int = 120) -> None:
        self.color = color
        self.width = width

    def render(self, result: ScanResult) -> str:
        buffer = StringIO()
        console = Console(
            file=buffer,
            width=self.width,
            force_terminal=self.color,
            no_color=not self.color,
            highlight=False,
            soft_wrap=False,
        )
        if result.findings:
            console.print(_table(result.findings))
            console.print(Text("Remediation", style="bold"))
            remediation: dict[str, str] = {}
            for finding in result.findings:
                remediation.setdefault(finding.rule_id, finding.remediation)
            for rule_id, text in remediation.items():
                console.print(Text.assemble("  ", (rule_id, "bold"), ": ", safe(text)))
            console.print()
        console.print(_summary(result))
        return buffer.getvalue()


def _table(findings: tuple[Finding, ...]) -> Table:
    table = Table(title="TokenHound findings", title_justify="left", expand=False)
    table.add_column("Severity", no_wrap=True)
    table.add_column("Rule", no_wrap=True)
    table.add_column("Location", overflow="fold")
    table.add_column("Value", overflow="fold")
    table.add_column("Score", justify="right", no_wrap=True)
    for finding in findings:
        location = f"{finding.file_path}:{finding.line_no}"
        if finding.commit_sha:
            location += f" @ {finding.commit_sha[:12]}"
        table.add_row(
            Text(finding.severity.value.upper(), style=SEVERITY_STYLES[finding.severity]),
            Text(finding.rule_id),
            Text(safe(location)),
            Text(safe(display_value(finding.masked_value))),
            Text(f"{finding.score:.2f}"),
        )
    return table


def _summary(result: ScanResult) -> Text:
    files = _plural(result.files_scanned, "file")
    if not result.findings:
        text = Text(f"No secrets found in {files}.", style="bold green")
    else:
        counts = {s: sum(f.severity is s for f in result.findings) for s in Severity}
        parts = ", ".join(f"{n} {s.value}" for s, n in counts.items() if n)
        found = _plural(len(result.findings), "finding")
        text = Text(f"{found} in {files} ({parts}).", style="bold red")
    if result.below_threshold:
        text.append(
            f" {_plural(result.below_threshold, 'candidate')} below threshold "
            f"{result.threshold:.2f} not shown.",
            style="dim",
        )
    return text


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"
