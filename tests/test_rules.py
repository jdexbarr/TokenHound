"""Per-rule tests for the built-in provider rules (spec section 7, NFR-012).

Positive examples are generated at test time from the documented formats: only prefixes appear in
this file, never a complete key, so the repository holds no realistic credentials.
"""

import base64
import json
import random
import string
from collections.abc import Callable

import pytest

from tests.conftest import ALPHANUMERIC, random_token
from tokenhound.detectors.jwt import decode_payload, is_privileged, jwt_severity
from tokenhound.detectors.regex_engine import RegexDetector
from tokenhound.detectors.rule_schema import Rule, load_rules
from tokenhound.models import Chunk, Severity

RULES = load_rules()
RULES_BY_ID = {rule.id: rule for rule in RULES}
DETECTOR = RegexDetector(RULES)

UPPER_DIGITS = string.ascii_uppercase + string.digits
URLSAFE = ALPHANUMERIC + "_-"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def make_jwt(rng: random.Random, payload: dict[str, object]) -> str:
    header = b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = b64url(json.dumps(payload).encode())
    return f"{header}.{body}.{random_token(rng, 43, URLSAFE)}"


def make_pem(rng: random.Random, kind: str = "RSA ") -> str:
    body = "\n".join(random_token(rng, 64, ALPHANUMERIC + "+/") for _ in range(4))
    return f"-----BEGIN {kind}PRIVATE KEY-----\n{body}\n-----END {kind}PRIVATE KEY-----"


Generator = Callable[[random.Random], str]

# rule id -> generators of valid synthetic secrets in that rule's format.
POSITIVES: dict[str, list[Generator]] = {
    "aws-access-key-id": [
        lambda r: "AKIA" + random_token(r, 16, UPPER_DIGITS),
        lambda r: "ASIA" + random_token(r, 16, UPPER_DIGITS),
    ],
    "github-token": [
        lambda r, p=prefix: f"{p}_" + random_token(r, 36)  # type: ignore[misc]
        for prefix in ("ghp", "gho", "ghu", "ghs", "ghr")
    ],
    "github-fine-grained-pat": [
        lambda r: "github_pat_" + random_token(r, 22) + "_" + random_token(r, 59),
    ],
    "anthropic-admin-key": [
        lambda r: "sk-ant-admin01-" + random_token(r, 80, URLSAFE),
    ],
    "anthropic-api-key": [
        lambda r: "sk-ant-api03-" + random_token(r, 93, URLSAFE) + "AA",
    ],
    "openai-api-key": [
        lambda r: "sk-proj-" + random_token(r, 120, URLSAFE),
        lambda r: "sk-svcacct-" + random_token(r, 120, URLSAFE),
        lambda r: "sk-admin-" + random_token(r, 80, URLSAFE),
        lambda r: "sk-" + random_token(r, 48),
    ],
    "huggingface-token": [lambda r: "hf_" + random_token(r, 34, string.ascii_letters)],
    "stripe-live-key": [
        lambda r: "sk_live_" + random_token(r, 99),
        lambda r: "rk_live_" + random_token(r, 24),
    ],
    "slack-token": [
        lambda r: (
            f"xoxb-{r.randrange(10**11, 10**12)}-{r.randrange(10**12, 10**13)}-"
            + random_token(r, 24)
        ),
        lambda r: f"xoxp-{r.randrange(10**11, 10**12)}-" + random_token(r, 32),
        lambda r: "xapp-1-" + random_token(r, 11, UPPER_DIGITS) + "-" + random_token(r, 64),
        lambda r: "xoxe.xoxp-1-" + random_token(r, 120),
    ],
    "google-api-key": [lambda r: "AIza" + random_token(r, 35, URLSAFE)],
    "private-key": [
        make_pem,
        lambda r: make_pem(r, ""),
        lambda r: make_pem(r, "OPENSSH "),
        lambda r: make_pem(r, "EC "),
    ],
    "jwt": [lambda r: make_jwt(r, {"sub": "1234", "role": "anon"})],
    "replicate-api-token": [lambda r: "r8_" + random_token(r, 37)],
}

# Strings that look close to a rule's format but must not match it.
NEGATIVES: dict[str, list[Generator]] = {
    "aws-access-key-id": [
        lambda r: "AKIA" + random_token(r, 15, UPPER_DIGITS),
        lambda r: "AKIA" + random_token(r, 16, string.ascii_lowercase),
        lambda r: "XAKIA" + random_token(r, 16, UPPER_DIGITS),
    ],
    "github-token": [
        lambda r: "ghp_" + random_token(r, 35),
        lambda r: "ghx_" + random_token(r, 36),
    ],
    "github-fine-grained-pat": [lambda r: "github_pat_" + random_token(r, 40)],
    "anthropic-api-key": [lambda r: "sk-ant-" + random_token(r, 10)],
    "openai-api-key": [
        lambda r: "sk-" + random_token(r, 10),
        lambda r: "sk-ant-api03-" + random_token(r, 95, URLSAFE),
    ],
    "huggingface-token": [lambda r: "hf_" + random_token(r, 12)],
    "stripe-live-key": [
        lambda r: "sk_test_" + random_token(r, 24),
        lambda r: "pk_live_" + random_token(r, 24),
    ],
    "slack-token": [lambda r: "xoxb-123", lambda r: "xoxz-" + random_token(r, 20)],
    "google-api-key": [
        lambda r: "AIza" + random_token(r, 34, URLSAFE),
        lambda r: "AIza" + random_token(r, 40, URLSAFE),
    ],
    "private-key": [
        lambda r: "-----BEGIN PUBLIC KEY-----\n" + random_token(r, 64),
        lambda r: "-----BEGIN CERTIFICATE-----\n" + random_token(r, 64),
    ],
    "jwt": [lambda r: "eyJhbGciOiJIUzI1NiJ9", lambda r: "eyJ" + random_token(r, 20) + ".abc"],
    "replicate-api-token": [lambda r: "r8_" + random_token(r, 36)],
}


