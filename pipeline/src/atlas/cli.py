"""The `atlas` command line."""

import typer

app = typer.Typer(help="Livability Atlas data pipeline.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Livability Atlas data pipeline."""
