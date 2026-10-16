"""Command-line entry point.

Only ``version`` exists in F0; ``scan`` and ``baseline`` arrive in F1/F2 (spec section 11).
"""

import typer

from tokenhound import __version__

app = typer.Typer(
    name="tokenhound",
    help="Scan repositories for leaked secrets, with an ML false-positive filter.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def main() -> None:
    """TokenHound command group."""


@app.command()
def version() -> None:
    """Print the installed TokenHound version."""
    typer.echo(f"tokenhound {__version__}")
