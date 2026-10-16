import random
import re

import pytest

from tests.conftest import random_token
from tokenhound.utils.fingerprint import fingerprint
from tokenhound.utils.masking import mask


@pytest.mark.parametrize(
    ("secret", "expected"),
    [
        ("", ""),
        ("abc", "***"),
        ("123456789", "*********"),
        ("1234567890", "12******90"),
        ("abcdefghijklmnopqrs", "ab***************rs"),
        ("sk-abcdefghijklmnxYz9", "sk-a*************xYz9"),
    ],
)
def test_mask_examples(secret: str, expected: str) -> None:
    assert mask(secret) == expected


@pytest.mark.parametrize("length", range(1, 120))
def test_mask_keeps_length_and_never_returns_the_secret(rng: random.Random, length: int) -> None:
    secret = random_token(rng, length)

    masked = mask(secret)

    assert len(masked) == length
    assert masked != secret
    # At most 8 characters (4 per side) are ever revealed.
    assert sum(ch != "*" for ch in masked) <= 8


def test_fingerprint_is_sha256_hex_and_deterministic() -> None:
    first = fingerprint("tst_value", "src/app.py")

    assert re.fullmatch(r"[0-9a-f]{64}", first)
    assert first == fingerprint("tst_value", "src/app.py")


def test_fingerprint_depends_on_secret_and_path() -> None:
    base = fingerprint("tst_value", "src/app.py")

    assert base != fingerprint("tst_other", "src/app.py")
    assert base != fingerprint("tst_value", "src/other.py")


def test_fingerprint_separates_secret_from_path() -> None:
    assert fingerprint("ab", "c") != fingerprint("a", "bc")
