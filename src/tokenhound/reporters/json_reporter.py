"""JSON output (FR-023). The shape is documented in ``docs/ARCHITECTURE.md``."""

from __future__ import annotations

import json
from typing import Any

from tokenhound import __version__
from tokenhound.models import Finding, Severity
from tokenhound.scanner import ScanResult

SCHEMA_VERSION = 1


class JsonReporter:
    def render(self, result: ScanResult) -> str:
        by_severity = {severity.value: 0 for severity in Severity}
        for finding in result.findings:
            by_severity[finding.severity.value] += 1
        document: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "tool": {"name": "tokenhound", "version": __version__},
            "summary": {
                "files_scanned": result.files_scanned,
                "findings": len(result.findings),
                "below_threshold": result.below_threshold,
                "threshold": result.threshold,
                "by_severity": by_severity,
            },
            "findings": [_finding(f) for f in result.findings],
        }
        return json.dumps(document, indent=2) + "\n"


def _finding(finding: Finding) -> dict[str, Any]:
    return {
        "rule_id": finding.rule_id,
        "severity": finding.severity.value,
        "file_path": finding.file_path,
        "line_no": finding.line_no,
        "commit_sha": finding.commit_sha,
        "masked_value": finding.masked_value,
        "fingerprint": finding.fingerprint,
        "score": finding.score,
        "remediation": finding.remediation,
    }
