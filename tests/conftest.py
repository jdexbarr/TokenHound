"""Shared test helpers.

All secrets used in tests are synthetic and generated at test time (see CLAUDE.md). The ``tst_``
prefix belongs to no real provider, so these values cannot trip secret-scanning push protection.
"""

import random
import string

import pytest

ALPHANUMERIC = string.ascii_letters + string.digits


def random_token(rng: random.Random, length: int, alphabet: str = ALPHANUMERIC) -> str:
    """Return a pseudo-random string; with a seeded ``rng`` the value is reproducible."""
    return "".join(rng.choice(alphabet) for _ in range(length))


@pytest.fixture
def rng() -> random.Random:
    return random.Random(1337)
