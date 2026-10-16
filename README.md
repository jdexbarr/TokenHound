# TokenHound

[![CI](https://github.com/jdexbarr/tokenhound/actions/workflows/ci.yml/badge.svg)](https://github.com/jdexbarr/tokenhound/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Secret scanner for AI-era codebases, with a machine-learning false-positive classifier.**

TokenHound scans source code and full git history for leaked credentials (API keys, tokens,
passwords, private keys). It focuses on the modern AI stack: dedicated detectors for AI providers
and priority scanning of MCP / agent configs, notebooks and `.env` files. A classifier trained on
context (variable names, file paths, string shape) filters out placeholders and example values.

> **Status: pre-alpha (Phase F1, detection engine).** Detectors and rules exist; the `scan`
> command arrives with milestone H4. See the [development plan](docs/DEVELOPMENT_PLAN.md).

## Detected secret types

| Provider / type | Rule id | Severity |
|---|---|---|
| AWS access key ID | `aws-access-key-id` | critical |
| GitHub tokens (classic, OAuth, app, refresh) | `github-token` | critical |
| GitHub fine-grained PAT | `github-fine-grained-pat` | critical |
| Anthropic Admin API key | `anthropic-admin-key` | critical |
| Anthropic API key | `anthropic-api-key` | high |
| OpenAI API key | `openai-api-key` | high |
| Hugging Face token | `huggingface-token` | high |
| Stripe live secret / restricted key | `stripe-live-key` | critical |
| Slack tokens | `slack-token` | high |
| Google API key | `google-api-key` | medium |
| PEM private key | `private-key` | critical |
| JWT (high if it grants a privileged role, e.g. Supabase `service_role`) | `jwt` | medium / high |
| Replicate API token | `replicate-api-token` | high |
| Generic high-entropy secret assignment | `generic-high-entropy` | medium |

Rules are YAML files in [`src/tokenhound/detectors/rules/`](src/tokenhound/detectors/rules/), each
citing the provider's official documentation.

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
