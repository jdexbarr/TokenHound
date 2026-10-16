# Security Policy

## Reporting a vulnerability

Please report vulnerabilities privately through
[GitHub Security Advisories](https://github.com/jdexbarr/tokenhound/security/advisories/new).
Do not open a public issue for security problems.

## Responsible disclosure of third-party secrets

If TokenHound's development (for example, collecting real-world negatives for the dataset) surfaces a
real secret in a public repository, the owner is notified privately (private issue or security
advisory) and the secret is never used or stored.

## Threat model

> Draft, completed in Phase F5. Items marked *(planned)* are not implemented yet.

**What TokenHound protects against**

- Committing credentials by accident (pre-commit hook on staged changes) *(planned)*
- Credentials already present in the working tree or anywhere in git history *(planned)*

**How TokenHound handles the secrets it finds**

- Full secret values are never printed, logged or written to disk. Reports contain masked values only.
- Fingerprints are `sha256(secret + file_path)`.
- Training data contains no real secrets: positives are synthetic; for real-world negatives only
  features, labels and a location pointer are stored, never the value.
- TokenHound never sends candidate secrets to any provider or network service.

**Known limitations**

- Detection is pattern- and entropy-based; secrets with unknown formats and low entropy can be missed.
- The ML classifier trades a small amount of recall for precision at the chosen threshold.
- Fingerprints are unsalted SHA-256. For low-entropy secrets (weak passwords caught by the generic
  detector), a fingerprint committed in a baseline file can be brute-forced. Rotate such secrets
  instead of baselining them.
- The bundled model is a joblib (pickle) file. Only load the model shipped with the package; never load
  model files from untrusted sources.
