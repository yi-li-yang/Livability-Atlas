"""A small bundle for the QA report's tests: real indicators of the catalogue on the seven cells
around Soho, with values that pass every check until a test spoils one."""

import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import h3
import pyarrow as pa
import pyarrow.parquet as pq

from atlas.catalogue.load import load_catalogue
from atlas.paths import CATALOGUE_DIR
from atlas.publish.bundle import Choice, Neighbourhoods, write_bundle

SOHO = h3.latlng_to_cell(51.5136, -0.1337, 9)
CELLS = sorted(h3.grid_disk(SOHO, 1))
PLACES = {"Soho": (51.5136, -0.1337)}


def sample_columns() -> dict[str, Sequence[Any]]:
    return {
        "service-level": ["6b", "6a", "5", "4", "3", "2", "1b"],
        "station-proximity": [2.0, 3.5, 5.0, 8.0, 12.0, 15.0, 30.0],
        "diversity": [0.7, 0.72, 0.65, 0.6, 0.5, 0.4, 0.3],
        "gigabit-broadband": [99.0, 98.0, 97.0, 95.0, 90.0, 80.0, 60.0],
    }


def sample_choices() -> dict[str, list[Choice]]:
    return {
        "faith": [
            Choice("hindu", "Hindu", None, [20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0]),
            Choice("sikh", "Sikh", None, [10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0]),
        ]
    }


def sample_neighbourhoods() -> Neighbourhoods:
    return Neighbourhoods(
        listing=[("Soho", "Westminster"), ("Fitzrovia", "Camden")],
        of_cell=[0, 0, 0, 0, 1, 1, None],
        datasets=["hoc-msoa-names", "ons-msoa-boundaries"],
    )


def spoil(
    folder: Path,
    *,
    table: Callable[[pa.Table], pa.Table] | None = None,
    manifest: Callable[[dict[str, Any]], None] | None = None,
) -> Path:
    """Rewrites a bundle's files after a change, so a check can be run against a fault."""
    if table is not None:
        pq.write_table(table(pq.read_table(folder / "cells.parquet")), folder / "cells.parquet")
    if manifest is not None:
        document = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        manifest(document)
        (folder / "manifest.json").write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return folder


def write_sample(
    out_dir: Path,
    *,
    columns: dict[str, Sequence[Any]] | None = None,
    choices: dict[str, list[Choice]] | None = None,
    neighbourhoods: Neighbourhoods | None = None,
    publish: bool = True,
) -> Path:
    """Writes the sample bundle with some columns replaced or added, and returns its folder."""
    return write_bundle(
        load_catalogue(CATALOGUE_DIR),
        region_id="london",
        cells=CELLS,
        columns={**sample_columns(), **(columns or {})},
        choices=sample_choices() if choices is None else choices,
        neighbourhoods=sample_neighbourhoods() if neighbourhoods is None else neighbourhoods,
        out_dir=out_dir,
        publish=publish,
    )
