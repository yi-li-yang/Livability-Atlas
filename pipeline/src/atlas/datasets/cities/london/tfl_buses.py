"""The rides between next stops of every bus route in London, for the way to and from the stations
(dataset `tfl-unified-api`, spike S9).

TfL's Unified API answers without a key: `Line/Mode/bus` lists the bus lines,
`Line/{id}/Route/Sequence/{direction}` gives each route's stops in order with their positions, and
`Line/{id}/Timetable/{first stop}` the minutes from that stop to each later one and the day's
departures. The departures between 07:00 and 10:00 on a weekday give a line's headway: each
direction counts those of its busiest first stop (a short working's timetable also lists the buses
that pass its first stop from further back, so the counts are not added), and the directions are
averaged. A line with none (the night buses, and some school and once-a-day routes) does not run at
the times the travel estimate is for, so it is left out. The headway keeps the rail lines' limits
of 1.5 to 30 minutes (`tfl_timetables.HEADWAY_LIMITS`): a person plans around a bus that comes
less often than every half hour, so its wait is taken as at most 15 minutes. A ride between next
stops takes the timetable's minutes, or its straight line at `BUS_SPEED` where no timetable times
it (about 4% of rides).

About 2,700 requests make the whole set, about 70 minutes without a key, since TfL refuses more
than about 50 a minute. Every answer is kept, written whole or not at all, so a stopped fetch
carries on (an answer cut short is asked again) and a build from kept answers needs no network.
They are kept trimmed to what this module reads (about 12 MB, where the whole timetables would
take several hundred), in the format that spike S9 kept. TfL's open data licence, with
attribution.
"""

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from atlas.datasets.cities.london import tfl_api
from atlas.datasets.cities.london.tfl_timetables import (
    DIRECTIONS,
    HEADWAY_LIMITS,
    PEAK,
    peak_departures,
)
from atlas.indicators.station_matrix import Ride
from atlas.scoring.travel import straight_metres

BUS_SPEED = 250.0  # metres a minute from stop to stop where no timetable answers (15 km/h)
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
    answer = answer if isinstance(answer, dict) else {}
    stops = {
        point["id"]: [point["lat"], point["lon"]]
        for sequence in answer.get("stopPointSequences") or []
        for point in sequence.get("stopPoint") or []
        if "id" in point and "lat" in point and "lon" in point
    }
    routes = [
        list(route["naptanIds"])
        for route in answer.get("orderedLineRoutes") or []
        if route.get("naptanIds")
    ]
    return {"routes": routes, "stops": stops}


def trim_timetable(answer: Any) -> dict[str, Any]:
    """The minutes from the first stop to each later stop of each set of intervals, the departures
    between 07:00 and 10:00 on a weekday, and the positions of the stops the answer lists."""
    answer = answer if isinstance(answer, dict) else {}
    intervals = [
        [
            [i["stopId"], float(i["timeToArrival"])]
            for i in station_intervals.get("intervals") or []
            if "stopId" in i and "timeToArrival" in i
        ]
        for route in (answer.get("timetable") or {}).get("routes") or []
        for station_intervals in route.get("stationIntervals") or []
    ]
    stops = {
        s["id"]: [s["lat"], s["lon"]]
        for s in answer.get("stops") or []
        if "id" in s and "lat" in s and "lon" in s
    }
    return {"intervals": intervals, "peak": peak_departures(answer), "stops": stops}


def _kept(path: Path, request: str, trim: Callable[[Any], Any]) -> Any:
    """The trimmed answer to `request`, asked once and then read from `path`. It is written to a
    part file and then moved into place, so a stopped fetch leaves no answer cut short; one that
    does not read (written before that) is asked again."""
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    time.sleep(PAUSE)
    trimmed = trim(tfl_api.get(request, missing=True))
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    part.write_text(json.dumps(trimmed), encoding="utf-8")
    part.replace(path)
    return trimmed


def _line_ids(answer: Any) -> list[str]:
    """The ids of the lines that `Line/Mode/bus` lists. An empty list is an error, not an answer:
    kept, it would leave every later build without buses."""
    ids = [x["id"] for x in answer or [] if "id" in x]
    if not ids:
        raise RuntimeError("TfL listed no bus lines; try the fetch again later")
    return ids


def fetch(data_dir: Path) -> BusRoutes:
    """Fetches every answer that is not kept under `data/raw/tfl/buses/`, then reads them all."""
    root = data_dir / "raw" / "tfl" / "buses"
    lines = _kept(root / "lines.json", "Line/Mode/bus", _line_ids)
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
        origins_of: dict[str, set[str]] = {}
        line_where: dict[str, tuple[float, float]] = {}
        for direction in DIRECTIONS:
            sequence = _read_json(root / "sequences" / f"{line}-{direction}.json")
            if sequence:
                found = [route for route in sequence["routes"] if route]
                routes += found
                origins_of[direction] = {route[0] for route in found}
                line_where |= {k: (v[0], v[1]) for k, v in sequence["stops"].items()}
        peak: dict[str, int] = {}
        line_timed: dict[tuple[str, str, str], float] = {}
        for origin in sorted({route[0] for route in routes}):
            answer = _read_json(root / "timetables" / f"{line}-{origin}.json")
            if not answer:
                continue
            peak[origin] = answer["peak"]
            line_where |= {k: (v[0], v[1]) for k, v in answer["stops"].items()}
            for intervals in answer["intervals"]:
                previous, before = origin, 0.0
                for stop, minutes in intervals:
                    if stop != previous:
                        key = (line, previous, stop)
                        ride = max(minutes - before, 0.0)
                        line_timed[key] = min(ride, line_timed.get(key, ride))
                    previous, before = stop, minutes
        each_way = [
            busiest
            for origins in origins_of.values()
            if (busiest := max((peak.get(o, 0) for o in origins), default=0)) > 0
        ]
        if not each_way:
            continue
        minutes = (PEAK[1] - PEAK[0]) * 60 / mean(each_way)
        headways[line] = min(max(minutes, HEADWAY_LIMITS[0]), HEADWAY_LIMITS[1])
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
