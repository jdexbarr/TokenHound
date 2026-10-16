# Test plan

Every mandatory requirement has a verification method in `docs/REQUIREMENTS.md`. This document
describes the strategy and records test cases with their results.

## Strategy

| Level | What | Tooling |
|---|---|---|
| Unit | Models, masking, fingerprint, rule schema, each rule (valid/invalid examples), entropy, features, reporters | pytest |
| Integration | Each source against temporary git repos built by pytest fixtures (`tmp_path` + `git init`); full `scan` runs | pytest, GitPython |
| CLI | Commands, flags, exit codes, help | `typer.testing.CliRunner` |
| Schema | SARIF output validated against the official SARIF 2.1.0 JSON schema | jsonschema (dev only) |
| Security | Cross-cutting: scan fixtures with known synthetic secrets and assert none appears unmasked in stdout, JSON, SARIF, baseline or logs | pytest |
| ML | Split leakage check, dataset contains no candidate values, metrics reproducible with fixed seed | pytest + notebook |
| Performance | History scan of a large repo, timed and documented | benchmark script |
| Manual acceptance | Action + hook in an example repo; SARIF visible in GitHub Security tab | checklist |

Rules:

- Secrets in tests are **synthetic** and generated at test time, never committed as realistic literals.
- Coverage target ≥ 80% for `sources`, `detectors`, `reporters` (NFR-007), measured with pytest-cov.
- A failing test is never deleted or weakened to make the suite pass; corrections are justified here.
- Results distinguish tests with fakes/mocks from tests against real integrations (GitHub, PyPI).

## Test cases

| Test ID | Requirement | Setup | Steps | Expected | Actual | Status |
|---|---|---|---|---|---|---|
| T-001 | FR-005, UI-001 | `uv sync` | `tokenhound version` via CliRunner | exit 0, prints `tokenhound <version>` | as expected (local) | VERIFIED (local) |
| T-002 | UI-001 | — | run with no arguments | help listing `version` | as expected (local) | VERIFIED (local) |
| T-003 | UI-001 | — | run unknown command | non-zero exit | as expected (local) | VERIFIED (local) |
| T-004 | DEL-002, TECH-001 | GitHub Actions | CI matrix 3.11–3.13 | all jobs green | green ([run](https://github.com/jdexbarr/TokenHound/actions/runs/38849756675)) | VERIFIED |
| T-005 | NFR-008 (partial) | CI build job | build wheel, install in clean venv, run `tokenhound version` | prints version | passed locally and in CI ([run](https://github.com/jdexbarr/TokenHound/actions/runs/38849756675)) | VERIFIED |
| T-006 | UI-004, FR-025 | — | `mask()` on fixed examples and random secrets of length 1–119 | same length, never equal to the secret, ≤ 8 characters revealed | as expected | VERIFIED (local) |
| T-007 | FR-017 | — | `fingerprint()` determinism, dependence on secret and path, separator | stable 64-hex digest; no split collisions | as expected | VERIFIED (local) |
| T-008 | FR-021, NFR-001 | synthetic candidate | build `Finding`; inspect fields and reprs | masked value, SHA-256 fingerprint, no raw secret anywhere, frozen | as expected | VERIFIED (local) |
| T-009 | FR-006 | temp YAML files | load valid/invalid rule files | valid rules load in name order; each schema violation raises `RuleLoadError` naming the file; duplicate ids rejected | as expected | VERIFIED (local) |
| T-010 | FR-013, FR-019 | synthetic `tst_` rule | run `RegexDetector` | secret group, span, line, severity and remediation correct; keyword prefilter works | as expected | VERIFIED (local) |
| T-011 | FR-007 | random 32-char values | run `EntropyDetector` on 8 assignment styles and 5 non-secrets | flags the random values only | as expected | VERIFIED (local) |
| T-012 | FR-007 (robustness) | 90k-char identifier | run `EntropyDetector` | finishes in < 2 s (was ~23 s for 50k before the fix) | as expected | VERIFIED (local) |
