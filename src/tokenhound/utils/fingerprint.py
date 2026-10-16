"""Stable identifiers for findings, used for deduplication and the baseline file."""

import hashlib

_SEPARATOR = "\x00"


def fingerprint(secret: str, file_path: str) -> str:
    """Return ``sha256(secret + file_path)`` as a hex string (spec section 5).

    A NUL separator sits between the two parts so different splits of the same characters
    (``"ab" + "c"`` vs ``"a" + "bc"``) cannot collide.
    """
    data = f"{secret}{_SEPARATOR}{file_path}".encode()
    return hashlib.sha256(data).hexdigest()
