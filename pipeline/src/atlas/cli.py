"""The `atlas` command line."""

from pathlib import Path
from typing import Annotated

import typer

from atlas.catalogue.load import validate_catalogue
from atlas.catalogue.schema import write_schemas
from atlas.paths import CATALOGUE_DIR, SCHEMAS_DIR

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
    noun = "problem" if len(problems) == 1 else "problems"
    typer.echo(f"{len(problems)} {noun} in {catalogue_dir}.", err=True)
    raise typer.Exit(code=1)


@app.command()
def schemas(
    output_dir: Annotated[
        Path, typer.Option(help="Where to write the JSON Schema files.")
    ] = SCHEMAS_DIR,
) -> None:
    """Export the catalogue models to JSON Schema, for the web app's types."""
    for path in write_schemas(output_dir):
        typer.echo(f"wrote {path}")
