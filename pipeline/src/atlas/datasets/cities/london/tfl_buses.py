"""The rides between next stops of every bus route in London, for the way to and from the stations
(dataset `tfl-unified-api`, spike S9).

TfL's Unified API answers without a key: `Line/Mode/bus` lists the bus lines,
`Line/{id}/Route/Sequence/{direction}` gives each route's stops in order with their positions, and
`Line/{id}/Timetable/{first stop}` the minutes from that stop to each later one and the day's
departures. The departures between 07:00 and 10:00 on a weekday, counted both ways, give a line's
headway, as for TfL's rail lines (`tfl_timetables`). A line with none (the night buses, and some
school and once-a-day routes) does not run at the times the travel estimate is for, so it is left
out. A ride between next stops takes the timetable's minutes, or its straight line at `BUS_SPEED`
where no timetable times it (about 4% of rides).

About 2,700 requests make the whole set, about 70 minutes without a key, since TfL refuses more
than about 50 a minute. Every answer is kept, so a stopped fetch carries on and a build from kept
answers needs no network. They are kept trimmed to what this module reads (about 12 MB, where the
whole timetables would take several hundred), in the format that spike S9 kept. TfL's open data
licence, with attribution.
"""

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from atlas.datasets.cities.london import tfl_api
from atlas.datasets.cities.london.tfl_timetables import DIRECTIONS, headway, peak_departures
from atlas.indicators.station_matrix import Ride
from atlas.scoring.travel import straight_metres

BUS_SPEED = 250.0  # metres a minute from stop to stop where no timetable answers (15 km/h)
BUS_HEADWAY = 12.0  # a fallback for `headway` only: a line with no morning departures is left out
PAUSE = 0.4  # seconds between requests, one at a time: TfL answers about 50 a minute without a key


@dataclass(frozen=True)
class BusRoutes:
    """The bus stops by NaPTAN id with their latitude and longitude, the rides between next stops,
    and each line's minutes between buses in the weekday morning."""

    stops: dict[str, tuple[float, float]]
    rides: list[Ride]
    headways: dict[str, float]


def trim_sequence(answer: Any) -> dict[str, Any]:
    """The stops of each route in order, and each stop's latitude and longitude."""
    answer = answer or {}
    stops = {
        point["id"]: [point["lat"], point["lon"]]
        for sequence in answer.get("stopPointSequences", [])
        for point in sequence.get("stopPoint", [])
    }
    routes = [list(route["naptanIds"]) for route in answer.get("orderedLineRoutes", [])]
    return {"routes": routes, "stops": stops}


def trim_timetable(answer: Any) -> dict[str, Any]:
    """The minutes from the first stop to each later stop of each set of intervals, the departures
    between 07:00 and 10:00 on a weekday, and the positions of the stops the answer lists."""
    answer = answer if isinstance(answer, dict) else {}
    intervals = [
        [[i["stopId"], float(i["timeToArrival"])] for i in station_intervals["intervals"]]
        for route in (answer.get("timetable") or {}).get("routes", [])
        for station_intervals in route.get("stationIntervals", [])
    ]
    stops = {s["id"]: [s["lat"], s["lon"]] for s in answer.get("stops") or [] if "lat" in s}
    return {"intervals": intervals, "peak": peak_departures(answer), "stops": stops}


def _kept(path: Path, request: str, trim: Callable[[Any], Any]) -> Any:
    """The trimmed answer to `request`, asked once and then read from `path`."""
    if not path.exists():
        time.sleep(PAUSE)
        answer = tfl_api.get(request, missing=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(trim(answer)), encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def fetch(data_dir: Path) -> BusRoutes:
    """Fetches every answer that is not kept under `data/raw/tfl/buses/`, then reads them all."""
    root = data_dir / "raw" / "tfl" / "buses"
    lines = _kept(root / "lines.json", "Line/Mode/bus", lambda a: [x["id"] for x in a or []])
    for line in lines:
        for direction in DIRECTIONS:
            sequence = _kept(
                root / "sequences" / f"{line}-{direction}.json",
                f"Line/{line}/Route/Sequence/{direction}",
                trim_sequence,
            )
            for origin in sorted({route[0] for route in sequence["routes"] if route}):
                _kept(
                    root / "timetables" / f"{line}-{origin}.json",
                    f"Line/{line}/Timetable/{origin}",
                    trim_timetable,
                )
    return read(root)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def read(root: Path) -> BusRoutes:
    """The bus routes from the answers kept under `root`, leaving out a line with no weekday
    departures from 07:00 to 10:00."""
    where: dict[str, tuple[float, float]] = {}
    pairs: set[tuple[str, str, str]] = set()
    timed: dict[tuple[str, str, str], float] = {}
    headways: dict[str, float] = {}
    for line in _read_json(root / "lines.json") or []:
        routes: list[list[str]] = []
        line_where: dict[str, tuple[float, float]] = {}
        for direction in DIRECTIONS:
            sequence = _read_json(root / "sequences" / f"{line}-{direction}.json")
            if sequence:
                routes += [route for route in sequence["routes"] if route]
                line_where |= {k: (v[0], v[1]) for k, v in sequence["stops"].items()}
        departures = 0
        line_timed: dict[tuple[str, str, str], float] = {}
        for origin in sorted({route[0] for route in routes}):
            answer = _read_json(root / "timetables" / f"{line}-{origin}.json")
            if not answer:
                continue
            departures += answer["peak"]
            line_where |= {k: (v[0], v[1]) for k, v in answer["stops"].items()}
            for intervals in answer["intervals"]:
                previous, before = origin, 0.0
                for stop, minutes in intervals:
                    if stop != previous:
                        key = (line, previous, stop)
                        ride = max(minutes - before, 0.0)
                        line_timed[key] = min(ride, line_timed.get(key, ride))
                    previous, before = stop, minutes
        if departures == 0:
            continue
        headways[line] = headway(departures, BUS_HEADWAY)
        pairs |= {
            (line, a, b)
            for route in routes
            for a, b in zip(route, route[1:], strict=False)
            if a != b
        }
        timed |= line_timed
        where |= line_where
    rides = []
    for key in sorted(pairs | set(timed)):
        line, a, b = key
        if key in timed:
            rides.append(Ride(line, a, b, timed[key]))
        elif a in where and b in where:
            rides.append(Ride(line, a, b, straight_metres(*where[a], *where[b]) / BUS_SPEED))
    used = {stop for ride in rides for stop in (ride.start, ride.end)}
    return BusRoutes({s: where[s] for s in sorted(used & set(where))}, rides, headways)
