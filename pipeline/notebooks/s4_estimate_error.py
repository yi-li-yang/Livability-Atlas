"""Spike S4: how far is the in-browser travel time estimate from TfL's Journey Planner?

Throwaway code, never imported by `atlas`. The estimate for a journey is the walk to a nearby
station, the ride between two stations (the station matrix), and the walk from a station. This
script takes the ride from the Journey Planner itself, which is what a matrix built from it
would hold, and compares the estimate with the Journey Planner's door-to-door time.

Needs `data/raw/naptan/naptan.csv` (DfT's NaPTAN) and spike S2's data, for the residents of each
cell. It calls the TfL Unified API without a key, about 400 times, slowly, and caches every
answer in `data/interim/s4_cache.json`, so an interrupted run resumes.
Run from `pipeline/` with `uv run python notebooks/s4_estimate_error.py`.
"""

import json
import math
import random
import time

import h3
import numpy as np
import pandas as pd
import requests
from s2_crime_rates import london_cells, residents_by_area

from atlas.paths import data_dir

API = "https://api.tfl.gov.uk/Journey/JourneyResults"
WHEN = {"date": "20261104", "time": "0830", "timeIs": "Departing"}  # a Wednesday morning
RAIL = "tube,dlr,overground,elizabeth-line,national-rail,tram,walking"
ALL = RAIL + ",bus"
PAIRS = 30
NEAREST = 3
WALK_M_PER_MIN = 80.0  # 4.8 km/h
DETOUR = 1.3  # a street route is about this much longer than a straight line
PAUSE = 1.5
CACHE = data_dir() / "interim" / "s4_cache.json"


def metres(a: tuple[float, float], b: tuple[float, float]) -> float:
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180
    h = (
        math.sin((la2 - la1) * p / 2) ** 2
        + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2
    )
    return 2 * 6371000 * math.asin(math.sqrt(h))


def stations() -> pd.DataFrame:
    frame = pd.read_csv(
        data_dir() / "raw" / "naptan" / "naptan.csv",
        usecols=["ATCOCode", "CommonName", "Latitude", "Longitude", "StopType", "Status"],
        dtype=str,
    )
    frame = frame[frame["StopType"].isin(["RLY", "MET"]) & (frame["Status"] == "active")].copy()
    frame["lat"], frame["lng"] = frame["Latitude"].astype(float), frame["Longitude"].astype(float)
    inside = frame["lat"].between(51.28, 51.69) & frame["lng"].between(-0.51, 0.34)
    return frame[inside].reset_index(drop=True)


class Planner:
    """The Journey Planner, with a cache on disk, a pause between calls and patience with errors."""

    def __init__(self) -> None:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        self.cache: dict[str, float | None] = (
            json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
        )
        self.calls = 0

    def minutes(self, origin: str, destination: str, modes: str) -> float | None:
        key = f"{origin}|{destination}|{modes}"
        if key in self.cache:
            return self.cache[key]
        for attempt in range(6):
            time.sleep(PAUSE)
            self.calls += 1
            reply = requests.get(
                f"{API}/{origin}/to/{destination}", params={**WHEN, "mode": modes}, timeout=60
            )
            if reply.status_code in (420, 429):
                time.sleep(60)
            elif reply.status_code >= 500:
                time.sleep(5 * (attempt + 1))
            else:
                break
        value = None
        if reply.status_code == 200:
            journeys = reply.json().get("journeys", [])
            if journeys:
                value = float(min(j["duration"] for j in journeys))
        self.cache[key] = value
        CACHE.write_text(json.dumps(self.cache), encoding="utf-8")
        return value


def main() -> None:
    cells = london_cells()
    residents = residents_by_area(cells)
    homes = [c for c in cells if residents.get(c, 0) >= 200]
    rng = random.Random(4)
    points = [h3.cell_to_latlng(c) for c in rng.sample(homes, 400)]
    pairs = []
    while len(pairs) < PAIRS:
        a, b = rng.sample(points, 2)
        if 4000 <= metres(a, b) <= 20000:
            pairs.append((a, b))

    table = stations()
    coords = table[["lat", "lng"]].to_numpy()
    planner = Planner()
    rows = []
    for a, b in pairs:
        near = {}
        for name, p in (("origin", a), ("destination", b)):
            d = np.array([metres(p, (la, lo)) for la, lo in coords])
            idx = np.argsort(d)[:NEAREST]
            near[name] = [(table["ATCOCode"][i], d[i] * DETOUR / WALK_M_PER_MIN) for i in idx]
        here, there = f"{a[0]:.5f},{a[1]:.5f}", f"{b[0]:.5f},{b[1]:.5f}"
        truth_all = planner.minutes(here, there, ALL)
        truth_rail = planner.minutes(here, there, RAIL)
        options = []
        for code_o, walk_o in near["origin"]:
            for code_d, walk_d in near["destination"]:
                ride = 0.0 if code_o == code_d else planner.minutes(code_o, code_d, RAIL)
                if ride is not None:
                    options.append(walk_o + ride + walk_d)
        rows.append(
            {
                "straight line km": metres(a, b) / 1000,
                "truth, all modes": truth_all,
                "truth, rail only": truth_rail,
                "estimate": min(options) if options else None,
            }
        )
        print(rows[-1], flush=True)

    frame = pd.DataFrame(rows).dropna()
    result: dict[str, object] = {
        "stations used": len(table),
        "pairs with every answer": len(frame),
        "pairs asked": PAIRS,
        "api calls this run": planner.calls,
    }
    for label in ("truth, all modes", "truth, rail only"):
        error = frame["estimate"] - frame[label]
        pct = error / frame[label]
        result[label] = {
            "median journey, minutes": float(frame[label].median()),
            "median error, minutes": round(float(error.median()), 1),
            "mean absolute error, minutes": round(float(error.abs().mean()), 1),
            "median absolute error, %": round(float(pct.abs().median() * 100), 1),
            "within 10 minutes": round(float((error.abs() <= 10).mean()), 2),
            "within 20%": round(float((pct.abs() <= 0.2).mean()), 2),
            "estimate too long by more than 20%": round(float((pct > 0.2).mean()), 2),
            "estimate too short by more than 20%": round(float((pct < -0.2).mean()), 2),
        }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
