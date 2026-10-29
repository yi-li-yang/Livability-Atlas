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
import requests

API = "https://api.tfl.gov.uk/"
RAIL_MODES = "tube,dlr,overground,elizabeth-line,tram,national-rail"
KINDS = {"rail": RAIL_MODES, "bus": "bus"}
RETRIES = 8
PAUSE = 1.3  # seconds between requests: without a key TfL allows about 50 a minute


def _get(path: str) -> Any:
    """One request to the API, waiting and trying again when TfL asks to slow down."""
    for attempt in range(RETRIES):
        reply = requests.get(API + path, timeout=120)
        if reply.status_code != 429:
            reply.raise_for_status()
            return reply.json()
        time.sleep(15.0 * (attempt + 1))
    raise RuntimeError(f"TfL kept refusing {path}")


def _day_lines(path: str) -> list[str]:
    """The ids of the lines of a mode, leaving out a line that only runs at night."""
    return [
        entry["id"]
        for entry in _get(path)
        if any(s["name"] != "Night" for s in entry["serviceTypes"]) or not entry["serviceTypes"]
    ]


def fetch(data_dir: Path) -> Path:
    """Fetches the stop points of every line to `data/raw/tfl/line-stops.parquet` once, and
    returns it. A failed request leaves no file."""
    target = data_dir / "raw" / "tfl" / "line-stops.parquet"
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
                    }
                )
    target.parent.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(rows).drop_duplicates(["kind", "line", "stop"])
    table.to_parquet(target.with_name(target.name + ".part"))
    target.with_name(target.name + ".part").replace(target)
    return target


def read_stops(path: Path) -> pd.DataFrame:
    """A row for each line at each stop: `kind` (`rail` or `bus`), `line`, `stop`, `Latitude`
    and `Longitude`."""
    return pd.read_parquet(path)
