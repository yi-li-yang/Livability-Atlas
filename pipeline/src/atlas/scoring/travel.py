"""The reference for the travel estimate to a user's place (D10), which the web app reproduces.

A cell's time to a place is the quickest of: walking straight there, when the walk is within reach;
or walking along the streets to one of the cell's stations, riding the station matrix to a station
near the place, and walking from there. A walk from the place is the straight line times the street
factor, since the browser has no street network. The inputs are in the format of the golden cases
in `shared/fixtures/travel/`, the same as the bundle's travel files.
"""

import math
from typing import Any

import numpy as np

EARTH_RADIUS = 6_371_008.8  # metres: the mean radius, as the web app uses


def straight_metres(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """The great-circle distance between two points, by the haversine formula."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS * math.asin(math.sqrt(a))


def estimate(case: dict[str, Any]) -> float | None:
    """The minutes from the cell to the place, or None where there is no way within reach."""
    k = case["constants"]
    reach, speed, factor, unreachable = (
        k["reach_minutes"],
        k["walk_metres_a_minute"],
        k["street_factor"],
        k["unreachable"],
    )
    cell, place = case["cell"], case["place"]

    def walk(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        return straight_metres(lat1, lng1, lat2, lng2) * factor / speed

    best = math.inf
    direct = walk(cell["lat"], cell["lng"], place["lat"], place["lng"])
    if direct <= reach:
        best = direct
    # The best time from each station to the place: its walk, where the walk is within reach.
    to_place = {
        q: minutes
        for q, (lat, lng) in enumerate(case["stations"])
        if (minutes := walk(lat, lng, place["lat"], place["lng"])) <= reach
    }
    for s, on_foot in cell["stations"]:
        for q, last in to_place.items():
            ride = case["matrix"][s][q]
            if ride != unreachable:
                best = min(best, on_foot + ride + last)
    return None if math.isinf(best) else best


def _metres(lat1: np.ndarray, lng1: np.ndarray, lat2: float, lng2: float) -> np.ndarray:
    """`straight_metres` from many points to one."""
    p1, p2 = np.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, np.radians(lng2 - lng1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * math.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS * np.arcsin(np.sqrt(a))


def region_minutes(
    stations: np.ndarray,
    matrix: np.ndarray,
    links: np.ndarray,
    centres: np.ndarray,
    place: tuple[float, float],
    constants: dict[str, float],
) -> np.ndarray:
    """`estimate` for every cell at once: `stations` and `centres` are (latitude, longitude) rows,
    `matrix` the square station matrix and `links` rows of (cell, station, minutes). NaN where a
    cell has no way within reach."""
    reach, speed, factor = (
        constants["reach_minutes"],
        constants["walk_metres_a_minute"],
        constants["street_factor"],
    )
    lat, lng = place
    last = _metres(stations[:, 0], stations[:, 1], lat, lng) * factor / speed
    near = np.flatnonzero(last <= reach)
    rides = matrix[:, near].astype(np.float64)
    rides[matrix[:, near] == constants["unreachable"]] = np.inf
    from_station = (rides + last[near]).min(axis=1) if len(near) else np.full(len(stations), np.inf)
    direct = _metres(centres[:, 0], centres[:, 1], lat, lng) * factor / speed
    best = np.where(direct <= reach, direct, np.inf)
    if len(links):
        cell = links[:, 0].astype(np.int64)
        station = links[:, 1].astype(np.int64)
        np.minimum.at(best, cell, links[:, 2] + from_station[station])
    return np.where(np.isfinite(best), best, np.nan)
