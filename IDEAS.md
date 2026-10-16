# Ideas (out of MVP scope)

Ideas that are **not** part of the MVP (spec §4 and §14). Nothing here gets implemented without an
explicit decision recorded in `docs/DECISIONS.md`.

- Active validity checks of keys against provider APIs (opt-in, only on repos you own; spec §9)
- Scanning Slack, Jira, Confluence and other collaboration tools
- Web dashboard (Next.js + Supabase)
- Scanning Docker images and binary artifacts
- Automatic remediation (history rewrite with git-filter-repo)
- pygit2 backend for faster history scans (spec §6, only if GitPython misses the speed target)
- `--exclude` globs and/or skipping dependency folders (`.venv/`, `node_modules/`) in working-tree
  scans. A self-scan found most candidates in `.venv/` (H4). Needs a decision because A-09 says to
  scan everything outside `.git/`.
