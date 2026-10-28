"""Writes the small data bundle that the web app's tests load: the cells within 8 steps of Soho.

It takes values from a real London bundle, so run `just data london` first. From the repo root:

    uv run --project pipeline python web/e2e/fixtures/make_fixture.py
"""

import json
import shutil
from pathlib import Path

import h3
import pyarrow.parquet as pq

from atlas.catalogue.load import load_catalogue
from atlas.paths import REPO_ROOT, data_dir
from atlas.publish.bundle import write_bundle

OUT = REPO_ROOT / "web" / "e2e" / "fixtures" / "bundles"
SOHO = h3.latlng_to_cell(51.5136, -0.1337, 9)


def main() -> None:
    published = data_dir() / "published" / "london"
    version = json.loads((published / "latest.json").read_text(encoding="utf-8"))["version"]
    table = pq.read_table(published / version / "cells.parquet").to_pydict()
    values = dict(zip(table["cell"], table["service_level"], strict=True))
    cells = sorted(set(h3.grid_disk(SOHO, 8)) & set(values))
    shutil.rmtree(OUT, ignore_errors=True)
    bundle = write_bundle(
        load_catalogue(),
        region_id="london",
        cells=cells,
        columns={"service-level": [values[c] for c in cells]},
        out_dir=OUT,
    )
    print(f"{len(cells)} cells in {bundle}")


if __name__ == "__main__":
    main()
