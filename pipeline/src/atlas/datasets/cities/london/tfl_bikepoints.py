"""London's cycle hire docking stations, Santander Cycles (dataset `tfl-unified-api`).

TfL's Unified API lists every docking station (`BikePoint`), about 800, with no key. Its answer
also counts the bikes and empty docks of the moment, so only each station's id, name and place
are kept, after the first fetch. TfL's open data licence, with attribution.
"""

import json
from pathlib import Path

import pandas as pd

from atlas.datasets.cities.london import tfl_api
from atlas.indicators.transport import place_stops


def fetch(data_dir: Path) -> Path:
    """Fetches the docking stations to `data/raw/tfl/bikepoints.json` once, and returns it."""
    target = data_dir / "raw" / "tfl" / "bikepoints.json"
    if target.exists():
        return target
    answer = tfl_api.get("BikePoint")
    docks = [
        {"id": d["id"], "name": d["commonName"], "lat": d["lat"], "lon": d["lon"]} for d in answer
    ]
    if not docks:
        raise RuntimeError("TfL listed no docking stations")
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    partial.write_text(json.dumps(docks, sort_keys=True), encoding="utf-8", newline="\n")
    partial.replace(target)
    return target


def read_docks(path: Path) -> pd.DataFrame:
    """The docking stations: `id`, `name`, and their place (`Latitude`, `Longitude`, `Easting`,
    `Northing`)."""
    docks = pd.DataFrame(json.loads(path.read_text(encoding="utf-8")))
    docks = docks.rename(columns={"lat": "Latitude", "lon": "Longitude"})
    return place_stops(docks)
