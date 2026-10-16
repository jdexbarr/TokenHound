# Requirements and traceability matrix

Source: `KeyHound_Especificacion.pdf` v1.0 (2026-10-15). "p.N" is the PDF page. The spec calls the
project KeyHound; it was renamed TokenHound (D-001). Names such as `keyhound scan` and
`.keyhound-baseline.json` in the spec map to `tokenhound scan` and `.tokenhound-baseline.json`.

**Priority:** M = Mandatory, I = Important, O = Optional.
**Status:** NOT STARTED · IN PROGRESS · BLOCKED · IMPLEMENTED – PENDING VERIFICATION · VERIFIED · ACCEPTED.
Implementation strategy and components per milestone are in `docs/ARCHITECTURE.md` and
`docs/DEVELOPMENT_PLAN.md`; test cases in `docs/TEST_PLAN.md`.

## Functional requirements

### CLI and sources

| ID | Requirement | Src | Pri | Milestone | Acceptance criteria | Verification | Status |
|---|---|---|---|---|---|---|---|
| FR-001 | `tokenhound scan <dir>` scans the working tree | p.4–5 | M | H4 | Planted synthetic secrets in a temp dir are reported with correct file/line | Integration test | NOT STARTED |
| FR-002 | `scan --history` scans the full git history | p.4 | M | H5 | Secret added then removed in a past commit is reported with its commit SHA | Integration test on temp git repo | NOT STARTED |
| FR-003 | `scan --staged` scans only staged changes | p.4 | M | H5 | Only staged additions are reported; unstaged files ignored | Integration test | NOT STARTED |
| FR-004 | Sources `WorkingTreeSource`, `GitHistorySource`, `StagedSource` yield `Chunk(path, commit, line_no, text)` | p.5, p.10 | M | H4–H5 | Each source satisfies the `Source` protocol | Unit tests + mypy | NOT STARTED |
| FR-005 | CLI commands `scan`, `baseline`, `version` | p.10 | M | H1, H4, H6 | Each command exists with `--help` | CLI tests | IN PROGRESS (`version` done) |

### Detection

| ID | Requirement | Src | Pri | Milestone | Acceptance criteria | Verification | Status |
|---|---|---|---|---|---|---|---|
| FR-006 | Regex rules in YAML (one file per provider), extensible without code, validated with Pydantic on load | p.4, p.6, p.10 | M | H2 | Invalid rule file fails with a clear error; adding a YAML file adds a rule | Unit tests | NOT STARTED |
| FR-007 | Generic Shannon-entropy detector for key/secret/token/password assignments | p.3, p.7 | M | H2 | High-entropy assignment flagged; low-entropy and non-assignment ignored | Unit tests | NOT STARTED |
| FR-008 | Initial rule set: AWS, GitHub, Anthropic, OpenAI, Hugging Face, Stripe, Slack, Google, PEM private key, JWT, generic entropy (+ Replicate, A-04) with spec severities | p.4, p.6–7 | M | H3 | Each rule matches its valid synthetic examples and rejects its invalid ones | Per-rule tests | NOT STARTED |
| FR-009 | Each pattern validated against official provider docs; source cited in its YAML | p.6, p.11 | M | H3 | Every YAML has a `references` entry to official docs | Schema test | NOT STARTED |
| FR-010 | JWT severity Medium, High when payload indicates privileged role | p.7 | M | H3 | `service_role` JWT reported as High | Unit test | NOT STARTED |
| FR-011 | Priority files: MCP/agent configs, `.env*`, `*.ipynb` incl. cell outputs, docker-compose, `*.tf`, `*.tfvars`, GitHub workflows | p.7 | M | H4 | Secret inside a notebook cell output is found and reported with the notebook path | Integration tests | NOT STARTED |
| FR-012 | `.env.example` scanned with a different threshold | p.7 | M | H8 | Threshold for `.env.example` differs and is applied | Unit test | NOT STARTED |
| FR-013 | Detectors emit `Candidate(rule_id, match, span, chunk)` | p.5 | M | H2 | Type-checked dataclass | mypy + unit tests | NOT STARTED |

### Context, classification, post-processing

