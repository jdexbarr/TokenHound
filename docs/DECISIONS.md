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
CI; Juan merges.

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
