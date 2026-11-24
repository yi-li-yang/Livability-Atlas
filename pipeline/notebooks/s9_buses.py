"""Spike S9: buses to and from the stations, for the travel estimate (D10).

Throwaway code, never imported by `atlas`. The travel estimate walks from a cell to a station, rides
the station matrix, and walks from a station to the place, so it is too long where a bus would take
a person to or from the station sooner (S4: a median 11 minutes too long). This script asks whether
TfL's bus routes and timetables, which the Unified API gives without a key, can give a walk-and-bus
leg to and from the stations, and how much that cuts the error that `atlas travel-check` measured.

`fetch` keeps every answer, trimmed to what the analysis reads, under `data/raw/tfl/buses/`, so a
stopped run carries on. `analyse` needs the London bundle and the kept travel-check answers.
Run from `pipeline/` with `PYTHONUTF8=1 ./.venv/Scripts/python.exe notebooks/s9_buses.py fetch`,
then `... analyse`.
"""

import json
import pickle
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import h3
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import KDTree

from atlas.datasets.cities.london import tfl_api
from atlas.datasets.cities.london.tfl_timetables import DATE, PEAK, _weekday, headway
from atlas.paths import data_dir
from atlas.scoring.travel import straight_metres
from atlas.travel_check import TIMES, errors, sample_pairs, table

ROOT = data_dir() / "raw" / "tfl" / "buses"
DIRECTIONS = ("inbound", "outbound")
PAUSE = 0.4  # one request at a time: TfL answers about 50 a minute without a key
WORKERS = 1

BUNDLE = data_dir() / "published" / "london" / "dc3d5a941943"
INTERIM = data_dir() / "interim" / "s9"
STOP_WALK = 10.0  # the longest walk from a cell's centre to a bus stop, in minutes
TO_STATION = 6.0  # the longest walk from a bus stop to a station (straight line, street factor)
BUS_SPEED = 250.0  # metres a minute from stop to stop where no timetable answers (15 km/h)
BUS_HEADWAY = 12.0  # a fallback only: a line with no morning departures is left out
BOARD = 0.5  # minutes to board a bus, beyond the wait
REACH = 40.0  # the longest way to a station, as the walk is now
STREET = 1.33
WALK = 80.0
UNREACHABLE = 65535
_TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)


def _keep(path: Path, request: str, trim: Any) -> Any:
    """The trimmed answer to `request`, asked once and then read from `path`."""
    if not path.exists():
        time.sleep(PAUSE)
        answer = tfl_api.get(request, missing=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(trim(answer)), encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def trim_sequence(answer: Any) -> dict[str, Any]:
    """The stops of each route in order, and each stop's latitude and longitude."""
    answer = answer or {}
    stops = {
        p["id"]: [p["lat"], p["lon"]]
        for seq in answer.get("stopPointSequences", [])
        for p in seq.get("stopPoint", [])
    }
    routes = [list(r["naptanIds"]) for r in answer.get("orderedLineRoutes", [])]
    return {"routes": routes, "stops": stops}


def trim_timetable(answer: Any) -> dict[str, Any]:
    """The minutes from the first stop to each later stop of each interval set, the departures
    between 07:00 and 10:00 on a weekday, and the stops' positions."""
    table = ((answer or {}).get("timetable") or {}) if isinstance(answer, dict) else {}
    intervals: list[list[list[Any]]] = []
    peak = 0
    for route in table.get("routes", []):
        for station_intervals in route.get("stationIntervals", []):
            intervals.append(
                [[i["stopId"], float(i["timeToArrival"])] for i in station_intervals["intervals"]]
            )
        schedule = _weekday(route.get("schedules", []))
        if schedule is not None:
            peak += sum(
                1 for j in schedule.get("knownJourneys", []) if PEAK[0] <= int(j["hour"]) < PEAK[1]
            )
    stops = {
        s["id"]: [s["lat"], s["lon"]]
        for s in ((answer or {}).get("stops") or [])
        if isinstance(answer, dict) and "lat" in s
    }
    return {"intervals": intervals, "peak": peak, "stops": stops}


def fetch() -> None:
    lines = _keep(ROOT / "lines.json", "Line/Mode/bus", lambda a: [x["id"] for x in a or []])
    print(f"{len(lines)} bus lines")
    jobs = [(line, d) for line in lines for d in DIRECTIONS]

    def sequence(job: tuple[str, str]) -> tuple[str, str, Any]:
        line, d = job
        path = ROOT / "sequences" / f"{line}-{d}.json"
        return line, d, _keep(path, f"Line/{line}/Route/Sequence/{d}", trim_sequence)

    origins: set[tuple[str, str]] = set()
    with ThreadPoolExecutor(WORKERS) as pool:
        for n, future in enumerate(as_completed([pool.submit(sequence, j) for j in jobs]), 1):
            line, _, seq = future.result()
            origins |= {(line, r[0]) for r in seq["routes"] if r}
            if n % 100 == 0:
                print(f"sequences {n}/{len(jobs)}", flush=True)
    print(f"{len(origins)} timetables to keep")

    def timetable(job: tuple[str, str]) -> None:
        line, origin = job
        path = ROOT / "timetables" / f"{line}-{origin}.json"
        _keep(path, f"Line/{line}/Timetable/{origin}", trim_timetable)

    with ThreadPoolExecutor(WORKERS) as pool:
        for n, future in enumerate(
            as_completed([pool.submit(timetable, j) for j in sorted(origins)]), 1
        ):
            future.result()
            if n % 100 == 0:
                print(f"timetables {n}/{len(origins)}", flush=True)
    print("fetched")


def bng(latlon: np.ndarray) -> np.ndarray:
    x, y = _TO_BNG.transform(latlon[:, 1], latlon[:, 0])
    return np.column_stack([x, y])


def bus_network() -> tuple[list[str], dict[str, tuple[float, float]], list[tuple], dict, dict]:
    """The bus stops, their positions, the rides between next stops (line, a, b, minutes), each
    line's headway, and counts for the write-up."""
    lines = json.loads((ROOT / "lines.json").read_text(encoding="utf-8"))
    where: dict[str, tuple[float, float]] = {}
    pairs: set[tuple[str, str, str]] = set()
    timed: dict[tuple[str, str, str], float] = {}
    headways: dict[str, float] = {}
    counts = {
        "lines": 0,
        "lines with no morning departures, left out": 0,
        "sequences": 0,
        "timetables": 0,
        "timetables answered": 0,
    }
    for line in lines:
        origins: set[str] = set()
        line_pairs: set[tuple[str, str, str]] = set()
        for d in DIRECTIONS:
            path = ROOT / "sequences" / f"{line}-{d}.json"
            if not path.exists():
                continue
            counts["sequences"] += 1
            seq = json.loads(path.read_text(encoding="utf-8"))
            where.update({k: (v[0], v[1]) for k, v in seq["stops"].items()})
            for route in seq["routes"]:
                line_pairs |= {
                    (line, a, b) for a, b in zip(route, route[1:], strict=False) if a != b
                }
                if route:
                    origins.add(route[0])
        if not origins:
            continue
        departures = 0
        line_timed: dict[tuple[str, str, str], float] = {}
        for origin in origins:
            path = ROOT / "timetables" / f"{line}-{origin}.json"
            if not path.exists():
                continue
            counts["timetables"] += 1
            t = json.loads(path.read_text(encoding="utf-8"))
            counts["timetables answered"] += bool(t["intervals"])
            departures += t["peak"]
            for intervals in t["intervals"]:
                previous, before = None, 0.0
                for stop, minutes in intervals:
                    if previous is not None and stop != previous:
                        key = (line, previous, stop)
                        ride = max(minutes - before, 0.0)
                        line_timed[key] = min(ride, line_timed.get(key, ride))
                    previous, before = stop, minutes
        # A line with no weekday departures from 07:00 to 10:00 (the night buses, some school and
        # once-a-day routes) does not run at the times the check asks about.
        if departures == 0:
            counts["lines with no morning departures, left out"] += 1
            continue
        counts["lines"] += 1
        pairs |= line_pairs
        timed.update(line_timed)
        headways[line] = headway(departures, BUS_HEADWAY)
    rides = []
    untimed = 0
    for key in sorted(pairs | set(timed)):
        if key in timed:
            rides.append((*key, timed[key]))
        elif key[1] in where and key[2] in where:
            untimed += 1
            metres = straight_metres(*where[key[1]], *where[key[2]])
            rides.append((*key, metres / BUS_SPEED))
    counts["rides"] = len(rides)
    counts["rides untimed"] = untimed
    stops = sorted({r[1] for r in rides} | {r[2] for r in rides})
    counts["stops"] = len(stops)
    counts["stops placed"] = sum(s in where for s in stops)
    return stops, where, rides, headways, counts


def bus_graph(
    stops: list[str],
    where: dict[str, tuple[float, float]],
    rides: list[tuple],
    headways: dict[str, float],
    station_xy: np.ndarray,
) -> tuple[Any, int, int]:
    """A graph whose first `len(stops)` nodes are the stops and whose last `len(station_xy)` nodes
    are the stations: a stop boards each line that calls at it (half the headway and `BOARD`), a
    line rides to its next stop, a line lets off at its stop, and a stop walks to a station within
    `TO_STATION`. Returns the graph, the first station node and the node count."""
    index = {s: i for i, s in enumerate(stops)}
    count = len(stops)
    line_nodes: dict[tuple[str, str], int] = {}

    def node(stop: str, line: str) -> int:
        key = (stop, line)
        if key not in line_nodes:
            line_nodes[key] = count + len(line_nodes)
        return line_nodes[key]

    edges: dict[tuple[int, int], float] = {}

    def edge(a: int, b: int, cost: float) -> None:
        edges[(a, b)] = min(cost, edges.get((a, b), np.inf))

    for line, a, b, minutes in rides:
        for stop in (a, b):
            edge(index[stop], node(stop, line), headways.get(line, BUS_HEADWAY) / 2 + BOARD)
            edge(node(stop, line), index[stop], 0.0)
        edge(node(a, line), node(b, line), minutes)
    first_station = count + len(line_nodes)
    placed = [s for s in stops if s in where]
    xy = bng(np.array([where[s] for s in placed]))
    tree = KDTree(station_xy)
    for s, point in zip(placed, xy, strict=True):
        for q in tree.query_ball_point(point, TO_STATION * WALK / STREET):
            metres = float(np.hypot(*(station_xy[q] - point)))
            edge(index[s], first_station + q, metres * STREET / WALK)
    size = first_station + len(station_xy)
    rows = [a for a, _ in edges]
    cols = [b for _, b in edges]
    costs = [max(c, 1e-9) for c in edges.values()]
    graph = coo_matrix((costs, (rows, cols)), shape=(size, size)).tocsr()
    return graph, first_station, size


def stop_to_station(graph: Any, first_station: int, stations: int, stops: int) -> np.ndarray:
    """The minutes from each stop to each station by bus and foot (stations by stops), within
    `REACH`, from searches back from each station."""
    back = graph.T.tocsr()
    out = np.full((stations, stops), np.inf, dtype=np.float32)
    for start in range(0, stations, 100):
        chunk = list(range(first_station + start, first_station + min(start + 100, stations)))
        found = dijkstra(back, directed=True, indices=chunk, limit=REACH)
        out[start : start + len(chunk)] = found[:, :stops]
    return out


def _cached(name: str, make: Any) -> Any:
    path = INTERIM / f"{name}.pkl"
    if path.exists():
        return pickle.loads(path.read_bytes())
    value = make()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pickle.dumps(value))
    return value


def _network() -> Any:
    from atlas.datasets.world import openstreetmap
    from atlas.spatial import walking

    return walking.Network.from_ways(walking.read_ways(openstreetmap.fetch(data_dir(), "london")))


def top_links(access: np.ndarray, keep: int) -> tuple[np.ndarray, np.ndarray]:
    """The `keep` stations quickest to reach, within `REACH`, as (stations, minutes)."""
    within = np.flatnonzero(access <= REACH)
    order = within[np.lexsort((within, access[within]))][:keep]
    return order, access[order]


def analyse() -> None:
    cells = pq.read_table(BUNDLE / "cells.parquet", columns=["cell"]).column("cell").to_pylist()
    centres = np.array([h3.cell_to_latlng(c) for c in cells])
    centre_xy = bng(centres)
    stations = pq.read_table(BUNDLE / "stations.parquet").to_pydict()
    station_ll = np.column_stack([stations["lat"], stations["lng"]])
    station_xy = bng(station_ll)
    n = len(station_ll)
    matrix = (
        pq.read_table(BUNDLE / "station-matrix.parquet").column("minutes").to_numpy().reshape(n, n)
    )
    ride = matrix.astype(np.float64)
    ride[matrix == UNREACHABLE] = np.inf
    links = pq.read_table(BUNDLE / "cell-stations.parquet").to_pandas()

    stops, where, rides, headways, counts = bus_network()
    print(json.dumps(counts))
    hw = np.array(list(headways.values()))
    print(
        f"headways: median {np.median(hw):.1f}, 10th {np.percentile(hw, 10):.1f}, "
        f"90th {np.percentile(hw, 90):.1f} minutes"
    )
    graph, first_station, _ = bus_graph(stops, where, rides, headways, station_xy)
    t0 = time.time()
    to_station = stop_to_station(graph, first_station, n, len(stops))
    print(f"stop to station searches: {time.time() - t0:.0f} s")

    placed = [i for i, s in enumerate(stops) if s in where]
    stop_xy = bng(np.array([where[stops[i]] for i in placed]))
    network: list[Any] = []

    def the_network() -> Any:
        if not network:
            t = time.time()
            network.append(_network())
            print(f"walking network: {time.time() - t:.0f} s")
        return network[0]

    to_stations = _cached(
        "station-walks", lambda: the_network().times_within(station_xy, centre_xy, REACH)
    )
    to_stops = _cached(
        f"stop-walks-{len(placed)}",
        lambda: the_network().times_within(stop_xy, centre_xy, STOP_WALK),
    )
    placed_arr = np.array(placed)

    # Each cell's way to every station: the walk, or a walk to a stop and the bus.
    walk_access = np.full((len(cells), n), np.inf, dtype=np.float32)
    bus_access = np.full((len(cells), n), np.inf, dtype=np.float32)
    for c in range(len(cells)):
        found, minutes = to_stations[c]
        walk_access[c, found] = minutes
        s_found, s_minutes = to_stops[c]
        if len(s_found):
            cols = to_station[:, placed_arr[s_found]] + s_minutes[None, :].astype(np.float32)
            bus_access[c] = cols.min(axis=1)
    access = np.minimum(walk_access, bus_access)
    print(
        f"cells with a station within {REACH:.0f} minutes: on foot "
        f"{np.mean(np.isfinite(walk_access).any(axis=1)):.1%}, with buses "
        f"{np.mean((access <= REACH).any(axis=1)):.1%}"
    )
    best_walk = np.where(np.isfinite(walk_access), walk_access, np.inf).min(axis=1)
    best_any = access.min(axis=1)
    has = np.isfinite(best_walk)
    print(
        f"quickest way to a station, median over cells: on foot {np.median(best_walk[has]):.1f}, "
        f"with buses {np.median(best_any[has]):.1f}; where the walk is over 20 minutes: "
        f"{np.median(best_walk[best_walk > 20]):.1f} on foot, "
        f"{np.median(best_any[best_walk > 20]):.1f} with buses"
    )

    pairs = sample_pairs(300, len(cells))
    jp: dict[tuple[str, str, str], float] = {}
    kept = pd.read_csv(data_dir() / "raw" / "tfl" / f"travel-check-london-{DATE}.csv", dtype=str)
    for o, d, t, m in kept.itertuples(index=False):
        jp[(o, d, t)] = float(m) if isinstance(m, str) and m else np.nan
    metres = np.array([straight_metres(*centres[a], *centres[b]) for a, b in pairs])

    def straight_from(b: int) -> np.ndarray:
        last = (
            np.array([straight_metres(*station_ll[q], *centres[b]) for q in range(n)])
            * STREET
            / WALK
        )
        return np.where(last <= REACH, last, np.inf)

    last_walk = {b: straight_from(b) for _, b in pairs}
    old_links: dict[int, tuple[np.ndarray, np.ndarray]] = {
        c: (g["station"].to_numpy(), g["minutes"].to_numpy()) for c, g in links.groupby("cell")
    }

    def estimate(a: int, b: int, start: tuple, egress: np.ndarray) -> float:
        direct = straight_metres(*centres[a], *centres[b]) * STREET / WALK
        best = direct if direct <= REACH else np.inf
        found, minutes = start
        if len(found):
            best = min(best, float((minutes[:, None] + ride[found] + egress[None, :]).min()))
        return best

    def variant(name: str, start_of: Any, egress_of: Any) -> np.ndarray:
        est = np.array([estimate(a, b, start_of(a), egress_of(b)) for a, b in pairs])
        est[~np.isfinite(est)] = np.nan
        return est

    nothing = (np.empty(0, dtype=np.int64), np.empty(0))

    def bus_egress(keep: int) -> Any:
        def egress(b: int) -> np.ndarray:
            out = last_walk[b].copy()
            found, minutes = top_links(access[b], keep)
            out[found] = np.minimum(out[found], minutes)
            return out

        return egress

    variants = {
        "now (walks only, the bundle)": variant(
            "now", lambda a: old_links.get(a, nothing), lambda b: last_walk[b]
        ),
        "buses to the station, 8 kept": variant(
            "b8", lambda a: top_links(access[a], 8), lambda b: last_walk[b]
        ),
        "buses both ends, 8 kept": variant("bb8", lambda a: top_links(access[a], 8), bus_egress(8)),
        "buses both ends, 16 kept": variant(
            "bb16", lambda a: top_links(access[a], 16), bus_egress(16)
        ),
    }

    # A diagnostic the browser cannot do: a journey by bus alone, from the stops near one cell to
    # the stops near the other, with changes at a stop.
    def bus_only(a: int, b: int) -> float:
        sa, wa = to_stops[a]
        sb, wb = to_stops[b]
        if not len(sa) or not len(sb):
            return np.inf
        d = dijkstra(graph, directed=True, indices=placed_arr[sa], limit=150.0)
        return float((wa[:, None] + d[:, placed_arr[sb]] + wb[None, :]).min())

    t0 = time.time()
    by_bus = np.array([bus_only(a, b) for a, b in pairs])
    print(f"bus-only searches: {time.time() - t0:.0f} s")
    with_bus_only = np.fmin(variants["buses both ends, 16 kept"], by_bus)
    variants["buses both ends, 16 kept, and bus-only journeys"] = with_bus_only
    journey = np.array([jp.get((cells[a], cells[b], "0830"), np.nan) for a, b in pairs])
    ok = np.isfinite(journey) & np.isfinite(variants["buses both ends, 16 kept"])
    quicker = ok & (by_bus < variants["buses both ends, 16 kept"])
    print(f"bus alone is quicker than rail in {quicker.sum()} of {ok.sum()} journeys")

    # The walks at both ends of today's estimate, as S4 grouped its errors.
    ends = np.array(
        [
            (old_links.get(a, nothing)[1].min() if len(old_links.get(a, nothing)[1]) else np.inf)
            + last_walk[b].min()
            for a, b in pairs
        ]
    )
    for name, est in variants.items():
        print(f"\n### {name}\n")
        rows = []
        for at in TIMES:
            journey = np.array(
                [jp.get((cells[a], cells[b], at), np.nan) for a, b in pairs], dtype=float
            )
            rows += errors(est, journey, metres, f"{at[:2]}:{at[2:]}")[:1]
        journey = np.array([jp.get((cells[a], cells[b], "0830"), np.nan) for a, b in pairs])
        rows += errors(est, journey, metres, "08:30")[1:]
        print(table(rows))
        ok = np.isfinite(est) & np.isfinite(journey)
        too_long = np.mean(est[ok] / journey[ok] > 1.2)
        too_short = np.mean(est[ok] / journey[ok] < 0.8)
        print(f"\nmore than 20% too long {too_long:.0%}, more than 20% too short {too_short:.0%}")
        for low, high in ((0, 10), (10, 20), (20, 30), (30, np.inf)):
            m = ok & (ends >= low) & (ends < high)
            if m.any():
                print(
                    f"walks {low} to {high}: {m.sum()} journeys, median error "
                    f"{np.median(est[m] - journey[m]):+.1f} min"
                )

    # The size of the links file, as the bundle would carry it.
    for keep in (8, 16):
        rows = [
            (c, int(q), round(float(m), 1))
            for c in range(len(cells))
            for q, m in zip(*top_links(access[c], keep), strict=True)
        ]
        table_ = pa.table(
            {
                "cell": pa.array([r[0] for r in rows], pa.uint16()),
                "station": pa.array([r[1] for r in rows], pa.uint16()),
                "minutes": pa.array([r[2] for r in rows], pa.float32()),
            }
        )
        path = INTERIM / f"cell-stations-{keep}.parquet"
        pq.write_table(table_, path, compression="zstd")
        print(f"cell-stations with {keep} kept: {len(rows)} links, {path.stat().st_size:,} bytes")

    # The default places: walk or bus to a station, then the Journey Planner's time from it.
    times = pd.read_csv(data_dir() / "raw" / "tfl" / "journeys-london-20261104-0830.csv")
    names = sorted(set(times["place"]))
    jp_table = np.full((n, len(names)), np.inf)
    row = {s: i for i, s in enumerate(stations["stop"])}
    for s, p, m in times.itertuples(index=False):
        if s in row and np.isfinite(m):
            jp_table[row[s], names.index(p)] = m
    old = pq.read_table(BUNDLE / "cells.parquet", columns=["travel_time_to_places"]).column(0)
    old = np.array(old.to_pylist(), dtype=float)
    new = np.full(len(cells), np.nan)
    for c in range(len(cells)):
        reach = np.flatnonzero(access[c] <= REACH)
        if len(reach):
            total = (access[c, reach][:, None] + jp_table[reach]).min(axis=0)
            if np.isfinite(total).all():
                new[c] = total.mean()
    both = np.isfinite(old) & np.isfinite(new)
    print(
        f"\ntravel time to the default places: cells with a value {np.isfinite(old).mean():.1%} "
        f"now, {np.isfinite(new).mean():.1%} with buses; median {np.nanmedian(old):.1f} now, "
        f"{np.nanmedian(new[both]):.1f} with buses on the same cells; median change "
        f"{np.median(new[both] - old[both]):+.1f}, 10th percentile "
        f"{np.percentile(new[both] - old[both], 10):+.1f} minutes"
    )


if __name__ == "__main__":
    {"fetch": fetch, "analyse": analyse}[sys.argv[1]]()