| ID | Requirement | Src | Pri | Milestone | Acceptance criteria | Verification | Status |
|---|---|---|---|---|---|---|---|
| FR-014 | Context feature extraction (string shape, code, file, rule groups) | p.5, p.8 | M | H8 | Same function used by training and runtime; features deterministic | Unit tests | NOT STARTED |
| FR-015 | Serialized scikit-learn model assigns `score ∈ [0,1]` | p.4–5, p.10 | M | H8 | Bundled model loads and scores every finding | Unit + integration tests | NOT STARTED |
| FR-016 | Findings below a configurable threshold are dropped | p.4–5 | M | H8 | `--threshold` changes output | CLI test | NOT STARTED |
| FR-017 | Dedup by `fingerprint = sha256(secret + file_path)` | p.5 | M | H2, H5 | Same secret/path across commits reported once | Unit + integration tests | NOT STARTED |
| FR-018 | Baseline/allowlist `.tokenhound-baseline.json` | p.4, p.9 | M | H6 | Baselined finding suppressed; new one still reported | Integration test | NOT STARTED |
| FR-019 | Severity derived from rule metadata | p.5 | M | H2 | Finding severity equals rule severity (except JWT elevation) | Unit test | NOT STARTED |
| FR-020 | Short provider-specific remediation in each finding | p.4–5, p.9 | M | H3, H9 | Every rule has non-empty remediation | Schema test | NOT STARTED |
| FR-021 | Frozen `Finding` dataclass with spec fields + `Chunk`, `Candidate`, `Severity` | p.5, p.10 | M | H2 | Fields match spec; no raw secret field on `Finding` | mypy + unit test | NOT STARTED |

### Outputs and integrations

| ID | Requirement | Src | Pri | Milestone | Acceptance criteria | Verification | Status |
|---|---|---|---|---|---|---|---|
| FR-022 | Rich terminal output | p.4, p.6 | M | H4 | Table with severity, rule, location, masked value, score | Snapshot test | NOT STARTED |
| FR-023 | JSON output | p.4 | M | H4 | Valid JSON matching documented shape | Unit test | NOT STARTED |
| FR-024 | SARIF 2.1.0 output, visible in GitHub Security tab | p.3–4, p.13 | M | H9 | Validates against the official schema; shows in code scanning of example repo | Schema test + manual check | NOT STARTED |
| FR-025 | Secrets always masked in every output | p.4–5, p.8 | M | H2–H9 | No synthetic secret appears in stdout, JSON, SARIF or baseline | Cross-cutting security test | NOT STARTED |
| FR-026 | pre-commit hook (`.pre-commit-hooks.yaml`) | p.4, p.10 | M | H6 | Hook blocks commit with a synthetic secret in a sample repo | Integration test + manual | NOT STARTED |
| FR-027 | GitHub Action (`action.yml`) with SARIF upload | p.3–4, p.10 | M | H9 | Action runs in example repo and uploads SARIF | Manual + workflow run | NOT STARTED |
| FR-028 | Docker image | p.6, p.9–10 | M | H9 | `docker run ... tokenhound version` works | CI build | NOT STARTED |
| FR-039 | Exit codes: 0 no findings, 1 findings, 2 error (A-08) | assumption | M | H4 | Codes match in each case | CLI tests | NOT STARTED |

### ML pipeline (`ml/`)

| ID | Requirement | Src | Pri | Milestone | Acceptance criteria | Verification | Status |
|---|---|---|---|---|---|---|---|
| FR-029 | Synthetic positives with exact provider format in realistic contexts | p.7, p.10 | M | H7 | Generator output matches each rule; reproducible with seed | Unit tests | NOT STARTED |
| FR-030 | Hard negatives (placeholders, docs/test values, hashes, UUIDs, base64 assets, lockfiles) | p.7 | M | H7 | Each category present in dataset | Dataset report | NOT STARTED |
| FR-031 | Real negatives from popular OSS repos: only features + label + location pointer stored (A-05) | p.7–8 | M | H7 | Dataset files contain no candidate values | Automated check | NOT STARTED |
| FR-032 | Auto-labeling of synthetic; terminal script for manual review of a real sample | p.7 | M | H7 | Script labels and saves without showing full values | Manual run | NOT STARTED |
| FR-033 | Train/test split by repository | p.7 | M | H7 | No repo appears in both splits | Unit test | NOT STARTED |
| FR-034 | Models: Baseline 0 (rules only), Logistic Regression, Random Forest; LightGBM optional | p.8 | M (LGBM: O) | H8 | All trained and compared in notebook | Notebook | NOT STARTED |
| FR-035 | Metrics: precision, recall, F1, PR-AUC; primary: precision at recall ≥ 0.95 | p.8 | M | H8 | Reported for each model on the test split | Notebook | NOT STARTED |
| FR-036 | Interpretability: feature importances (SHAP if gradient boosting) explained in README | p.8 | M (SHAP: O) | H8, H10 | README section with importances | Review | NOT STARTED |
| FR-037 | Evaluation notebook `ml/notebooks/evaluation.ipynb` | p.9–10 | M | H8 | Runs top to bottom | CI or manual run | NOT STARTED |
| FR-038 | External benchmark: Gitleaks on the same labeled set, comparison table | p.8–9 | M | H10 | Table in `benchmarks/` and README | Reproducible script | NOT STARTED |

