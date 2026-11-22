"""The rides between next stops of every rail line, for the station matrix (dataset
`tfl-unified-api`).

TfL's own lines (Tube, DLR, Overground, Elizabeth line, tram) have timetables in the Unified API:
`Line/{id}/Route/Sequence/{direction}` gives each route's stops in order, and
`Line/{id}/Timetable/{first stop}` the minutes from that stop to each later one and the day's
departures, whose number between 07:00 and 10:00 on Monday to Thursday gives the headway. National
Rail lines have stop orders but no timetable there, so the minutes between two stops that a
service calls at one after the other come from one Journey Planner call each, by National Rail
only, at 08:30 on a Wednesday. The Journey Planner answers only for days to come, so the day is
a fixed one that was ahead when the answers were kept (`DATE`). Both answer without a key;
every answer is kept, so a stopped fetch carries on. TfL's open data licence, with attribution.

Not every answer comes: some timetables fail at TfL's end, a few lines list no weekday, and the
Journey Planner finds no train for some pairs. So every pair of next stops that a route sequence
gives is a ride, timed by the timetable or the Journey Planner where they answer and otherwise by
its straight line at the mode's speed between stops; a line with no weekday departures takes its
mode's usual headway. Both defaults are stated here.

The answers are API answers, not files, so they are kept by `_kept` and in a CSV (as
`tfl_journeys` keeps its times) rather than through `atlas.fetch.download`. The list of lines is
kept too, so a build from kept answers needs no network and gives the same matrix.
"""

import csv
import json
import time
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.datasets.cities.london import tfl_api
from atlas.indicators.station_matrix import Ride
from atlas.scoring.travel import straight_metres

TFL_MODES = "tube,dlr,overground,elizabeth-line,tram"
DATE = "20261125"  # a Wednesday; the Journey Planner refuses a day that has passed
TIME = "0830"
NATIONAL_RAIL = "national-rail"
DIRECTIONS = ("inbound", "outbound")
PEAK = (7, 10)  # the hours whose departures give the headway: 07:00 to 10:00
# TfL gives no National Rail timetable, so its headway is a stated default, in minutes.
NATIONAL_RAIL_HEADWAY = 12.0
# Each mode's usual minutes between trains in the morning, where its timetable lists no weekday.
MODE_HEADWAY = {"tube": 4.0, "dlr": 6.0, "overground": 10.0, "elizabeth-line": 6.0, "tram": 8.0}
# Each mode's mean speed from stop to stop, stops included, in metres a minute (a stated default
# where no timetable answers: Tube about 33 km/h, National Rail about 54 km/h).
MODE_SPEED = {
    "tube": 550.0,
    "dlr": 450.0,
    "overground": 600.0,
    "elizabeth-line": 700.0,
    "tram": 350.0,
    NATIONAL_RAIL: 900.0,
}
# A line is taken to run at most every 90 seconds, and at least every half hour.
HEADWAY_LIMITS = (1.5, 30.0)
# More pairs than this share with no train means the Journey Planner refused the day (it has
# passed), not that the trains are missing: about one pair in ten has no single train.
MOST_EMPTY = 0.5
PAUSE = 1.3
WORKERS = 3


