# Development plan

Milestones follow the spec roadmap (§10, p.9). Each phase ends with green tests, an updated README and
a git tag. Statuses: NOT STARTED · IN PROGRESS · BLOCKED · IMPLEMENTED – PENDING VERIFICATION ·
VERIFIED · ACCEPTED.

## Current state (2026-10-16)

- **Current milestone:** H4 — working-tree scan and output (last milestone of phase F1)
- **Done:** H0 plan; H1 skeleton (PR #1); H2 detection core (PR #2); H3 provider rules (PR #3).
- **In progress:** H4 pull request (`h4-scan`).
- **Blockers:** tags `f0` and, after H4 merges, `f1` must be created by Juan (the cloud environment
  cannot push tags).
- **Failing / pending tests:** none.
- **Next three actions:**
  1. Merge H4 once CI is green; Juan tags `f1`.
  2. H5: `GitHistorySource` (streamed `git log -p`, added lines only, blob cache) and `--history`.
  3. H5: `StagedSource` and `--staged`, dedup by fingerprint, first speed measurement.

## Milestones

| ID | Phase | Goal | Requirements | Depends on | Status |
|---|---|---|---|---|---|
| H0 | — | Spec analysis, requirements, architecture, plan | all | — | ACCEPTED |
| H1 | F0 | Professional skeleton | TECH-001…003, TECH-008, NFR-011, NFR-020, DEL-001/002/016/019 | H0 | VERIFIED (merged, PR #1) |
| H2 | F1 | Core models, masking, fingerprint, rule schema/loader, regex engine, entropy detector | FR-006/007/013/017/019/021/025, NFR-001 | H1 | VERIFIED (merged, PR #2) |
| H3 | F1 | 11 YAML rules validated against official docs, remediation, per-rule tests, JWT elevation | FR-008/009/010/020, NFR-005, NFR-012 | H2 | VERIFIED (merged, PR #3) |
| H4 | F1 | Working-tree source, orchestrator, AI-priority files, Rich + JSON output, exit codes | FR-001/004/011/022/023/039 | H3 | VERIFIED (local; CI on the H4 PR) |
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
all pre-commit hooks pass; wheel includes `detectors/rules/`. CI: green on Python 3.11–3.13 and build
([run 38852192242](https://github.com/jdexbarr/TokenHound/actions/runs/38852192242)).

## H3 — Provider rules (F1)

1. **Goal:** the initial rule set of spec §7, each pattern checked against official documentation.
2. **Requirements:** FR-008, FR-009, FR-010, FR-020 (per-rule remediation), NFR-005, NFR-012.
3. **Dependencies:** H2 (rule schema, regex engine).
4. **Tasks:** 11 YAML files (13 rules); `detectors/jwt.py` and severity adjusters in the regex engine;
   per-rule tests.
5. **Files:** `src/tokenhound/detectors/rules/*.yaml`, `src/tokenhound/detectors/jwt.py`,
   `src/tokenhound/detectors/regex_engine.py`, `tests/test_rules.py`.
6. **Tests:** every rule has generated positives (in 4 surrounding contexts) that match only that
   rule, and near-miss negatives; MCP/.env/Python/YAML contexts; JWT elevation and malformed tokens;
   reference and remediation presence; rule-count check for NFR-005.
7. **Acceptance:** all rule tests pass; no realistic key literal committed.
8. **Risks:** OpenAI does not document its key format (rule based on issued prefixes); the
   generic `sk-` OpenAI pattern is broad and relies on the classifier for precision (H8).
9. **Result:** 11 providers / 13 rules + generic entropy detector.

**Sources checked (2026-10-16):** AWS IAM unique identifiers; GitHub token-format blog posts and
PAT docs; Claude Console API key and Admin key docs; OpenAI API key safety article; Hugging Face
security tokens; Stripe API keys and restricted keys; Slack token types; Google Cloud API key best
practices; Replicate API tokens; RFC 7468 (PEM) and RFC 7519 (JWT). Each YAML file cites its URLs.

**Evidence (local, 2026-10-16, Python 3.13.16):** `pytest` 353 passed (167 rule tests); coverage
99%; ruff, ruff format and mypy strict (20 files) clean. CI: green on Python 3.11–3.13 and build
([run 38852619611](https://github.com/jdexbarr/TokenHound/actions/runs/38852619611)).

## H4 — Working-tree scan and output (F1)

1. **Goal:** `tokenhound scan <dir>` works end to end on the working tree, with terminal and JSON
   output and exit codes. Closes phase F1.
2. **Requirements:** FR-001, FR-004 (working tree), FR-011, FR-022, FR-023, FR-025, FR-039, UI-003,
   TECH-004, NFR-001 (output part).
3. **Dependencies:** H3.
4. **Tasks:** `errors.py`; `sources/` (`Source` protocol, `priority.py` file kinds,
   `working_tree.py`, `notebook.py`); `Detector` protocol; `scanner.py` (overlap handling,
   threshold, sorting); `reporters/` (`Reporter` protocol, Rich terminal, JSON); `scan` command;
   tighter bare-value matching in the entropy detector.
5. **Files:** the modules above, `cli.py`, tests `test_priority.py`, `test_working_tree.py`,
   `test_scanner.py`, `test_reporters.py`, `test_cli.py`, `test_no_secret_leak.py`.
6. **Tests:** file walking and skip rules (`.git/`, symlinks, binaries, size limits, unreadable
   files); notebook sources and outputs with line numbers in the `.ipynb`; overlap and threshold
   logic; JSON shape; terminal snapshot and control-character neutralisation; CLI exit codes and
   errors; one synthetic secret per rule planted in MCP config, `.env` and notebook output, checked
   absent from every output format and the verbose log.
7. **Acceptance:** all of the above pass; ruff, ruff format and mypy strict clean.
8. **Risks found:** a self-scan of this repo produced 464 candidates, almost all from `.venv/`
   (A-09 scans everything outside `.git/`) and from code such as `secret = match.group(...)`. Bare
   values that contain or end in code punctuation are no longer entropy candidates (464 → 73;
   the rest are in `.venv/` plus a handful of identifiers the classifier must learn, e.g.
   `monkeypatch`). Excluding dependency folders is noted in `IDEAS.md` pending Juan's decision.
9. **Result:** phase F1 complete after merge; tag `f1`.

**Evidence (local, 2026-10-16, Python 3.13.16):** `pytest` 437 passed, 1 skipped (the unreadable-file
test is skipped when running as root; the same path is covered by a monkeypatched test); coverage 99%
(`sources/`, `reporters/`, `scanner.py`, `cli.py` 100%); ruff, ruff format, mypy strict and all
pre-commit hooks pass. CI: pending.

Detailed task breakdowns for H4+ are written when each milestone starts.