## Non-functional requirements

| ID | Requirement | Src | Pri | Milestone | Acceptance / target | Verification | Status |
|---|---|---|---|---|---|---|---|
| NFR-001 | Never print or store full secrets; fingerprint SHA-256 | p.4, p.8 | M | all | Cross-cutting test passes | Security test | NOT STARTED |
| NFR-002 | Datasets without real secrets | p.8 | M | H7 | Automated check over dataset files | Script | NOT STARTED |
| NFR-003 | Recall ≥ 0.95 on labeled test set | p.10 | M (target) | H8 | Reported honestly | Notebook | NOT STARTED |
| NFR-004 | ≥ 50% fewer false positives vs. rules-only at same recall | p.10 | M (target) | H8, H10 | Reported honestly | Notebook + benchmark | NOT STARTED |
| NFR-005 | ≥ 10 secret types + generic detector | p.10 | M (target) | H3 | 11 types (A-04) | Rule count test | NOT STARTED |
| NFR-006 | ~10k-commit repo scanned in < 2 min, measured and documented | p.10–11 | M (target) | H5, H10 | Benchmark script + README number | Benchmark | NOT STARTED |
| NFR-007 | Coverage ≥ 80% in sources, detectors, reporters | p.11 | M (target) | H2–H9 | pytest-cov report | CI | NOT STARTED |
| NFR-008 | Installable with pip; Action and hook working in an example repo | p.11 | M | H9–H10 | Fresh install works; example repo green | Manual + CI | NOT STARTED |
| NFR-009 | Report real numbers in README even if targets are missed | p.11 | M | H10 | README metrics table | Review | NOT STARTED |
| NFR-010 | Five independent, separately testable, replaceable stages | p.5 | M | H2–H8 | Protocol per stage; tests per stage | Code review + tests | NOT STARTED |
| NFR-011 | Every change has pytest tests and passes ruff and mypy | p.6, p.12 | M | all | CI green on every PR | CI | VERIFIED |
| NFR-012 | Rules versioned, tested per rule, official source cited | p.11 | M | H3 | Schema + per-rule tests | Tests | NOT STARTED |
| NFR-013 | No validity checks against provider APIs in MVP | p.5, p.8 | M | all | No network calls in scanner | Code review | NOT STARTED |
| NFR-014 | Responsible disclosure of real secrets found during development | p.8 | M | H7 | Process in SECURITY.md | Review | IMPLEMENTED – PENDING VERIFICATION |
| NFR-015 | Threat model documented in SECURITY.md | p.8, p.10 | M | H1, H10 | Final version reviewed | Review | IN PROGRESS (draft) |
| NFR-016 | Total cost $0 | p.11 | M | all | No paid services | Review | NOT STARTED |
| NFR-017 | Repo content in English; communication with Juan in Spanish | p.12 | M | all | — | Review | IN PROGRESS |
| NFR-018 | No phase advance without green tests and updated README; tag per phase | p.9 | M | all | Tags `f0`…`f5` exist | git tags | NOT STARTED |
| NFR-019 | Out-of-scope ideas go to IDEAS.md | p.11 | I | all | File exists and is used | Review | IMPLEMENTED – PENDING VERIFICATION |
| NFR-020 | Open source, MIT license | p.3, p.9 | M | H1 | LICENSE present | Review | IMPLEMENTED – PENDING VERIFICATION |

## Technical constraints

