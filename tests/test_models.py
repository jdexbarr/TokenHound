import dataclasses

import pytest

from tokenhound.models import Candidate, Chunk, Finding, Severity
from tokenhound.utils.fingerprint import fingerprint

SECRET = "tst_" + "Qw3rTy9UiOp4AsDf7GhJ"


def make_candidate(text: str, secret: str = SECRET, line_no: int = 1) -> Candidate:
    chunk = Chunk(path="app/config.py", commit=None, line_no=line_no, text=text)
    start = text.index(secret)
    return Candidate(
        rule_id="test-token",
        match=secret,
        span=(start, start + len(secret)),
        chunk=chunk,
        severity=Severity.HIGH,
        remediation="Rotate the test token.",
    )


def test_candidate_line_no_counts_newlines_before_match() -> None:
    text = f"first line\nsecond line\ntoken = '{SECRET}'\n"

    assert make_candidate(text).line_no == 3
    assert make_candidate(text, line_no=10).line_no == 12


def test_finding_from_candidate_masks_and_fingerprints() -> None:
    candidate = make_candidate(f"token = '{SECRET}'")

    finding = Finding.from_candidate(candidate, score=0.9)

    assert finding.rule_id == "test-token"
    assert finding.file_path == "app/config.py"
    assert finding.line_no == 1
    assert finding.commit_sha is None
    assert finding.masked_value == "tst_" + "*" * 16 + "7GhJ"
    assert finding.fingerprint == fingerprint(SECRET, "app/config.py")
    assert finding.score == 0.9
    assert finding.severity is Severity.HIGH
    assert finding.remediation == "Rotate the test token."


def test_finding_has_no_field_for_the_raw_secret() -> None:
    finding = Finding.from_candidate(make_candidate(f"x = '{SECRET}'"), score=1.0)

    for value in dataclasses.asdict(finding).values():
        assert SECRET not in str(value)


@pytest.mark.parametrize("score", [-0.01, 1.01])
def test_finding_rejects_scores_outside_unit_interval(score: float) -> None:
    with pytest.raises(ValueError, match="score"):
        Finding.from_candidate(make_candidate(f"x = '{SECRET}'"), score=score)


def test_reprs_never_contain_the_secret() -> None:
    candidate = make_candidate(f"token = '{SECRET}'")
    finding = Finding.from_candidate(candidate, score=0.5)

    assert SECRET not in repr(candidate)
    assert SECRET not in repr(candidate.chunk)
    assert SECRET not in repr(finding)


def test_models_are_immutable() -> None:
    finding = Finding.from_candidate(make_candidate(f"x = '{SECRET}'"), score=0.5)

    with pytest.raises(dataclasses.FrozenInstanceError):
        finding.score = 0.1  # type: ignore[misc]


def test_severity_rank_orders_levels() -> None:
    ordered = sorted(Severity, key=lambda s: s.rank)

    assert ordered == [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
    assert Severity("critical") is Severity.CRITICAL
