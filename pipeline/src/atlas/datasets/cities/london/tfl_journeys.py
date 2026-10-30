"""Journey times from stations to a region's default places, from TfL's Journey Planner (dataset
`tfl-unified-api`).

The Journey Planner gives the quickest journey by all modes between two points, from the
timetables of the day asked for. A cell's own journey cannot be asked for (17,000 cells), so each
station is asked for its journey to each default place, and a cell takes the walk to a station
and that station's journey (`transport.travel_minutes`). One departure is asked for: the morning
of a weekday, 08:30, as D10 says. The answers are kept, one line at a time, so a stopped fetch
carries on. TfL's open data licence, with attribution.
"""

import csv
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.datasets.cities.london import tfl_api

DATE = "20261104"  # a Wednesday
TIME = "0830"
PAUSE = 1.3  # seconds a worker waits before each request
WORKERS = 3  # requests at once: without a key TfL allows a modest rate, and 429 makes us wait


def _get(path: str, missing: bool = False) -> Any:
    return tfl_api.get(path, missing=missing)


def _quickest(answer: Any) -> float | None:
    """The shortest duration, in minutes, of the journeys in an answer."""
    durations = [j["duration"] for j in (answer or {}).get("journeys", []) if "duration" in j]
    return float(min(durations)) if durations else None


def fetch(
    data_dir: Path,
    region_id: str,
    stations: pd.DataFrame,
    places: Sequence[tuple[str, float, float]],
) -> Path:
    """Asks the Journey Planner for the quickest journey from each station (`stop`, `Latitude`,
    `Longitude`) to each place (name, latitude, longitude) and keeps the minutes, in
    `data/raw/tfl/journeys-<region>-<date>-<time>.csv`. A pair with no journey is kept with no
    minutes. Pairs already kept are not asked again."""
    target = data_dir / "raw" / "tfl" / f"journeys-{region_id}-{DATE}-{TIME}.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    done: set[tuple[str, str]] = set()
    if target.exists():
        kept = pd.read_csv(target, dtype={"stop": str, "place": str})
        done = set(zip(kept["stop"], kept["place"], strict=True))
    else:
        target.write_text("stop,place,minutes\n", encoding="utf-8", newline="\n")
    pairs = [
        (str(stop), f"{latitude},{longitude}", name, lat, lng)
        for stop, latitude, longitude in stations[["stop", "Latitude", "Longitude"]].to_numpy()
        for name, lat, lng in places
        if (str(stop), name) not in done
    ]

    def ask(pair: tuple[str, str, str, float, float]) -> tuple[str, str, float | None]:
        stop, origin, name, lat, lng = pair
        time.sleep(PAUSE)
        answer = _get(
            f"Journey/JourneyResults/{origin}/to/{lat},{lng}"
            f"?date={DATE}&time={TIME}&timeIs=Departing&journeyPreference=LeastTime",
            missing=True,
        )
        return stop, name, _quickest(answer)

    with target.open("a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        pool = ThreadPoolExecutor(WORKERS)
        try:
            for future in as_completed([pool.submit(ask, pair) for pair in pairs]):
                stop, name, minutes = future.result()
                writer.writerow([stop, name, "" if minutes is None else minutes])
                file.flush()
        except BaseException:
            pool.shutdown(wait=True, cancel_futures=True)  # no request still flying once we stop
            raise
        pool.shutdown()
    return target


def read_times(path: Path) -> pd.DataFrame:
    """The journey minutes, a row for each `stop` and `place`, with NaN where there is none."""
    return pd.read_csv(path, dtype={"stop": str, "place": str})
