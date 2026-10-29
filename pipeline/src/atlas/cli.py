"""The `atlas` command line."""

from pathlib import Path
from typing import Annotated

import pyarrow.parquet as pq
import typer

from atlas.build import build_region
from atlas.catalogue.load import load_catalogue, validate_catalogue
from atlas.catalogue.schema import write_schemas
from atlas.paths import CATALOGUE_DIR, SCHEMAS_DIR
from atlas.paths import data_dir as default_data_dir
from atlas.publish.bundle import published_version
from atlas.qa.release import check, release
from atlas.qa.report import Report, describe

app = typer.Typer(help="Livability Atlas data pipeline.", no_args_is_help=True)

DataDir = Annotated[
    Path | None,
    typer.Option("--data-dir", help="Where raw and published data live (default: ATLAS_DATA_DIR)."),
]


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


@app.command()
def build(
    region: Annotated[str, typer.Argument(help="The region to build, such as london.")],
    data_dir_option: DataDir = None,
    commercial: Annotated[
        bool,
        typer.Option(
            "--commercial",
            help="Leave out indicators from datasets without a licence for commercial use (D07).",
        ),
    ] = False,
) -> None:
    """Build a region's data bundle from raw downloads, fetching what is missing.

    The bundle is checked and its QA report written beside it. It is published only if no check
    failed.
    """
    try:
        bundle = build_region(
            region, data_dir=data_dir_option, commercial=commercial, publish=False
        )
    except (KeyError, ValueError) as error:
        typer.echo(f"Cannot build {region}: {error}", err=True)
        raise typer.Exit(code=1) from error
    cells = len(pq.read_table(bundle / "cells.parquet"))
    typer.echo(f"Built {cells} cells into {bundle}")
    report = release(bundle, load_catalogue(CATALOGUE_DIR))
    _say(report, bundle, publishing=True)


@app.command()
def qa(
    region: Annotated[str, typer.Argument(help="The region whose bundle to check.")],
    version: Annotated[
        str | None,
        typer.Option("--version", help="The version to check (default: the published one)."),
    ] = None,
    publish: Annotated[
        bool,
        typer.Option("--publish", help="Publish the version if no check fails."),
    ] = False,
    data_dir_option: DataDir = None,
) -> None:
    """Check a built bundle and write its QA report beside it."""
    region_dir = (data_dir_option or default_data_dir()) / "published" / region
    if version is None:
        version = published_version(region_dir)
        if version is None:
            typer.echo(
                f"Cannot check {region}: no published bundle of {region} in {region_dir}", err=True
            )
            raise typer.Exit(code=1)
    bundle = region_dir / version
    if not (bundle / "manifest.json").exists():
        typer.echo(f"Cannot check {region}: no bundle {version} in {region_dir}", err=True)
        raise typer.Exit(code=1)
    catalogue = load_catalogue(CATALOGUE_DIR)
    report = release(bundle, catalogue) if publish else check(bundle, catalogue)
    _say(report, bundle, publishing=publish)


def _plural(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def _say(report: Report, bundle: Path, *, publishing: bool) -> None:
    """Tells the outcome of the QA report, and exits with an error if a check failed."""
    region, version = bundle.parent.name, bundle.name
    failed = report.count("fail")
    listed = [r for r in report.results if r.status in ("fail", "warn")]
    if report.failed:
        outcome = f"QA failed: {failed} of {len(report.results)} checks failed"
        outcome += f", so {region} {version} is not published." if publishing else "."
    else:
        outcome = (
            f"QA passed: {_plural(report.count('pass'), 'check', 'checks')}, "
            f"{_plural(report.count('warn'), 'warning', 'warnings')}, "
            f"{report.count('skipped')} skipped."
        )
    typer.echo(f"{outcome} Report: {bundle / 'qa.md'}", err=report.failed)
    for result in listed:
        typer.echo(f"- {describe(result)}", err=report.failed)
    if report.failed:
        if publishing:
            typer.echo(
                f"After a correction, `atlas qa {region} --version {version} --publish` checks it "
                "again and publishes it.",
                err=True,
            )
        raise typer.Exit(code=1)
    if publishing:
        typer.echo(f"Published {region} {version}.")
