import random
import time

import pytest

from tests.conftest import random_token
from tokenhound.detectors.entropy import EntropyDetector, shannon_entropy
from tokenhound.detectors.regex_engine import RegexDetector
from tokenhound.detectors.rule_schema import Rule
from tokenhound.models import Chunk, Severity


def make_rule(**overrides: object) -> Rule:
    data: dict[str, object] = {
        "id": "test-token",
        "provider": "Test",
        "description": "Synthetic test token",
        "regex": r"\b(tst_[A-Za-z0-9]{20})\b",
        "secret_group": 1,
        "keywords": ["tst_"],
        "severity": "critical",
        "remediation": "Rotate the test token.",
        "references": ["https://example.com/docs/tokens"],
    }
    data.update(overrides)
    return Rule.model_validate(data)


def chunk(text: str, path: str = "app.py") -> Chunk:
    return Chunk(path=path, commit=None, line_no=1, text=text)


# --- regex engine -------------------------------------------------------------------------


def test_regex_detector_reports_the_secret_group(rng: random.Random) -> None:
    secret = "tst_" + random_token(rng, 20)
    text = f"import os\nclient = Client(api_key='{secret}')\n"

    [candidate] = RegexDetector([make_rule()]).detect(chunk(text))

    assert candidate.rule_id == "test-token"
    assert candidate.match == secret
    assert text[candidate.span[0] : candidate.span[1]] == secret
    assert candidate.line_no == 2
    assert candidate.severity is Severity.CRITICAL
    assert candidate.remediation == "Rotate the test token."


def test_regex_detector_finds_every_occurrence(rng: random.Random) -> None:
    secrets = ["tst_" + random_token(rng, 20) for _ in range(3)]
    text = "\n".join(f"KEY_{i}={s}" for i, s in enumerate(secrets))

    found = [c.match for c in RegexDetector([make_rule()]).detect(chunk(text))]

    assert found == secrets


def test_keyword_prefilter_skips_rule_when_keyword_absent(rng: random.Random) -> None:
    # The regex would match, but the rule only runs when its keyword is present.
    rule = make_rule(keywords=["unrelated"])
    text = "tst_" + random_token(rng, 20)

    assert list(RegexDetector([rule]).detect(chunk(text))) == []


def test_keyword_prefilter_is_case_insensitive(rng: random.Random) -> None:
    rule = make_rule(keywords=["TST_"])
    text = "tst_" + random_token(rng, 20)

    assert len(list(RegexDetector([rule]).detect(chunk(text)))) == 1


def test_rule_without_keywords_always_runs(rng: random.Random) -> None:
    text = "tst_" + random_token(rng, 20)

    assert len(list(RegexDetector([make_rule(keywords=[])]).detect(chunk(text)))) == 1


def test_empty_optional_group_is_ignored() -> None:
    rule = make_rule(regex=r"token:(tst_[a-z]{3})?", secret_group=1, keywords=[])

    assert list(RegexDetector([rule]).detect(chunk("token:"))) == []


def test_no_match_yields_nothing() -> None:
    detector = RegexDetector([make_rule()])

    assert detector.rules[0].id == "test-token"
    assert list(detector.detect(chunk("tst_short and nothing else"))) == []


# --- entropy ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [("", 0.0), ("aaaa", 0.0), ("ab", 1.0), ("abcd", 2.0), ("abcdefgh", 3.0)],
)
def test_shannon_entropy_known_values(value: str, expected: float) -> None:
    assert shannon_entropy(value) == pytest.approx(expected)


@pytest.mark.parametrize(
    "template",
    [
        'db_password = "{v}"',
        "API_KEY={v}",
        '"client_secret": "{v}",',
        "auth_token: {v}",
        "const accessToken = `{v}`;",
        "$secretKey => '{v}'",
        "token = '{v}'",
        "PASSWORD={v}",
        "connect(password={v})",
        "{{secret: {v}}}",
    ],
)
def test_entropy_detector_flags_random_values_in_secret_assignments(
    rng: random.Random, template: str
) -> None:
    value = random_token(rng, 32)
    text = template.format(v=value)

    [candidate] = EntropyDetector().detect(chunk(text))

    assert candidate.match == value
    assert text[candidate.span[0] : candidate.span[1]] == value
    assert candidate.rule_id == "generic-high-entropy"
    assert candidate.severity is Severity.MEDIUM


@pytest.mark.parametrize(
    "text",
    [
        'api_key = "your-api-key-here"',  # placeholder: long but low entropy
        'password = "aaaaaaaaaaaaaaaaaaaaaaaa"',
        'token = "Ab3dE5"',  # too short
        'username = "q8ZrT2mXv9LpW4sK7nB1cY6d"',  # name is not secret-like
        "the key is important",  # no assignment
        "keywords = self._keywords_by_rule_identifier[rule.id]",  # code, not a literal
        "secret = match.group(rule.secret_group_name)",
        "token=compute_token_for_the_user(x)",
    ],
)
def test_entropy_detector_ignores_non_secrets(text: str) -> None:
    assert list(EntropyDetector().detect(chunk(text))) == []


def test_entropy_thresholds_are_configurable(rng: random.Random) -> None:
    text = f"token = '{random_token(rng, 10)}'"

    assert list(EntropyDetector().detect(chunk(text))) == []
    assert len(list(EntropyDetector(min_length=8, min_entropy=2.0).detect(chunk(text)))) == 1


@pytest.mark.parametrize(("min_length", "min_entropy"), [(0, 3.0), (10, -1.0)])
def test_entropy_detector_rejects_invalid_thresholds(min_length: int, min_entropy: float) -> None:
    with pytest.raises(ValueError):
        EntropyDetector(min_length=min_length, min_entropy=min_entropy)


def test_entropy_detector_is_linear_on_huge_identifiers() -> None:
    # Regression: an unbounded name pattern backtracked quadratically (50k chars took ~23 s).
    text = "key" * 30_000

    start = time.perf_counter()
    assert list(EntropyDetector().detect(chunk(text))) == []
    assert time.perf_counter() - start < 2.0
