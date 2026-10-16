"""Command-line entry point (spec sections 4 and 11).

Exit codes (A-08): 0 no findings, 1 findings at or above the threshold, 2 usage or runtime error.
"""

from __future__ import annotations

import logging
import shutil
import sys
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from tokenhound import __version__
from tokenhound.errors import TokenHoundError
from tokenhound.reporters import Reporter
from tokenhound.reporters.json_reporter import JsonReporter
from tokenhound.reporters.terminal import TerminalReporter
from tokenhound.scanner import default_detectors, scan
from tokenhound.sources.working_tree import WorkingTreeSource

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2

logger = logging.getLogger("tokenhound")

app = typer.Typer(
    name="tokenhound",
    help="Scan repositories for leaked secrets, with an ML false-positive filter.",
    no_args_is_help=True,
    add_completion=False,
)


class OutputFormat(StrEnum):
    TERMINAL = "terminal"
    JSON = "json"


@app.callback()
def main() -> None:
    """TokenHound command group."""


@app.command()
def version() -> None:
    """Print the installed TokenHound version."""
    typer.echo(f"tokenhound {__version__}")


@app.command("scan")
def scan_command(
    path: Annotated[
        Path, typer.Argument(help="Directory or file to scan.", exists=True, readable=True)
    ] = Path("."),
    output_format: Annotated[
        OutputFormat, typer.Option("--format", "-f", help="Output format.")
    ] = OutputFormat.TERMINAL,
    threshold: Annotated[
        float,
        typer.Option(
            min=0.0, max=1.0, help="Report findings whose confidence score is at least this."
        ),
    ] = 0.5,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Log skipped files and progress to stderr.")
    ] = False,
) -> None:
    """Scan the files under PATH (working tree) for secrets.

    Exits with 0 if nothing is found, 1 if there are findings and 2 on errors.
    """
    _configure_logging(verbose)
    try:
        result = scan(WorkingTreeSource(path), default_detectors(), threshold=threshold)
    except TokenHoundError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(EXIT_ERROR) from exc
    except Exception as exc:
        # The message of an unexpected exception could quote scanned text, so it is only shown
        # (with the traceback) in verbose mode.
        logger.debug("unexpected error", exc_info=True)
        typer.echo(f"error: unexpected {type(exc).__name__}; rerun with --verbose", err=True)
        raise typer.Exit(EXIT_ERROR) from exc

    reporter: Reporter
    if output_format is OutputFormat.JSON:
        reporter = JsonReporter()
    else:
        width = shutil.get_terminal_size((120, 24)).columns
        reporter = TerminalReporter(color=sys.stdout.isatty(), width=width)
    typer.echo(reporter.render(result), nl=False)
    raise typer.Exit(EXIT_FINDINGS if result.findings else EXIT_CLEAN)


def _configure_logging(verbose: bool) -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    logger.handlers[:] = [handler]
    logger.setLevel(logging.DEBUG if verbose else logging.WARNING)
    logger.propagate = False
