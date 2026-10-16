import random
from collections.abc import Iterator

import pytest

from tests.conftest import random_token
from tokenhound.detectors.entropy import RULE_ID as ENTROPY_RULE_ID
from tokenhound.models import Candidate, Chunk, Severity
from tokenhound.scanner import default_detectors, detect_chunk, pass_through_score, scan


class ListSource:
    def __init__(self, *chunks: Chunk) -> None:
        self.chunks = chunks

    def iter_chunks(self) -> Iterator[Chunk]:
        yield from self.chunks


def chunk(text: str, path: str = "app.py") -> Chunk:
    return Chunk(path=path, commit=None, line_no=1, text=text)


DETECTORS = default_detectors()


def test_provider_rule_wins_over_entropy_on_the_same_value(rng: random.Random) -> None:
    key = "ghp_" + random_token(rng, 36)

    found = detect_chunk(chunk(f'github_token = "{key}"'), DETECTORS)

    assert [(c.rule_id, c.match) for c in found] == [("github-token", key)]


def test_entropy_candidate_elsewhere_in_the_chunk_is_kept(rng: random.Random) -> None:
    key = "ghp_" + random_token(rng, 36)
    password = random_token(rng, 24)

    found = detect_chunk(chunk(f'token = "{key}"\ndb_password = "{password}"\n'), DETECTORS)

    assert [(c.rule_id, c.match) for c in found] == [
        ("github-token", key),
        (ENTROPY_RULE_ID, password),
    ]


def test_scan_sorts_by_severity_then_location(rng: random.Random) -> None:
    google = "AIza" + random_token(rng, 35)
    aws = "AKIA" + random_token(rng, 16, "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
    source = ListSource(
        chunk(f"k = '{google}'\n", "b.py"),
        chunk(f"\n\nk = '{aws}'\n", "c.py"),
        chunk(f"k = '{aws}'\n", "a.py"),
        chunk("nothing here\n", "d.py"),
    )

    result = scan(source, DETECTORS)

    assert [(f.severity, f.file_path, f.line_no) for f in result.findings] == [
        (Severity.CRITICAL, "a.py", 1),
        (Severity.CRITICAL, "c.py", 3),
        (Severity.MEDIUM, "b.py", 1),
    ]
    assert result.files_scanned == 4
    assert result.below_threshold == 0
    assert all(f.score == 1.0 for f in result.findings)


def test_files_scanned_counts_distinct_paths() -> None:
    result = scan(ListSource(chunk("a", "nb.ipynb"), chunk("b", "nb.ipynb")), DETECTORS)

    assert result.files_scanned == 1


def test_threshold_filters_low_scores(rng: random.Random) -> None:
    key = "ghp_" + random_token(rng, 36)
    password = random_token(rng, 24)
    source = ListSource(chunk(f'token = "{key}"\npassword = "{password}"\n'))

    def scorer(candidate: Candidate) -> float:
        return 0.9 if candidate.rule_id == "github-token" else 0.2

    result = scan(source, DETECTORS, threshold=0.5, scorer=scorer)

    assert [f.rule_id for f in result.findings] == ["github-token"]
    assert result.below_threshold == 1
    assert result.threshold == 0.5


def test_threshold_is_inclusive(rng: random.Random) -> None:
    source = ListSource(chunk("ghp_" + random_token(rng, 36)))

    result = scan(source, DETECTORS, threshold=1.0, scorer=pass_through_score)

    assert len(result.findings) == 1


@pytest.mark.parametrize("threshold", [-0.1, 1.1])
def test_threshold_out_of_range_is_rejected(threshold: float) -> None:
    with pytest.raises(ValueError, match="threshold"):
        scan(ListSource(), DETECTORS, threshold=threshold)
