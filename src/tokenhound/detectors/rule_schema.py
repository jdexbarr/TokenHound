"""Declarative detection rules: Pydantic schema and YAML loader (spec sections 4, 6, 7).

Each YAML file holds the rules for one provider::

    provider: Example
    rules:
      - id: example-api-key
        description: Example API key
        regex: '\\b(exk_[A-Za-z0-9]{32})\\b'
        secret_group: 1
        keywords: [exk_]
        severity: high
        remediation: Revoke the key in the Example dashboard and issue a new one.
        references: [https://docs.example.com/api-keys]

Rules are validated when loaded, so a broken rule file fails fast with the file name in the error.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from importlib.resources import files
from pathlib import Path
from typing import Annotated, Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError, model_validator

from tokenhound.errors import TokenHoundError
from tokenhound.models import Severity

RuleId = Annotated[str, Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=64)]


class RuleLoadError(TokenHoundError):
    """A rule file could not be read or does not satisfy the schema."""


class Rule(BaseModel):
    """One regex detector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: RuleId
    provider: str = Field(min_length=1)
    description: str = Field(min_length=1)
    regex: str = Field(min_length=1)
    secret_group: int | str = 0
    keywords: tuple[str, ...] = ()
    severity: Severity
    remediation: str = Field(min_length=1)
    references: tuple[HttpUrl, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_regex(self) -> Rule:
        try:
            pattern = re.compile(self.regex)
        except re.error as exc:
            raise ValueError(f"invalid regex: {exc}") from exc
        group = self.secret_group
        if isinstance(group, int) and not 0 <= group <= pattern.groups:
            raise ValueError(f"secret_group {group} out of range (pattern has {pattern.groups})")
        if isinstance(group, str) and group not in pattern.groupindex:
            raise ValueError(f"secret_group {group!r} is not a named group in the regex")
        return self

    @property
    def pattern(self) -> re.Pattern[str]:
        """Compiled regex (``re`` caches compiled patterns, so this is cheap)."""
        return re.compile(self.regex)


class RuleFile(BaseModel):
    """Top-level structure of a provider YAML file."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1)
    rules: list[dict[str, Any]] = Field(min_length=1)


def builtin_rules_dir() -> Path:
    """Directory holding the rules bundled with the package."""
    return Path(str(files("tokenhound.detectors").joinpath("rules")))


def load_rule_file(path: Path) -> list[Rule]:
    """Load and validate every rule in one YAML file."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        rule_file = RuleFile.model_validate(raw)
        return [Rule.model_validate({"provider": rule_file.provider, **r}) for r in rule_file.rules]
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise RuleLoadError(f"{path}: {exc}") from exc


def load_rules(directories: Iterable[Path] | None = None) -> list[Rule]:
    """Load all ``*.yaml`` / ``*.yml`` rule files from ``directories`` (default: built-in rules).

    Files are read in name order so the result is deterministic. Duplicate rule ids are an error.
    """
    dirs = list(directories) if directories is not None else [builtin_rules_dir()]
    rules: list[Rule] = []
    seen: dict[str, Path] = {}
    for directory in dirs:
        if not directory.is_dir():
            raise RuleLoadError(f"{directory}: not a directory")
        paths = sorted(p for p in directory.iterdir() if p.suffix in {".yaml", ".yml"})
        for path in paths:
            for rule in load_rule_file(path):
                if rule.id in seen:
                    raise RuleLoadError(
                        f"{path}: duplicate rule id {rule.id!r} (first defined in {seen[rule.id]})"
                    )
                seen[rule.id] = path
                rules.append(rule)
    return rules