def _kept(path: Path, request: str) -> Any:
    """An answer of the API, asked once and then read from `path`."""
    if not path.exists():
        time.sleep(PAUSE)
        answer = tfl_api.get(request, missing=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(answer), encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def _day_lines(root: Path, modes: str) -> list[tuple[str, str]]:
    """The ids and modes of the lines of some modes, leaving out a line that runs only at night.
    The answer is kept under `root`."""
    answer = _kept(root / "lines-of" / f"{modes.replace(',', '-')}.json", f"Line/Mode/{modes}")
    return [
        (entry["id"], entry["modeName"])
        for entry in answer or []
        if any(s["name"] != "Night" for s in entry["serviceTypes"]) or not entry["serviceTypes"]
    ]


def route_stops(sequence: Any) -> list[list[str]]:
    """The stops of each route of a `Route/Sequence` answer, in order (NaPTAN ids)."""
    return [list(route["naptanIds"]) for route in (sequence or {}).get("orderedLineRoutes", [])]


def timetable_rides(answer: Any, line: str, origin: str) -> list[Ride]:
    """The rides between next stops that a `Timetable/{origin}` answer gives. Its intervals are the
    minutes from `origin` to each later stop, so a ride is the difference between two."""
    rides = []
    for route in ((answer or {}).get("timetable") or {}).get("routes", []):
        for intervals in route.get("stationIntervals", []):
            previous, before = origin, 0.0
            for interval in intervals.get("intervals", []):
                stop, minutes = interval["stopId"], float(interval["timeToArrival"])
                if stop != previous:
                    rides.append(Ride(line, previous, stop, max(minutes - before, 0.5)))
                previous, before = stop, minutes
    return rides


def _weekday(schedules: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The schedule of a weekday: one named for Monday, or else one not named for the weekend."""
    for schedule in schedules:
        if "Monday" in schedule.get("name", ""):
            return schedule
    for schedule in schedules:
        name = schedule.get("name", "")
        if "Saturday" not in name and "Sunday" not in name:
            return schedule
    return None


def peak_departures(answer: Any) -> int:
    """The departures between 07:00 and 10:00 on a weekday that a timetable lists."""
    count = 0
    for route in ((answer or {}).get("timetable") or {}).get("routes", []):
        schedule = _weekday(route.get("schedules", []))
        if schedule is None:
            continue
        count += sum(
            1
            for journey in schedule.get("knownJourneys", [])
            if PEAK[0] <= int(journey["hour"]) < PEAK[1]
        )
    return count


def headway(departures_both_ways: int, usual: float = HEADWAY_LIMITS[1]) -> float:
    """The minutes between trains, from the peak departures counted in both directions, or the
    mode's `usual` headway where none are counted."""
    if departures_both_ways <= 0:
        return usual
    each_way = departures_both_ways / 2
    minutes = (PEAK[1] - PEAK[0]) * 60 / each_way
    return min(max(minutes, HEADWAY_LIMITS[0]), HEADWAY_LIMITS[1])


def rail_minutes(answer: Any) -> float | None:
    """The minutes on the train of the quickest journey that is one National Rail ride, or None."""
    rides = [
        float(legs[0]["duration"])
        for journey in (answer or {}).get("journeys", [])
        if len(legs := journey.get("legs", [])) == 1
        and legs[0].get("mode", {}).get("id") == NATIONAL_RAIL
    ]
    return min(rides) if rides else None


def next_stop_pairs(routes: Iterable[list[str]], inside: set[str]) -> set[tuple[str, str]]:
    """The pairs of stops that a route calls at one after the other, both in `inside`."""
    return {
        (a, b)
        for stops in routes
        for a, b in zip(stops, stops[1:], strict=False)
        if a in inside and b in inside and a != b
    }


def timed_rides(
    line: str,
    pairs: set[tuple[str, str]],
    minutes: dict[tuple[str, str], float],
    where: dict[str, tuple[float, float]],
    speed: float,
) -> list[Ride]:
    """A ride for each pair of next stops: the minutes that a timetable or the Journey Planner
    gave, or else its straight line at `speed` metres a minute."""
    rides = []
    for a, b in sorted(pairs):
        known = minutes.get((a, b))
        if known is None:
            known = max(straight_metres(*where[a], *where[b]) / speed, 0.5)
        rides.append(Ride(line, a, b, known))
    return rides


def fetch(
    data_dir: Path, where: dict[str, tuple[float, float]]
) -> tuple[list[Ride], dict[str, float]]:
    """The rides between next stops of every rail line among the stations of `where` (a stop's
    latitude and longitude), and each line's headway. TfL's lines are timed by their timetables
    and National Rail by the Journey Planner. Every answer is kept under
    `data/raw/tfl/timetables/`."""
    root = data_dir / "raw" / "tfl" / "timetables"
    inside = set(where)
    rides: list[Ride] = []
    headways: dict[str, float] = {}
    for line, mode in _day_lines(root, TFL_MODES):
        departures = 0
        routes: list[list[str]] = []
        timed: dict[tuple[str, str], float] = {}
        for direction in DIRECTIONS:
            sequence = _kept(
                root / "sequences" / f"{line}-{direction}.json",
                f"Line/{line}/Route/Sequence/{direction}",
            )
            routes += route_stops(sequence)
            for origin in sorted({route[0] for route in route_stops(sequence) if route}):
                answer = _kept(
                    root / "lines" / f"{line}-{origin}.json", f"Line/{line}/Timetable/{origin}"
                )
                for ride in timetable_rides(answer, line, origin):
                    pair = (ride.start, ride.end)
                    timed[pair] = min(ride.minutes, timed.get(pair, ride.minutes))
                departures += peak_departures(answer)
        headways[line] = headway(departures, MODE_HEADWAY.get(mode, HEADWAY_LIMITS[1]))
        pairs = next_stop_pairs(routes, inside)
        rides += timed_rides(line, pairs, timed, where, MODE_SPEED.get(mode, 500.0))

    pairs_of: dict[str, set[tuple[str, str]]] = {}
    for line, _ in _day_lines(root, NATIONAL_RAIL):
        routes = []
        for direction in DIRECTIONS:
            sequence = _kept(
                root / "sequences" / f"{line}-{direction}.json",
                f"Line/{line}/Route/Sequence/{direction}",
            )
            routes += route_stops(sequence)
        pairs_of[line] = next_stop_pairs(routes, inside)
        headways[line] = NATIONAL_RAIL_HEADWAY
    minutes = _national_rail_minutes(root / f"national-rail-{DATE}-{TIME}.csv", pairs_of)
    for line, line_pairs in sorted(pairs_of.items()):
        rides += timed_rides(line, line_pairs, minutes, where, MODE_SPEED[NATIONAL_RAIL])
    return rides, headways


def _national_rail_minutes(
    target: Path, pairs: dict[str, set[tuple[str, str]]]
) -> dict[tuple[str, str], float]:
    """The minutes of each pair, asked of the Journey Planner once (a pair that several operators
    serve is asked once) and kept a line at a time in `target`. A pair with no train is kept only
    once the fetch has ended, and only if most pairs had one: otherwise the day has passed, and
    the fetch stops rather than keep answers that are not true."""
    done: dict[tuple[str, str], float | None] = {}
    if target.exists():
        kept = pd.read_csv(target, dtype={"start": str, "end": str})
        for a, b, m in zip(kept["start"], kept["end"], kept["minutes"], strict=True):
            done[(a, b)] = None if pd.isna(m) else float(m)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("start,end,minutes\n", encoding="utf-8", newline="\n")
    wanted = sorted({p for line_pairs in pairs.values() for p in line_pairs} - set(done))

    def ask(pair: tuple[str, str]) -> tuple[str, str, float | None]:
        a, b = pair
        time.sleep(PAUSE)
        answer = tfl_api.get(
            f"Journey/JourneyResults/{a}/to/{b}?date={DATE}&time={TIME}&timeIs=Departing"
            f"&journeyPreference=LeastTime&mode={NATIONAL_RAIL}",
            missing=True,
        )
        return a, b, rail_minutes(answer)

    empty: list[tuple[str, str]] = []
    with target.open("a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        pool = ThreadPoolExecutor(WORKERS)
        try:
            for future in as_completed([pool.submit(ask, pair) for pair in wanted]):
                a, b, m = future.result()
                done[(a, b)] = m
                if m is None:
                    empty.append((a, b))
                else:
                    writer.writerow([a, b, m])
                    file.flush()
        except BaseException:
            pool.shutdown(wait=True, cancel_futures=True)  # no request still flying once we stop
            raise
        pool.shutdown()
        check_answered(len(wanted), len(empty))
        for a, b in sorted(empty):
            writer.writerow([a, b, ""])
    return {pair: m for pair, m in done.items() if m is not None}


def check_answered(asked: int, empty: int) -> None:
    """Stops a fetch whose answers were mostly empty: the Journey Planner refuses a day that has
    passed, so `DATE` must move ahead to a coming Wednesday."""
    if asked >= 10 and empty > asked * MOST_EMPTY:
        raise RuntimeError(
            f"The Journey Planner answered nothing for {empty} of {asked} journeys: {DATE} has "
            "likely passed. Move tfl_timetables.DATE to a coming Wednesday and fetch again."
        )
