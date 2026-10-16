# Development plan

Milestones follow the spec roadmap (§10, p.9). Each phase ends with green tests, an updated README and
a git tag. Statuses: NOT STARTED · IN PROGRESS · BLOCKED · IMPLEMENTED – PENDING VERIFICATION ·
VERIFIED · ACCEPTED.

## Current state (2026-10-16)

- **Current milestone:** H2 — detection core (phase F1)
- **Done:** H0 plan; H1 skeleton merged (PR #1).
- **In progress:** H2 pull request (`h2-core`).
- **Blockers:** tag `f0` must be created by Juan (the cloud environment cannot push tags).
- **Failing / pending tests:** none.
- **Next three actions:**
  1. Merge H2 once CI is green.
  2. H3: research current key formats in official provider docs; write the 11 YAML rules.
  3. H3: per-rule tests with synthetic keys generated at test time; JWT privilege elevation.

## Milestones

| ID | Phase | Goal | Requirements | Depends on | Status |
|---|---|---|---|---|---|
| H0 | — | Spec analysis, requirements, architecture, plan | all | — | ACCEPTED |
| H1 | F0 | Professional skeleton | TECH-001…003, TECH-008, NFR-011, NFR-020, DEL-001/002/016/019 | H0 | VERIFIED (merged, PR #1) |
| H2 | F1 | Core models, masking, fingerprint, rule schema/loader, regex engine, entropy detector | FR-006/007/013/017/019/021/025, NFR-001 | H1 | VERIFIED (local; CI pending) |
| H3 | F1 | 11 YAML rules validated against official docs, remediation, per-rule tests, JWT elevation | FR-008/009/010/020, NFR-005, NFR-012 | H2 | NOT STARTED |
| H4 | F1 | Working-tree source, orchestrator, AI-priority files, Rich + JSON output, exit codes | FR-001/004/011/022/023/039 | H3 | NOT STARTED |
| H5 | F2 | Git history (diffs, cache), staged source, dedup, first speed measurement | FR-002/003/017, NFR-006 | H4 | NOT STARTED |
| H6 | F2 | Baseline/allowlist, `baseline` command, pre-commit hook | FR-005/018/026 | H5 | NOT STARTED |
| H7 | F3 | Dataset: synthetic generator, hard negatives, real negatives (pointers), labeling script, split by repo | FR-029…033, NFR-002 | H6 | NOT STARTED |
| H8 | F3 | Features, training, evaluation notebook, threshold, model integration, `--no-ml` | FR-012/014/015/016/034…037, NFR-003/004 | H7 | NOT STARTED |
| H9 | F4 | SARIF, remediation guide, `action.yml`, Dockerfile, example repo | FR-024/027/028, DEL-009…012/017 | H8 | NOT STARTED |
| H10 | F5 | Gitleaks benchmark, speed docs, case-study README, final SECURITY.md, audit, publication (with approval) | FR-038, NFR-006/007/009, DEL-013…015/020 | H9 | NOT STARTED |

## H1 — Project skeleton (F0)

1. **Goal:** a repo that installs, lints, type-checks, tests and builds, locally and in CI.
2. **Requirements:** TECH-001…003, TECH-008, TECH-009 (CI part), NFR-011, NFR-020, DEL-001, DEL-002, DEL-016 (draft), DEL-019.
3. **Dependencies:** approved plan; GitHub repo `jdexbarr/tokenhound`.
4. **Tasks:** `pyproject.toml` (hatchling, uv dependency groups, ruff, mypy strict, pytest, coverage);
   package with `tokenhound version`; `.pre-commit-config.yaml`; CI workflow; README, LICENSE,
   SECURITY.md, IDEAS.md, CLAUDE.md, `docs/`.
5. **Files:** `pyproject.toml`, `uv.lock`, `src/tokenhound/{__init__,__main__,cli}.py`, `py.typed`,
   `tests/test_cli.py`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `.gitignore`, docs.
6. **Tests:** CLI tests (`version`, help, unknown command); wheel build + install smoke test in CI.
7. **Acceptance:** ruff, ruff format, mypy and pytest pass on Python 3.11, 3.12, 3.13 in CI; wheel
   installs and runs `tokenhound version`.
8. **Risks:** action versions or tooling drift in CI.
9. **Result:** tag `f0` after merge.

**Evidence (local, 2026-10-16, Python 3.13.16):** `ruff check` passed; `ruff format --check` passed;
`mypy` (strict) no issues in 4 files; `pytest` 3 passed, coverage 86% (`__main__.py` not covered,
exercised by `python -m tokenhound version` manually); `pre-commit run --all-files` all hooks passed;
`uv build` produced sdist + wheel and `tokenhound version` ran from a clean venv. CI on GitHub: all four jobs green (Python 3.11, 3.12, 3.13, build) on [run 38849756675](https://github.com/jdexbarr/TokenHound/actions/runs/38849756675).

## H2 — Detection core (F1)

1. **Goal:** the data model and the two detectors every later stage builds on.
2. **Requirements:** FR-006, FR-007, FR-013, FR-017 (fingerprint), FR-019, FR-021, FR-025 (masking), NFR-001, TECH-006, UI-004.
3. **Dependencies:** H1.
4. **Tasks:** `models.py` (Chunk, Candidate, Finding, Severity); `utils/masking.py`; `utils/fingerprint.py`;
   `detectors/rule_schema.py` (Pydantic schema + YAML loader); `detectors/regex_engine.py`;
   `detectors/entropy.py`; add PyYAML, Pydantic, types-PyYAML.
5. **Files:** the modules above, `detectors/rules/README.md`, `tests/conftest.py`, `tests/test_utils.py`,
   `tests/test_models.py`, `tests/test_rule_schema.py`, `tests/test_detectors.py`.
6. **Tests:** masking examples and property test over lengths 1–119; fingerprint determinism and
   separation; model invariants (no raw secret in fields or reprs, immutability, score range);
   rule validation errors; detector behaviour; entropy thresholds; ReDoS regression.
7. **Acceptance:** all tests pass; ruff and mypy strict clean; coverage of `detectors/` ≥ 80%.
8. **Risks found:** the first entropy regex missed bare names (`token = ...`) and backtracked
   quadratically on huge identifiers (50k chars: ~23 s). Both fixed and covered by tests.
9. **Result:** H3 can add provider rules as YAML only.

**Evidence (local, 2026-10-16, Python 3.13.16):** `pytest` 186 passed; coverage 99% overall,
`detectors/` 100%, `utils/` 100%, `models.py` 100%; ruff, ruff format, mypy strict (18 files) and
all pre-commit hooks pass; wheel includes `detectors/rules/`. CI: pending.

Detailed task breakdowns for H3+ are written when each milestone starts.
