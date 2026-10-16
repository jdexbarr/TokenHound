import pytest

from tokenhound.sources.priority import FileKind, classify


@pytest.mark.parametrize(
    ("path", "kind"),
    [
        ("mcp.json", FileKind.MCP_CONFIG),
        (".mcp.json", FileKind.MCP_CONFIG),
        (".cursor/mcp.json", FileKind.MCP_CONFIG),
        (".vscode/mcp.json", FileKind.MCP_CONFIG),
        ("Library/Claude/claude_desktop_config.json", FileKind.MCP_CONFIG),
        (".env", FileKind.ENV),
        ("app/.env.production", FileKind.ENV),
        (".env.local", FileKind.ENV),
        (".env.example", FileKind.ENV_EXAMPLE),
        ("notebooks/Explore.IPYNB", FileKind.NOTEBOOK),
        ("docker-compose.yml", FileKind.INFRA),
        ("deploy/docker-compose.prod.yaml", FileKind.INFRA),
        ("infra/main.tf", FileKind.INFRA),
        ("prod.tfvars", FileKind.INFRA),
        (".github/workflows/ci.yml", FileKind.INFRA),
        ("src/app.py", FileKind.OTHER),
        ("config.json", FileKind.OTHER),
        ("environment.yml", FileKind.OTHER),
        ("workflows/ci.yml", FileKind.OTHER),
        (".github/ci.yml", FileKind.OTHER),
        ("docs/.envrc", FileKind.OTHER),
    ],
)
def test_classify(path: str, kind: FileKind) -> None:
    assert classify(path) is kind


def test_only_other_is_not_priority() -> None:
    assert [k for k in FileKind if not k.is_priority] == [FileKind.OTHER]
