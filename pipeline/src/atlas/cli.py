"""The `atlas` command line."""

from pathlib import Path
from typing import Annotated

import typer

from atlas.catalogue.load import validate_catalogue
from atlas.paths import CATALOGUE_DIR

app = typer.Typer(help="Livability Atlas data pipeline.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Livability Atlas data pipeline."""


@app.command()
def validate(
    catalogue_dir: Annotated[
        Path, typer.Option(help="The folder holding factors.yaml and datasets.yaml.")
    ] = CATALOGUE_DIR,
) -> None:
    """Check the factor catalogue against its rules."""
    problems = validate_catalogue(catalogue_dir)
    if not problems:
        typer.echo("The catalogue passes.")
        return
    for problem in problems:
        typer.echo(problem, err=True)
    typer.echo(f"{len(problems)} problems in {catalogue_dir}.", err=True)
    raise typer.Exit(code=1)
