"""File kinds that deserve priority in an AI-era codebase (spec section 7, "Archivos priorizados").

MCP and agent configs, ``.env`` files, notebooks and infrastructure files are where secrets leak
most often. The working-tree source scans them first and allows them a larger size limit, and the
notebook reader also scans cell outputs. Later milestones use the kind as a classifier feature and
to pick a separate threshold for ``.env.example`` (spec section 7, A-07).
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath

MCP_CONFIG_NAMES = frozenset({"mcp.json", ".mcp.json", "claude_desktop_config.json"})
INFRA_SUFFIXES = frozenset({".tf", ".tfvars"})
YAML_SUFFIXES = frozenset({".yml", ".yaml"})


class FileKind(StrEnum):
    MCP_CONFIG = "mcp-config"
    ENV = "env"
    ENV_EXAMPLE = "env-example"
    NOTEBOOK = "notebook"
    INFRA = "infra"
    OTHER = "other"

    @property
    def is_priority(self) -> bool:
        return self is not FileKind.OTHER


def classify(path: str) -> FileKind:
    """Classify a path (relative, ``/``-separated) by name; the content is not read."""
    pure = PurePosixPath(path)
    name = pure.name
    lower = name.lower()
    if lower in MCP_CONFIG_NAMES:
        return FileKind.MCP_CONFIG
    if lower == ".env.example":
        return FileKind.ENV_EXAMPLE
    if lower == ".env" or lower.startswith(".env."):
        return FileKind.ENV
    if pure.suffix.lower() == ".ipynb":
        return FileKind.NOTEBOOK
    if pure.suffix.lower() in INFRA_SUFFIXES:
        return FileKind.INFRA
    if pure.suffix.lower() in YAML_SUFFIXES and (
        lower.startswith("docker-compose") or _in_workflows_dir(pure)
    ):
        return FileKind.INFRA
    return FileKind.OTHER


def _in_workflows_dir(path: PurePosixPath) -> bool:
    parts = path.parts[:-1]
    return len(parts) >= 2 and parts[-2:] == (".github", "workflows")