| ID | Constraint | Src | Status |
|---|---|---|---|
| TECH-001 | Python 3.11+ | p.6 | VERIFIED (CI matrix 3.11–3.13) |
| TECH-002 | uv + pyproject.toml | p.6 | VERIFIED |
| TECH-003 | Typer | p.6 | VERIFIED |
| TECH-004 | Rich | p.6 | NOT STARTED (H4) |
| TECH-005 | GitPython; pygit2 only as later optimisation | p.6, p.11 | NOT STARTED (H5) |
| TECH-006 | PyYAML + Pydantic | p.6 | NOT STARTED (H2) |
| TECH-007 | scikit-learn, pandas, joblib; LightGBM optional | p.6 | NOT STARTED (H7–H8) |
| TECH-008 | pytest, ruff, mypy, pre-commit | p.6 | VERIFIED |
| TECH-009 | GitHub Actions, PyPI trusted publishing, Docker | p.6 | IN PROGRESS (CI done; publishing H10, Docker H9) |
| TECH-010 | SARIF 2.1.0 | p.4, p.13 | NOT STARTED (H9) |
| TECH-011 | Repository structure of spec §11 (+ `scanner.py`, `baseline.py`, A-14) | p.10 | IN PROGRESS |
| TECH-012 | Model at `src/tokenhound/classifier/tokenhound_model.joblib` | p.10 | NOT STARTED (H8) |

## User interface (CLI)

| ID | Requirement | Src | Milestone | Status |
|---|---|---|---|---|
| UI-001 | Commands `scan`, `baseline`, `version` with auto-generated help | p.6, p.10 | H1–H6 | IN PROGRESS |
| UI-002 | Flags `--history`, `--staged`, threshold, output format | p.4 | H4–H8 | NOT STARTED |
| UI-003 | Rich table with severity colors | p.6 | H4 | NOT STARTED |
| UI-004 | Masked values like `sk-a****xYz9` | p.5 | H2 | NOT STARTED |
| UI-005 | Findings in GitHub Security tab via SARIF | p.3 | H9 | NOT STARTED |

## Deliverables

| ID | Deliverable | Src | Milestone | Status |
|---|---|---|---|---|
| DEL-001 | Public repo, spec §11 structure, MIT | p.9–10 | H1 | VERIFIED |
| DEL-002 | GitHub Actions CI | p.9 | H1 | VERIFIED |
| DEL-003 | YAML rules + entropy + `scan .` with Rich/JSON, tests per rule | p.9 | H2–H4 | NOT STARTED |
| DEL-004 | `--history`, `--staged`, dedup, baseline | p.9 | H5–H6 | NOT STARTED |
| DEL-005 | pre-commit hook | p.9–10 | H6 | NOT STARTED |
| DEL-006 | Synthetic generator, `build_dataset.py`, `train.py`, feature extractor | p.9–10 | H7–H8 | NOT STARTED |
| DEL-007 | Evaluation notebook | p.9–10 | H8 | NOT STARTED |
| DEL-008 | Trained model integrated | p.9 | H8 | NOT STARTED |
| DEL-009 | SARIF output | p.9 | H9 | NOT STARTED |
| DEL-010 | GitHub Action on Marketplace | p.3, p.9 | H9–H10 | NOT STARTED |
| DEL-011 | Remediation guide per secret type | p.9 | H9 | NOT STARTED |
| DEL-012 | Docker image | p.9 | H9 | NOT STARTED |
| DEL-013 | Benchmark vs. Gitleaks | p.9–10 | H10 | NOT STARTED |
| DEL-014 | Case-study README with real metrics | p.8–9 | H10 | NOT STARTED |
| DEL-015 | PyPI package | p.3, p.9 | H10 | NOT STARTED |
| DEL-016 | SECURITY.md (threat model + disclosure) | p.8, p.10 | H1, H10 | IN PROGRESS |
| DEL-017 | Example repo with Action and hook working | p.11 | H9–H10 | NOT STARTED |
| DEL-018 | Tag per phase | p.9 | all | NOT STARTED |
| DEL-019 | IDEAS.md | p.11 | H1 | IMPLEMENTED – PENDING VERIFICATION |
| DEL-020 | LinkedIn/blog post and resume entry (written by Juan) | p.9, p.13 | H10 | NOT STARTED |
