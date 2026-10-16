# TokenHound

[![CI](https://github.com/jdexbarr/tokenhound/actions/workflows/ci.yml/badge.svg)](https://github.com/jdexbarr/tokenhound/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Secret scanner for AI-era codebases, with a machine-learning false-positive classifier.**

TokenHound scans source code and full git history for leaked credentials (API keys, tokens,
passwords, private keys). It focuses on the modern AI stack: dedicated detectors for AI providers
and priority scanning of MCP / agent configs, notebooks and `.env` files. A classifier trained on
context (variable names, file paths, string shape) filters out placeholders and example values.

> **Status: pre-alpha (Phase F0, project skeleton).** No scanning yet. See the
> [development plan](docs/DEVELOPMENT_PLAN.md) for the roadmap.

## Planned features (MVP)

- `tokenhound scan` over the working tree, `--history` over the whole git history, `--staged` for pre-commit
- Rules in YAML plus a Shannon-entropy detector
- ML confidence score for every finding, filtered by a configurable threshold
- Baseline / allowlist file (`.tokenhound-baseline.json`)
- Terminal (Rich), JSON and SARIF 2.1.0 output; secrets are always masked
- pre-commit hook and GitHub Action

## Development

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/jdexbarr/tokenhound
cd tokenhound
uv sync                      # create .venv and install dependencies
uv run pre-commit install    # enable git hooks (ruff, mypy, basic checks)
uv run tokenhound version
```

Quality checks (the same ones CI runs):

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov
```

## Project documents

- [Requirements and traceability](docs/REQUIREMENTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Development plan](docs/DEVELOPMENT_PLAN.md)
- [Test plan](docs/TEST_PLAN.md)
- [Decision log](docs/DECISIONS.md)
- [Security policy and threat model](SECURITY.md)

## License

[MIT](LICENSE)
