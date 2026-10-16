# Decision log

Each entry: context, decision, reason. "A-xx" are the assumptions from the initial spec analysis,
approved by Juan on 2026-10-16.

## D-001 · Project name: TokenHound (2026-10-16)

The spec name "KeyHound" is provisional (p.1). `keyhound` is already taken on PyPI by an unrelated
secret scanner, and "KeyScout" clashes with a commercial forensic tool. **TokenHound** was free on
PyPI, npm, crates.io and Docker Hub. Package, command and import are `tokenhound`; the baseline file is
`.tokenhound-baseline.json`.

## D-002 · Code hosted on GitHub, work through pull requests (2026-10-16)

Repo `jdexbarr/tokenhound` (public, so Actions and code scanning are free). Changes go through PRs with
CI; Claude squash-merges once CI is green (see D-006).

## D-003 · Repository docs in English (2026-10-16)

Spec p.12: code, comments, commits and repo docs in English; conversation in Spanish.

## D-004 · Build backend hatchling, dev tools in a uv dependency group (2026-10-16)

Hatchling is a mature, standard PEP 517 backend that uv supports natively. Dev tools live in
`[dependency-groups].dev` so they are never installed by end users. Added dev-only tools beyond the
spec: `pytest-cov` (to measure NFR-007); `jsonschema` will be added in H9 to validate SARIF.

## D-005 · Approved assumptions from the analysis (2026-10-16)

- **A-03** OpenAI rule excludes `sk-ant-` (no double match with Anthropic); current key formats verified against official docs in H3.
- **A-04** "≥ 10 providers" counts secret types (10 in the spec table) plus Replicate (named on p.4) = 11 + generic.
- **A-05** Real negatives store a pointer (repo URL, commit, path, line, fingerprint) + features + label, never the value, so the Gitleaks benchmark can re-materialise them.
- **A-06** Pass-through classifier (score 1.0) until H8; afterwards `--no-ml` reproduces Baseline 0.
- **A-07** Default threshold and `.env.example` threshold chosen in H8 from the PR curve (operating point with recall ≥ 0.95); configured with `--threshold`. No config file in the MVP.
- **A-08** Exit codes 0 / 1 / 2 (no findings / findings / error).
- **A-09** Working-tree scan skips `.git/`, binaries and files > 1 MB; it does not honour `.gitignore`.
- **A-10** `docs/` and `CLAUDE.md` in English (see D-003).
- **A-11** Docker image published to GitHub Container Registry.
- **A-12** GitHub Action is a composite action installing the pinned PyPI version.
- **A-13** `--history` scans only added lines from a single streamed `git log -p` (via GitPython) with a cache of seen blobs.
- **A-14** Additions to the spec layout: `src/tokenhound/scanner.py` (orchestrator) and `src/tokenhound/baseline.py`.

## D-006 · Detection core details (2026-10-16, H2)

- `Candidate` carries `severity` and `remediation` in addition to the spec's four fields, so
  detectors can set them (JWT privilege elevation) without the orchestrator looking rules up again.
- Fingerprint is `sha256(secret + "\0" + file_path)`: the NUL separator prevents collisions
  between different splits of the same characters; otherwise identical to spec §5.
- Masking keeps the secret's length and reveals at most 4 characters per end (spec example), fewer
  for short values, none below 10 characters.
- Entropy detector defaults: min length 16, min entropy 3.5 bits/char, base severity medium. They
  are deliberately permissive because the classifier filters later; tuned in H8.
- Phase tags are created by Juan: the cloud environment's proxy rejects tag pushes.
- PR workflow: Claude merges its own PRs (squash) once CI is green, at Juan's request.

## D-007 · Initial rule set (2026-10-16, H3)

- 13 rules for 11 providers. Splits beyond the spec table: Anthropic Admin keys (`sk-ant-admin01-`,
  critical) separate from API keys (high); GitHub fine-grained PATs separate from classic tokens.
- Slack also covers `xapp-`, `xwfp-` and rotating `xoxe.` tokens, listed in Slack's token docs.
- Stripe only flags live keys (`sk_live_`, `rk_live_`) as in the spec; test keys are not secrets of
  consequence and publishable keys are public by design.
- Private keys: the whole PEM block is the secret when its END line is in the same chunk, so
  different keys get different fingerprints; otherwise the header alone is reported.
- OpenAI publishes no key format; the rule uses the issued prefixes and excludes `sk-ant-` (A-03).
- JWT severity is raised by a per-rule severity adjuster (`SEVERITY_ADJUSTERS` in the regex
  engine) that decodes the payload without verifying it; roles `service_role`, `admin`,
  `administrator`, `superuser`, `root`, `owner` or `is_admin: true` count as privileged.
- Rule examples live in `tests/test_rules.py` as generators, not in YAML, so no realistic key is
  ever committed (resolves the open point in `docs/ARCHITECTURE.md`).

## D-008 · Working-tree scan and output (2026-10-16, H4)

- Priority files (spec §7) are scanned first and may be up to 20 MiB instead of 1 MiB: notebooks
  with outputs easily exceed 1 MiB, and A-09's limit would otherwise skip exactly the files the spec
  prioritises.
- Notebooks are parsed so detectors see decoded cell text (not JSON-escaped strings) and cell
  outputs are scanned; images are ignored. Invalid notebooks are scanned as plain text.
- Symbolic links are skipped, so a scan never reads outside the scanned tree.
- When a provider rule and the entropy detector match overlapping text, only the provider finding
  is kept.
- The entropy detector no longer accepts bare (unquoted) values that contain brackets or are
  followed by code punctuation (`self._keys[rule.id]`, `match.group(...)`). On a self-scan this cut
  candidates from 464 to 73 without losing any test case.
- `--threshold` exists now (default 0.5, A-07 sets the final value in H8); with pass-through scores
  it filters nothing yet.
- JSON output carries `schema_version: 1` so its shape can evolve without breaking consumers.
- Unexpected exceptions exit with code 2 and print only their type unless `--verbose`, because an
  exception message could quote scanned text.