def scan(text: str) -> list[tuple[str, str]]:
    chunk = Chunk(path="config.txt", commit=None, line_no=1, text=text)
    return [(c.rule_id, c.match) for c in DETECTOR.detect(chunk)]


def test_every_builtin_rule_has_examples() -> None:
    assert set(POSITIVES) == set(RULES_BY_ID)
    assert set(NEGATIVES) <= set(RULES_BY_ID)


def test_rule_set_covers_at_least_ten_secret_types() -> None:
    providers = {rule.provider for rule in RULES}

    assert len(providers) >= 10  # NFR-005 (plus the generic entropy detector)


@pytest.mark.parametrize("rule", RULES, ids=lambda r: r.id)
def test_rule_cites_an_https_source_and_has_remediation(rule: Rule) -> None:
    assert all(str(url).startswith("https://") for url in rule.references)
    assert len(rule.remediation) > 40


@pytest.mark.parametrize(
    ("rule_id", "generator"),
    [(rule_id, gen) for rule_id, gens in POSITIVES.items() for gen in gens],
)
@pytest.mark.parametrize("template", ["{s}", 'API_KEY = "{s}"', '{{"token": "{s}"}}', "x={s}\n"])
def test_positive_examples_match_only_their_rule(
    rng: random.Random, rule_id: str, generator: Generator, template: str
) -> None:
    secret = generator(rng)

    found = scan(template.format(s=secret))

    assert found == [(rule_id, secret)]


@pytest.mark.parametrize(
    ("rule_id", "generator"),
    [(rule_id, gen) for rule_id, gens in NEGATIVES.items() for gen in gens],
)
def test_negative_examples_do_not_match_their_rule(
    rng: random.Random, rule_id: str, generator: Generator
) -> None:
    text = f'value = "{generator(rng)}"'

    assert rule_id not in {found_rule for found_rule, _ in scan(text)}


def test_private_key_header_alone_is_reported(rng: random.Random) -> None:
    pem = make_pem(rng)
    header_only = pem.split("\n")[0]

    assert scan(header_only) == [("private-key", header_only)]


@pytest.mark.parametrize(
    "context",
    [
        # MCP / agent config (spec section 7, AI-priority files)
        '{{"mcpServers": {{"github": {{"env": {{"GITHUB_TOKEN": "{s}"}}}}}}}}',
        # .env file
        "GITHUB_TOKEN={s}\nDEBUG=true\n",
        # Python client construction
        'client = Github(auth=Auth.Token("{s}"))',
        # YAML CI workflow
        "env:\n  GH_TOKEN: {s}\n",
    ],
)
def test_secrets_are_found_in_realistic_contexts(rng: random.Random, context: str) -> None:
    secret = "ghp_" + random_token(rng, 36)

    assert scan(context.format(s=secret)) == [("github-token", secret)]


# --- JWT privilege elevation (spec section 7: "Alta si el payload indica rol privilegiado") ---


@pytest.mark.parametrize(
    "payload",
    [
        {"role": "service_role", "iss": "supabase"},
        {"roles": ["user", "Admin"]},
        {"scope": "read:all superuser"},
        {"is_admin": True},
    ],
)
def test_privileged_jwt_is_high_severity(rng: random.Random, payload: dict[str, object]) -> None:
    token = make_jwt(rng, payload)
    chunk = Chunk(path="supabase.ts", commit=None, line_no=1, text=f"const key = '{token}'")

    [candidate] = DETECTOR.detect(chunk)

    assert candidate.rule_id == "jwt"
    assert candidate.severity is Severity.HIGH


@pytest.mark.parametrize(
    "payload",
    [{"role": "anon"}, {"roles": ["reader"]}, {"is_admin": "yes"}, {"sub": "42"}],
)
def test_unprivileged_jwt_keeps_rule_severity(
    rng: random.Random, payload: dict[str, object]
) -> None:
    token = make_jwt(rng, payload)

    assert not is_privileged(token)
    assert jwt_severity(token, Severity.MEDIUM) is Severity.MEDIUM


def test_jwt_severity_never_lowers_the_base(rng: random.Random) -> None:
    token = make_jwt(rng, {"role": "service_role"})

    assert jwt_severity(token, Severity.CRITICAL) is Severity.CRITICAL


@pytest.mark.parametrize(
    "token",
    [
        "only.two",
        "a.%%%.c",
        "a." + b64url(b"not json") + ".c",
        "a." + b64url(b"[1, 2]") + ".c",
        "a." + b64url(b"[" * 100_000 + b"]" * 100_000) + ".c",
    ],
)
def test_undecodable_payloads_are_not_privileged(token: str) -> None:
    assert decode_payload(token) is None
    assert not is_privileged(token)
