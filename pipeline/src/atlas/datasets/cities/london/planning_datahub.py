"""Homes completed in London, from the GLA's Planning London Datahub (dataset
`gla-planning-london-datahub`): the planning applications of every London planning authority, with
each scheme's place and the homes it gains and loses, each with its own completion date.

The Datahub answers searches without a key (its public API guide gives the header value to send).
Only the schemes completed in five financial years, April 2020 to March 2025, are fetched: boroughs
report completions once a year, so later years are not yet whole. Each scheme is kept as its id,
place and homes gained and lost in the window. Its licence is not stated: see the dataset's
licence note.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

SEARCH = "https://planningdata.london.gov.uk/api-guest/applications/_search"
SCROLL = "https://planningdata.london.gov.uk/api-guest/_search/scroll"
HEADERS = {"X-API-AllowRequest": "be2rmRnt&", "Content-Type": "application/json"}
START, END = date(2020, 4, 1), date(2025, 3, 31)
PAGE = 2000
FIELDS = [
    "id",
    "actual_completion_date",
    "centroid_easting",
    "centroid_northing",
    "application_details.residential_details.residential_units.change_type",
    "application_details.residential_details.residential_units.actual_completion_date",
]


def _day(text: str | None) -> date | None:
    if not text:
        return None
    try:
        return datetime.strptime(text.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def homes(source: dict[str, Any]) -> dict[str, Any] | None:
    """A scheme's id, place (`x`, `y`, in metres of British National Grid) and the homes it
    `gained` and `lost` that were completed in the window: each home by its own completion date,
    or the scheme's where it has none. None for a scheme with no place."""
    x, y = source.get("centroid_easting"), source.get("centroid_northing")
    if x is None or y is None:
        return None
    scheme_day = _day(source.get("actual_completion_date"))
    details = (source.get("application_details") or {}).get("residential_details") or {}
    counts = {"gain": 0, "loss": 0}
    for unit in details.get("residential_units") or []:
        change = str(unit.get("change_type") or "").strip().lower()
        day = _day(unit.get("actual_completion_date")) or scheme_day
        if change in counts and day is not None and START <= day <= END:
            counts[change] += 1
    return {
        "id": source.get("id"),
        "x": float(x),
        "y": float(y),
        "gained": counts["gain"],
        "lost": counts["loss"],
    }


def fetch(data_dir: Path) -> Path:
    """Fetches the schemes completed in the window to `data/raw/gla-planning/` once, and returns
    the file."""
    target = data_dir / "raw" / "gla-planning" / f"completions-{START:%Y%m}-{END:%Y%m}.json"
    if target.exists():
        return target
    query = {
        "size": PAGE,
        "_source": FIELDS,
        "sort": ["_doc"],
        "query": {
            "range": {
                "actual_completion_date": {
                    "gte": f"{START:%d/%m/%Y}",
                    "lte": f"{END:%d/%m/%Y}",
                    "format": "dd/MM/yyyy",
                }
            }
        },
    }
    reply = requests.post(
        SEARCH, params={"scroll": "2m"}, headers=HEADERS, data=json.dumps(query), timeout=120
    )
    reply.raise_for_status()
    body = reply.json()
    rows: list[dict[str, Any]] = []
    while body["hits"]["hits"]:
        rows += [r for hit in body["hits"]["hits"] if (r := homes(hit["_source"])) is not None]
        reply = requests.post(
            SCROLL,
            headers=HEADERS,
            data=json.dumps({"scroll": "2m", "scroll_id": body["_scroll_id"]}),
            timeout=120,
        )
        reply.raise_for_status()
        body = reply.json()
    if not rows:
        raise RuntimeError("the Planning London Datahub returned no completed schemes")
    rows.sort(key=lambda r: str(r["id"]))
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    partial.write_text(json.dumps(rows), encoding="utf-8", newline="\n")
    partial.replace(target)
    return target


def read_completions(path: Path) -> pd.DataFrame:
    """The kept schemes: `id`, `x`, `y`, `gained` and `lost`."""
    return pd.DataFrame(json.loads(path.read_text(encoding="utf-8")))
