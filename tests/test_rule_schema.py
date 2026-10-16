from pathlib import Path
from typing import Any

import pytest
import yaml

from tokenhound.detectors.rule_schema import (
    Rule,
    RuleLoadError,
    builtin_rules_dir,
    load_rule_file,
    load_rules,
)
from tokenhound.models import Severity

VALID_RULE: dict[str, Any] = {
    "id": "test-token",
    "description": "Synthetic test token",
    "regex": r"\b(tst_[A-Za-z0-9]{20})\b",
    "secret_group": 1,
    "keywords": ["tst_"],
    "severity": "high",
    "remediation": "Rotate the test token.",
    "references": ["https://example.com/docs/tokens"],
}


def write_rules(
    directory: Path, name: str, rules: list[dict[str, Any]], provider: str = "Test"
) -> Path:
    path = directory / name
    path.write_text(yaml.safe_dump({"provider": provider, "rules": rules}), encoding="utf-8")
    return path


def test_load_valid_rule_file(tmp_path: Path) -> None:
    path = write_rules(tmp_path, "test.yaml", [VALID_RULE])

    [rule] = load_rule_file(path)

    assert rule.id == "test-token"
    assert rule.provider == "Test"
    assert rule.severity is Severity.HIGH
    assert rule.keywords == ("tst_",)
    assert rule.pattern.search("x = tst_ABCDEFGHIJKLMNOPQRST") is not None


def test_load_rules_reads_yaml_and_yml_in_name_order(tmp_path: Path) -> None:
    write_rules(tmp_path, "b.yml", [{**VALID_RULE, "id": "rule-b"}])
    write_rules(tmp_path, "a.yaml", [{**VALID_RULE, "id": "rule-a"}])
    (tmp_path / "notes.txt").write_text("ignored", encoding="utf-8")

    rules = load_rules([tmp_path])

    assert [r.id for r in rules] == ["rule-a", "rule-b"]


def test_named_secret_group_is_accepted(tmp_path: Path) -> None:
    rule = {**VALID_RULE, "regex": r"(?P<secret>tst_[A-Za-z0-9]{20})", "secret_group": "secret"}
    path = write_rules(tmp_path, "test.yaml", [rule])

    assert load_rule_file(path)[0].secret_group == "secret"


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"regex": "(unclosed"}, "invalid regex"),
        ({"secret_group": 2}, "out of range"),
        ({"secret_group": "missing"}, "not a named group"),
        ({"id": "Not Kebab"}, "id"),
        ({"severity": "catastrophic"}, "severity"),
        ({"references": []}, "references"),
        ({"references": ["not a url"]}, "references"),
        ({"remediation": ""}, "remediation"),
        ({"unexpected": True}, "unexpected"),
    ],
)
def test_invalid_rules_fail_with_file_name(
    tmp_path: Path, override: dict[str, Any], message: str
) -> None:
    path = write_rules(tmp_path, "broken.yaml", [{**VALID_RULE, **override}])

    with pytest.raises(RuleLoadError, match=message) as excinfo:
        load_rule_file(path)

    assert "broken.yaml" in str(excinfo.value)


def test_missing_required_field_fails(tmp_path: Path) -> None:
    rule = {k: v for k, v in VALID_RULE.items() if k != "severity"}
    path = write_rules(tmp_path, "test.yaml", [rule])

    with pytest.raises(RuleLoadError, match="severity"):
        load_rule_file(path)


def test_file_without_rules_fails(tmp_path: Path) -> None:
    path = write_rules(tmp_path, "empty.yaml", [])

    with pytest.raises(RuleLoadError, match="rules"):
        load_rule_file(path)


def test_malformed_yaml_fails(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("provider: [unclosed", encoding="utf-8")

    with pytest.raises(RuleLoadError, match=r"bad\.yaml"):
        load_rule_file(path)


def test_duplicate_rule_ids_across_files_fail(tmp_path: Path) -> None:
    write_rules(tmp_path, "a.yaml", [VALID_RULE])
    write_rules(tmp_path, "b.yaml", [VALID_RULE])

    with pytest.raises(RuleLoadError, match="duplicate rule id 'test-token'"):
        load_rules([tmp_path])


def test_missing_directory_fails(tmp_path: Path) -> None:
    with pytest.raises(RuleLoadError, match="not a directory"):
        load_rules([tmp_path / "nope"])


def test_builtin_rules_directory_ships_with_package() -> None:
    directory = builtin_rules_dir()

    assert directory.is_dir()
    assert all(isinstance(rule, Rule) for rule in load_rules())
