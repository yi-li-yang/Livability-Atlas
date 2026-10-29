"""Writes the small data bundle that the web app's tests load: the cells within 8 steps of Soho.

The service level, the walk to the nearest station, the five crime rates and the options of the
two choice indicators come from a real
London bundle, so run `just data london` first. The other two indicators are FABRICATED, only so
that the tests have several factors to weigh: see README.md beside this file. From the repo root:

    uv run --project pipeline python web/e2e/fixtures/make_fixture.py
"""

import json
import shutil
from pathlib import Path

import h3
import pyarrow.parquet as pq

from atlas.catalogue.load import load_catalogue
from atlas.indicators import crime
from atlas.paths import REPO_ROOT, data_dir
from atlas.publish.bundle import Choice, write_bundle

OUT = REPO_ROOT / "web" / "e2e" / "fixtures" / "bundles"
SOHO = h3.latlng_to_cell(51.5136, -0.1337, 9)
CRIME = list(crime.CATEGORIES)
# The options of the two choice indicators that the fixture keeps, from the real bundle.
OPTIONS = {"faith": ("hindu", "sikh"), "your-community": ("religion-hindu", "ethnic-indian")}


def main() -> None:
    published = data_dir() / "published" / "london"
    version = json.loads((published / "latest.json").read_text(encoding="utf-8"))["version"]
    table = pq.read_table(published / version / "cells.parquet").to_pydict()
    values = dict(zip(table["cell"], table["service_level"], strict=True))
    cells = sorted(set(h3.grid_disk(SOHO, 8)) & set(values))
    row = {c: i for i, c in enumerate(table["cell"])}
    real = {
        "service-level": [values[c] for c in cells],
        "station-proximity": [table["station_proximity"][row[c]] for c in cells],
        **{
            indicator: [table[indicator.replace("-", "_")][row[c]] for c in cells]
            for indicator in CRIME
        },
    }
    manifest = json.loads((published / version / "manifest.json").read_text(encoding="utf-8"))
    choices = {}
    for indicator in manifest["indicators"]:
        wanted = OPTIONS.get(indicator["id"])
        if wanted is None:
            continue
        choices[indicator["id"]] = [
            Choice(
                id=option["id"],
                name=option["name"],
                group=option["group"],
                values=[table[option["column"]][row[c]] for c in cells],
            )
            for option in indicator["options"]
            if option["id"] in wanted
        ]
    fabricated = {
        # A pattern that varies from cell to cell.
        "walk-to-green-space": [4 + (i * 7) % 12 for i in range(len(cells))],
        "gp-walk": [5 + (i * 5) % 9 for i in range(len(cells))],
    }
    shutil.rmtree(OUT, ignore_errors=True)
    bundle = write_bundle(
        load_catalogue(),
        region_id="london",
        cells=cells,
        columns={**real, **fabricated},
        choices=choices,
        out_dir=OUT,
    )
    print(f"{len(cells)} cells in {bundle}")


if __name__ == "__main__":
    main()
