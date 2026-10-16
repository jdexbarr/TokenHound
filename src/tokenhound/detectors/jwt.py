"""JWT inspection used to raise the severity of privileged tokens (spec section 7).

The payload is decoded without verifying the signature: the goal is only to see which role the
token claims, e.g. a Supabase ``service_role`` key, which bypasses row-level security.
"""

from __future__ import annotations

import base64
import binascii
import json
from collections.abc import Iterable
from typing import Any

from tokenhound.models import Severity

PRIVILEGED_ROLES = frozenset(
    {"service_role", "admin", "administrator", "superuser", "root", "owner"}
)
_ROLE_CLAIMS = ("role", "roles", "scope", "scopes", "permissions", "groups")


def decode_payload(token: str) -> dict[str, Any] | None:
    """Return the JSON payload of ``token`` or ``None`` if it is not a decodable JWT."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    segment = parts[1]
    try:
        raw = base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))
        payload = json.loads(raw)
    except (binascii.Error, ValueError, RecursionError):
        # Not base64url, not UTF-8/JSON, or pathologically nested: treat as not a JWT.
        return None
    return payload if isinstance(payload, dict) else None


def _claim_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield from value.replace(",", " ").split()
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                yield item


def is_privileged(token: str) -> bool:
    """True when a role-like claim (or ``is_admin: true``) grants a privileged role."""
    payload = decode_payload(token)
    if payload is None:
        return False
    if payload.get("is_admin") is True:
        return True
    for claim in _ROLE_CLAIMS:
        if any(v.lower() in PRIVILEGED_ROLES for v in _claim_values(payload.get(claim))):
            return True
    return False


def jwt_severity(token: str, base: Severity) -> Severity:
    """``HIGH`` for privileged tokens (never lowering ``base``), otherwise ``base``."""
    if is_privileged(token) and Severity.HIGH.rank > base.rank:
        return Severity.HIGH
    return base
