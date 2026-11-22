"""Writes the small data bundle that the web app's tests load: the cells within 8 steps of Soho.

The service level, the walk to the nearest station, the travel time to the default places, the
five crime rates, the options of the two choice indicators, the neighbourhoods, and the travel
files cut to these cells (their stations, the matrix between those, and the postcodes around)
come from a real
London bundle, so run `just data london` first. The other two indicators are FABRICATED, only so
that the tests have several factors to weigh: see README.md beside this file. From the repo root:

    uv run --project pipeline python web/e2e/fixtures/make_fixture.py
"""

import json
import shutil

import h3
import numpy as np
import pyarrow.parquet as pq

from atlas.catalogue.load import load_catalogue
from atlas.indicators import crime
from atlas.paths import REPO_ROOT, data_dir
from atlas.publish.bundle import Choice, Neighbourhoods, Travel, write_bundle

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
        "travel-time-to-places": [table["travel_time_to_places"][row[c]] for c in cells],
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
    # The neighbourhoods the cells are in, renumbered for the cells that the fixture keeps.
    old = [table["neighbourhood"][row[c]] for c in cells]
    kept = sorted({i for i in old if i is not None})
    renumbered = {i: n for n, i in enumerate(kept)}
    neighbourhoods = Neighbourhoods(
        listing=[
            (manifest["neighbourhoods"][i]["name"], manifest["neighbourhoods"][i]["area"])
            for i in kept
        ],
        of_cell=[None if i is None else renumbered[i] for i in old],
        datasets=["hoc-msoa-names", "ons-msoa-boundaries"],
    )
    fabricated = {
        # A pattern that varies from cell to cell.
        "walk-to-green-space": [4 + (i * 7) % 12 for i in range(len(cells))],
        "gp-walk": [5 + (i * 5) % 9 for i in range(len(cells))],
    }
    travel = _travel(published / version, manifest, table["cell"], cells)
    shutil.rmtree(OUT, ignore_errors=True)
    bundle = write_bundle(
        load_catalogue(),
        region_id="london",
        cells=cells,
        columns={**real, **fabricated},
        choices=choices,
        neighbourhoods=neighbourhoods,
        travel=travel,
        out_dir=OUT,
    )
    print(f"{len(cells)} cells in {bundle}")


def _travel(folder, manifest, all_cells, cells) -> Travel | None:
    """The real bundle's travel files cut to the fixture's cells: the stations their cells walk
    to, the matrix between those stations, and the postcodes within the cells' box."""
    t = manifest.get("travel")
    if t is None:
        return None
    stations = pq.read_table(folder / t["stations"]).to_pydict()
    links = pq.read_table(folder / t["cell_stations"]).to_pydict()
    n = t["station_count"]
    matrix = pq.read_table(folder / t["matrix"]).column("minutes").to_numpy().reshape(n, n)
    position = {c: i for i, c in enumerate(cells)}
    kept = [
        (position[all_cells[c]], s, m)
        for c, s, m in zip(links["cell"], links["station"], links["minutes"], strict=True)
        if all_cells[c] in position
    ]
    used = sorted({s for _, s, _ in kept})
    renumbered = {s: i for i, s in enumerate(used)}
    centres = np.array([h3.cell_to_latlng(c) for c in cells])
    (south, west), (north, east) = centres.min(axis=0), centres.max(axis=0)
    codes = pq.read_table(folder / t["postcodes"]).to_pydict() if t.get("postcodes") else {}
    postcodes = [
        (p, float(lat), float(lng))
        for p, lat, lng in zip(
            codes.get("postcode", []), codes.get("lat", []), codes.get("lng", []), strict=True
        )
        if south <= lat <= north and west <= lng <= east
    ]
    return Travel(
        stations=[(stations["stop"][s], stations["lat"][s], stations["lng"][s]) for s in used],
        cell_stations=[(c, renumbered[s], m) for c, s, m in kept],
        matrix=matrix[np.ix_(used, used)],
        indicator=t["indicator"],
        reach_minutes=t["reach_minutes"],
        postcodes=postcodes,
    )


if __name__ == "__main__":
    main()
