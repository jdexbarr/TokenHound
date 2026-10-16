# TokenHound — instructions for Claude Code

TokenHound is an open-source Python CLI that scans repositories (working tree, staged changes, full git
history) for leaked secrets, scores each candidate with a scikit-learn false-positive classifier, and
reports to the terminal, JSON or SARIF 2.1.0. It also ships a pre-commit hook and a GitHub Action.

The spec PDF (`KeyHound_Especificacion.pdf`, v1.0, the project's original name) is the source of truth
for scope, architecture, stack and roadmap. Requirement IDs (FR/NFR/TECH/UI/DEL) and page references live
in `docs/REQUIREMENTS.md`.

## Working rules

- Talk to Juan in **Spanish**. Everything in the repo (code, comments, commits, docs) is in **English**.
- Respect the MVP scope (spec §4). Out-of-scope ideas go to `IDEAS.md`, never into the code without approval.
- Work milestone by milestone (`docs/DEVELOPMENT_PLAN.md`). Do not start a phase until the previous one
  has green tests and an updated README (spec §10, "golden rule"). Tag the last commit of each phase.
- Every code change comes with pytest tests and passes ruff and mypy (strict).
- Never print, log or store a full secret. Output only masked values; fingerprints are SHA-256.
- Tests use **synthetic** secrets only, generated at test time (do not commit realistic fake keys: they
  trip GitHub push protection and our own scanner).
- Never call provider APIs to validate keys (out of scope; spec §9).
- Ask Juan before anything external or irreversible: publishing to PyPI / Marketplace / GHCR, creating
  releases, changing repo settings.
- Statuses: NOT STARTED, IN PROGRESS, BLOCKED, IMPLEMENTED – PENDING VERIFICATION, VERIFIED, ACCEPTED.
  A task is VERIFIED only with recorded evidence (test output, CI run). Only Juan marks ACCEPTED.
- Record significant decisions in `docs/DECISIONS.md`.

## Stack (mandatory, spec §6)

Python 3.11+, uv + `pyproject.toml`, Typer, Rich, GitPython (pygit2 only as a later optimisation),
PyYAML + Pydantic, scikit-learn + pandas + joblib (LightGBM optional), pytest, ruff, mypy, pre-commit,
GitHub Actions, PyPI trusted publishing, Docker.

## Commands

```bash
uv sync                          # install runtime + dev dependencies
uv run pytest --cov              # tests with coverage
uv run ruff check . && uv run ruff format --check .
uv run mypy                      # strict type check (src + tests)
uv run pre-commit run --all-files
uv run tokenhound version        # smoke test
uv build                         # sdist + wheel
```

## Layout

`src/tokenhound/` package (pipeline: sources → detectors → context → classifier → reporters, see
`docs/ARCHITECTURE.md`), `tests/`, `ml/` (dataset + training), `benchmarks/`, `docs/`.

## Docs map

- `docs/REQUIREMENTS.md` — traceability matrix with status
- `docs/DEVELOPMENT_PLAN.md` — milestones, current state, next actions
- `docs/ARCHITECTURE.md` — design and interfaces
- `docs/TEST_PLAN.md` — test strategy and cases
- `docs/DECISIONS.md` — decision log
