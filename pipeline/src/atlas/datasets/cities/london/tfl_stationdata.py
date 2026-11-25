"""TfL's station topology, October 2026 (dataset `tfl-station-topology`): the step-free paths inside
509 stations of the Tube, DLR, Overground, Elizabeth line, trams and the National Rail stations
that TfL serves. Two small files, with no key: GTFS pathways and the detailed station data.

The pathways hold only step-free links: level walkways, ramps and lifts, with no stairs or
escalators. So a platform that can be reached from the station's "Outside" node along them is
step-free from the street. Stations served by National Rail alone (about 140 in London, such as
Barnes or Feltham) are not in the data. TfL's open data licence (OGL v2.0 with TfL's amendments),
"Powered by TfL Open Data".
"""

import zipfile
from collections import defaultdict, deque
from pathlib import Path
from typing import cast

import pandas as pd

from atlas.fetch import download

GTFS_URL = "https://api.tfl.gov.uk/stationdata/tfl-stationdata-gtfs.zip"
DETAILED_URL = "https://api.tfl.gov.uk/stationdata/tfl-stationdata-detailed.zip"
STATION, PLATFORM, ENTRANCE = 1, 0, 3  # GTFS location types


def fetch(data_dir: Path) -> tuple[Path, Path]:
    """Downloads the GTFS and the detailed station data to `data/raw/tfl/stationdata/` once, and
    returns them."""
    folder = data_dir / "raw" / "tfl" / "stationdata"
    paths = (folder / "gtfs.zip", folder / "detailed.zip")
    for url, path in zip((GTFS_URL, DETAILED_URL), paths, strict=True):
        download(url, path)
    return paths


def _csv(archive: Path, name: str) -> pd.DataFrame:
    with zipfile.ZipFile(archive) as files:
        return pd.read_csv(files.open(name), dtype=str, keep_default_na=False, encoding="utf-8")


def read_stations(gtfs: Path, detailed: Path) -> pd.DataFrame:
    """Each station, indexed by its id: `name`, `Latitude` and `Longitude` (the mean of its points),
    `platforms`, `step_free` (the platforms reached from the street along step-free paths) and
    `all_step_free` (every platform is)."""
    stops = _csv(gtfs, "stops.txt")
    pathways = _csv(gtfs, "pathways.txt")
    points = _csv(detailed, "StationPoints.csv")

    links: dict[str, list[str]] = defaultdict(list)
    for start, end, both in pathways[["from_stop_id", "to_stop_id", "is_bidirectional"]].itertuples(
        index=False
    ):
        links[start].append(end)
        if both.strip() == "1":
            links[end].append(start)

    kind = stops["location_type"].astype(int)
    stations = stops.loc[kind == STATION, ["stop_id", "stop_name"]].set_index("stop_id")
    platforms = stops.loc[kind == PLATFORM].groupby("parent_station")["stop_id"].apply(set)
    outside = stops.loc[kind == ENTRANCE].groupby("parent_station")["stop_id"].apply(list)

    rows = []
    for station, name in stations["stop_name"].items():
        own = platforms.get(station, set())
        seen = _reached(outside.get(station, []), links)
        rows.append((station, name, len(own), len(own & seen)))
    table = pd.DataFrame(rows, columns=["station", "name", "platforms", "step_free"])
    table = table.set_index("station")
    table["all_step_free"] = (table["platforms"] > 0) & (table["step_free"] == table["platforms"])

    where = cast(
        pd.DataFrame,
        points.assign(
            Latitude=pd.to_numeric(points["Lat"], errors="coerce"),
            Longitude=pd.to_numeric(points["Lon"], errors="coerce"),
        )
        .groupby("StationUniqueId")[["Latitude", "Longitude"]]
        .mean(),
    )
    return table.join(where)


def _reached(starts: list[str], links: dict[str, list[str]]) -> set[str]:
    """Every node reached from `starts` along the links."""
    seen = set(starts)
    queue = deque(starts)
    while queue:
        for nxt in links.get(queue.popleft(), []):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen
