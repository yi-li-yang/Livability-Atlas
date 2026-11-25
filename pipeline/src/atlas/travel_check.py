"""How far the travel estimate for a user's places is from the Journey Planner (D10).

A sample of journeys, each from one cell's centre to another's, is asked of TfL's Journey Planner
by every mode at three times of a weekday, and compared with the estimate that the web app makes
from the bundle's travel files. The answers are kept a line at a time by the cells' ids, so a
stopped check carries on and a rebuilt bundle reuses only the journeys between the same cells.
The result is a table for the S4 write-up: the median and mean error, and the share within 20%,
by the length of the journey.
"""

import csv
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import h3
import numpy as np
import pyarrow.parquet as pq

from atlas.datasets.cities.london import tfl_api
from atlas.datasets.cities.london.tfl_timetables import DATE, check_answered
from atlas.scoring.travel import region_minutes, straight_metres

TIMES = ("0830", "1230", "1800")
BANDS = ((0, 5_000, "under 5 km"), (5_000, 15_000, "5 to 15 km"), (15_000, math.inf, "over 15 km"))
PAUSE = 1.3
WORKERS = 3


def sample_pairs(count: int, cells: int, seed: int = 20261122) -> list[tuple[int, int]]:
    """`count` pairs of different cells, the same each time for the same seed."""
    rng = np.random.default_rng(seed)
    pairs: list[tuple[int, int]] = []
    while len(pairs) < count:
        a, b = (int(x) for x in rng.integers(0, cells, size=2))
        if a != b:
            pairs.append((a, b))
    return pairs


@dataclass(frozen=True)
class Error:
    """How the estimates of a group of journeys compare with the Journey Planner's times."""

    label: str
    journeys: int
    median_error: float  # minutes, the estimate less the Journey Planner's time
    mean_absolute: float  # minutes
    within_20: float  # the share of journeys whose estimate is within 20% of the time


def errors(
    estimate: np.ndarray, journey: np.ndarray, metres: np.ndarray, label: str = "all"
) -> list[Error]:
    """The errors over all journeys that have both times, and by the length of the journey."""
    both = np.isfinite(estimate) & np.isfinite(journey) & (journey > 0)

    def one(mask: np.ndarray, name: str) -> Error:
        e, j = estimate[mask], journey[mask]
        if len(e) == 0:
            return Error(name, 0, math.nan, math.nan, math.nan)
        return Error(
            name,
            len(e),
            float(np.median(e - j)),
            float(np.mean(np.abs(e - j))),
            float(np.mean(np.abs(e / j - 1) <= 0.2)),
        )

    out = [one(both, label)]
    for low, high, name in BANDS:
        out.append(one(both & (metres >= low) & (metres < high), f"{label}, {name}"))
    return out


def table(rows: list[Error]) -> str:
    """The errors as a Markdown table."""
    lines = [
        "| Journeys | Count | Median error | Mean absolute error | Within 20% |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for r in rows:
        lines.append(
            f"| {r.label} | {r.journeys} | {r.median_error:+.1f} min | "
            f"{r.mean_absolute:.1f} min | {r.within_20:.0%} |"
        )
    return "\n".join(lines)


def _quickest(answer: object) -> float | None:
    journeys = (answer or {}).get("journeys", []) if isinstance(answer, dict) else []
    durations = [j["duration"] for j in journeys if "duration" in j]
    return float(min(durations)) if durations else None


def check(bundle: Path, data_dir: Path, region_id: str, count: int = 300) -> str:
    """Asks the Journey Planner for a sample of journeys at each time, compares them with the
    bundle's estimate, and returns the table."""
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    travel = manifest.get("travel")
    if travel is None:
        raise ValueError(f"{bundle} has no travel files")
    cells = pq.read_table(bundle / "cells.parquet", columns=["cell"]).column("cell").to_pylist()
    centres = np.array([h3.cell_to_latlng(c) for c in cells])
    pairs = sample_pairs(count, len(cells))
    target = data_dir / "raw" / "tfl" / f"travel-check-{region_id}-{DATE}.csv"
    times = _ask(target, cells, centres, pairs)

    stations = pq.read_table(bundle / travel["stations"]).to_pydict()
    links = pq.read_table(bundle / travel["cell_stations"]).to_pydict()
    n = travel["station_count"]
    matrix = pq.read_table(bundle / travel["matrix"]).column("minutes").to_numpy().reshape(n, n)
    station_xy = np.column_stack([stations["lat"], stations["lng"]])
    link_rows = np.column_stack([links["cell"], links["station"], links["minutes"]]).astype(float)
    estimate = np.full(len(pairs), np.nan)
    by_place: dict[int, np.ndarray] = {}
    for i, (a, b) in enumerate(pairs):
        if b not in by_place:
            by_place[b] = region_minutes(
                station_xy,
                matrix,
                link_rows,
                centres,
                (centres[b][0], centres[b][1]),
                travel,
                place_cell=b,
            )
        estimate[i] = by_place[b][a]
    metres = np.array([straight_metres(*centres[a], *centres[b]) for a, b in pairs])

    rows: list[Error] = []
    for at in TIMES:
        journey = np.array(
            [times.get((cells[a], cells[b], at), np.nan) for a, b in pairs], dtype=float
        )
        rows += errors(estimate, journey, metres, f"{at[:2]}:{at[2:]}")
    return table(rows)


def _ask(
    target: Path, cells: list[str], centres: np.ndarray, pairs: list[tuple[int, int]]
) -> dict[tuple[str, str, str], float]:
    """The Journey Planner's quickest time for each pair of cells at each time, kept in `target`
    by the cells' ids. A journey with no answer is kept only once the check has ended, and only
    if most journeys had one (otherwise the day has passed)."""
    done: dict[tuple[str, str, str], float] = {}
    if target.exists():
        with target.open(encoding="utf-8") as file:
            for row in csv.DictReader(file):
                key = (row["origin"], row["destination"], row["time"])
                done[key] = float(row["minutes"]) if row["minutes"] else math.nan
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("origin,destination,time,minutes\n", encoding="utf-8", newline="\n")
    wanted = [(a, b, at) for at in TIMES for a, b in pairs if (cells[a], cells[b], at) not in done]

    def ask(job: tuple[int, int, str]) -> tuple[int, int, str, float | None]:
        a, b, at = job
        time.sleep(PAUSE)
        (la, lo), (lb, lg) = centres[a], centres[b]
        answer = tfl_api.get(
            f"Journey/JourneyResults/{la:.5f},{lo:.5f}/to/{lb:.5f},{lg:.5f}"
            f"?date={DATE}&time={at}&timeIs=Departing&journeyPreference=LeastTime",
            missing=True,
        )
        return a, b, at, _quickest(answer)

    empty: list[tuple[str, str, str]] = []
    with target.open("a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        pool = ThreadPoolExecutor(WORKERS)
        try:
            for future in as_completed([pool.submit(ask, job) for job in wanted]):
                a, b, at, minutes = future.result()
                key = (cells[a], cells[b], at)
                if minutes is None:
                    done[key] = math.nan
                    empty.append(key)
                else:
                    done[key] = minutes
                    writer.writerow([*key, minutes])
                    file.flush()
        except BaseException:
            pool.shutdown(wait=True, cancel_futures=True)
            raise
        pool.shutdown()
        check_answered(len(wanted), len(empty))
        for key in sorted(empty):
            writer.writerow([*key, ""])
    return done
