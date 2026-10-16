# TokenHound

[![CI](https://github.com/jdexbarr/tokenhound/actions/workflows/ci.yml/badge.svg)](https://github.com/jdexbarr/tokenhound/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Secret scanner for AI-era codebases, with a machine-learning false-positive classifier.**

TokenHound scans source code and full git history for leaked credentials (API keys, tokens,
passwords, private keys). It focuses on the modern AI stack: dedicated detectors for AI providers
and priority scanning of MCP / agent configs, notebooks and `.env` files. A classifier trained on
context (variable names, file paths, string shape) filters out placeholders and example values.

> **Status: pre-alpha (end of Phase F1).** `tokenhound scan` works on the working tree with
> terminal and JSON output. Git history, the pre-commit hook, the ML classifier and SARIF come in
> later phases; until the classifier lands every finding has score 1.0. See the
> [development plan](docs/DEVELOPMENT_PLAN.md).

## Usage

```bash
tokenhound scan                      # scan the current directory
tokenhound scan path/to/repo         # scan a directory (or a single file)
tokenhound scan . --format json      # machine-readable output
tokenhound scan . --verbose          # also log skipped files to stderr
```

Exit codes: `0` no findings, `1` findings, `2` error. Example output (values are always masked):

```text
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Severity ┃ Rule                 ┃ Location           ┃ Value                                    ┃ Score ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ CRITICAL │ github-token         │ .cursor/mcp.json:5 │ ghp_********************************oL8g │  1.00 │
│ HIGH     │ huggingface-token    │ nb.ipynb:13        │ hf_S*****************************oaXm    │  1.00 │
│ MEDIUM   │ generic-high-entropy │ .env:2             │ mtsL****************lxJ4                 │  1.00 │
└──────────┴──────────────────────┴────────────────────┴──────────────────────────────────────────┴───────┘
```

What is scanned: every text file under the path except `.git/`, symbolic links, binaries and files
over 1 MiB. `.gitignore` is not honoured, since ignored files such as `.env` are where secrets live.
Priority files are scanned first and may be up to 20 MiB: MCP and agent configs (`mcp.json`,
`.cursor/mcp.json`, `claude_desktop_config.json`, ...), `.env*`, Jupyter notebooks **including cell
outputs**, docker-compose files, Terraform and GitHub workflows.

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

## Planned features (rest of the MVP)

- `--history` over the whole git history, `--staged` for pre-commit
- ML confidence score for every finding (the `--threshold` filter already exists)
- Baseline / allowlist file (`.tokenhound-baseline.json`)
- SARIF 2.1.0 output
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
