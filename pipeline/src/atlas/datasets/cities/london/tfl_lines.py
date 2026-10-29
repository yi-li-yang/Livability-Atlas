"""The lines and routes that serve each stop in London (dataset `tfl-unified-api`).

TfL's Unified API lists the stop points of every line: Tube, DLR, Overground, Elizabeth line,
tram and National Rail operators as TfL lists them, and the day bus routes. It answers without
a key at a modest rate, and about 700 requests make the whole table, so the table is kept after
the first fetch. TfL's open data licence, with attribution.
"""

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.datasets.cities.london import tfl_api

RAIL_MODES = "tube,dlr,overground,elizabeth-line,tram,national-rail"
KINDS = {"rail": RAIL_MODES, "bus": "bus"}
PAUSE = 1.3  # seconds between requests: without a key TfL allows about 50 a minute


def _get(path: str) -> Any:
    """One request to the API, waiting and trying again when TfL asks to slow down."""
    return tfl_api.get(path)


def _zone(point: dict[str, Any]) -> str:
    """The fare zone TfL gives a stop, such as `2` or `2+3`, or empty text where it gives none."""
    for property in point.get("additionalProperties", []):
        if property.get("key") == "Zone":
            return str(property.get("value", ""))
    return ""


def _day_lines(path: str) -> list[str]:
    """The ids of the lines of a mode, leaving out a line that only runs at night."""
    return [
        entry["id"]
        for entry in _get(path)
        if any(s["name"] != "Night" for s in entry["serviceTypes"]) or not entry["serviceTypes"]
    ]


def fetch(data_dir: Path) -> Path:
    """Fetches the stop points of every line to `data/raw/tfl/line-stops-v2.parquet` once, and
    returns it. Each line's answer is kept in `data/raw/tfl/stops/`, so a stopped fetch carries
    on, and a new table is made from the answers already kept."""
    target = data_dir / "raw" / "tfl" / "line-stops-v2.parquet"
    if target.exists():
        return target
    kept = target.parent / "stops"  # each line's answer, so a stopped fetch carries on
    kept.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for kind, modes in KINDS.items():
        for line in _day_lines(f"Line/Mode/{modes}"):
            answer = kept / f"{kind}-{line}.json"
            if not answer.exists():
                time.sleep(PAUSE)
                answer.write_text(json.dumps(_get(f"Line/{line}/StopPoints")), encoding="utf-8")
            for point in json.loads(answer.read_text(encoding="utf-8")):
                rows.append(
                    {
                        "kind": kind,
                        "line": line,
                        "stop": point["id"],
                        "Latitude": point["lat"],
                        "Longitude": point["lon"],
                        "zone": _zone(point),
                    }
                )
    target.parent.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(rows).drop_duplicates(["kind", "line", "stop"])
    table.to_parquet(target.with_name(target.name + ".part"))
    target.with_name(target.name + ".part").replace(target)
    return target


def read_stops(path: Path) -> pd.DataFrame:
    """A row for each line at each stop: `kind` (`rail` or `bus`), `line`, `stop`, `Latitude`,
    `Longitude` and the fare `zone` TfL gives the stop (empty for most)."""
    return pd.read_parquet(path)
