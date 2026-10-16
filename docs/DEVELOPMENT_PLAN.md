# Development plan

Milestones follow the spec roadmap (§10, p.9). Each phase ends with green tests, an updated README and
a git tag. Statuses: NOT STARTED · IN PROGRESS · BLOCKED · IMPLEMENTED – PENDING VERIFICATION ·
VERIFIED · ACCEPTED.

## Current state (2026-10-16)

- **Current milestone:** H1 — project skeleton (phase F0)
- **Done:** H0 analysis and plan approved by Juan; name chosen (TokenHound); repo created.
- **In progress:** H1 pull request #1 (`f0-setup`): CI green, waiting for Juan's review and merge.
- **Blockers:** none.
- **Failing / pending tests:** none.
- **Next three actions:**
  1. Get H1 CI green, Juan merges, tag `f0`.
  2. H2: `models.py`, masking, fingerprint, rule schema and loader.
  3. H2: regex engine and entropy detector with unit tests.

## Milestones

| ID | Phase | Goal | Requirements | Depends on | Status |
|---|---|---|---|---|---|
| H0 | — | Spec analysis, requirements, architecture, plan | all | — | ACCEPTED |
| H1 | F0 | Professional skeleton | TECH-001…003, TECH-008, NFR-011, NFR-020, DEL-001/002/016/019 | H0 | VERIFIED |
| H2 | F1 | Core models, masking, fingerprint, rule schema/loader, regex engine, entropy detector | FR-006/007/013/017/019/021/025, NFR-001 | H1 | NOT STARTED |
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

Detailed task breakdowns for H2+ are written when each milestone starts.
