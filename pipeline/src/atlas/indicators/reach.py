"""What a cell reaches by public transport: the sum of a value (such as jobs) over every cell within
a time, by the same estimate as the travel to a user's places (D10).

A cell's time to another is the quicker of the straight walk (the line times the street factor),
when that walk is within reach, and the journey through the stations: its way to one of its
stations, on foot or by bus (the cell-station links), the station matrix's ride, and the other
cell's way to one of its own stations, read backwards. It is an estimate of a weekday morning: see
the method of travel time to places and spike S9.
"""

import numpy as np

from atlas.indicators.station_matrix import UNREACHABLE


def within_minutes(
    values: np.ndarray,
    east: np.ndarray,
    north: np.ndarray,
    links: np.ndarray,
    matrix: np.ndarray,
    *,
    minutes: float,
    reach_minutes: float,
    walk_metres_a_minute: float,
    street_factor: float,
    chunk: int = 256,
) -> np.ndarray:
    """For each cell, the sum of `values` over the cells it reaches within `minutes`, itself
    included. `east` and `north` are the cells' centres in metres, `links` rows of (cell, station,
    minutes) and `matrix` the square station matrix in whole minutes, with `UNREACHABLE` where no
    ride goes. A missing value counts as nothing."""
    n, s = len(values), len(matrix)
    value = np.nan_to_num(np.asarray(values, dtype=np.float64), nan=0.0)
    cell = links[:, 0].astype(np.int64) if len(links) else np.zeros(0, dtype=np.int64)
    station = links[:, 1].astype(np.int64) if len(links) else np.zeros(0, dtype=np.int64)
    if len(links) and (cell.min() < 0 or cell.max() >= n):
        raise ValueError("a link names a cell that the region does not have")
    if len(links) and (station.min() < 0 or station.max() >= s):
        raise ValueError("a link names a station that the matrix does not have")

    # Each cell's stations as a fixed-width table, padded with a station of its own that reaches
    # nothing (index s) at an endless time.
    width = int(np.bincount(cell, minlength=n).max()) if len(links) else 0
    near = np.full((n, max(width, 1)), s, dtype=np.int64)
    away = np.full((n, max(width, 1)), np.inf, dtype=np.float32)
    order = np.argsort(cell, kind="stable")
    cell, station, leg = cell[order], station[order], links[order, 2].astype(np.float32)
    slot = np.arange(len(cell)) - np.searchsorted(cell, cell)
    near[cell, slot] = station
    away[cell, slot] = leg

    ride = matrix.astype(np.float32)
    ride[matrix == UNREACHABLE] = np.inf
    np.fill_diagonal(ride, 0.0)
    ride = np.vstack([ride, np.full((1, s), np.inf, dtype=np.float32)])  # the padding station
    ride = np.hstack([ride, np.full((s + 1, 1), np.inf, dtype=np.float32)])

    walk_metres = reach_minutes * walk_metres_a_minute / street_factor
    out = np.zeros(n)
    for start in range(0, n, chunk):
        rows = slice(start, min(start + chunk, n))
        # The quickest time from each origin to each station: its own leg, then the ride.
        to_station = np.full((rows.stop - rows.start, s + 1), np.inf, dtype=np.float32)
        for k in range(near.shape[1]):
            np.minimum(to_station, away[rows, k, None] + ride[near[rows, k]], out=to_station)
        # Then to each cell, from one of the cell's own stations.
        best = np.full((rows.stop - rows.start, n), np.inf, dtype=np.float32)
        for k in range(near.shape[1]):
            np.minimum(best, to_station[:, near[:, k]] + away[None, :, k], out=best)
        metres = np.hypot(east[rows, None] - east[None, :], north[rows, None] - north[None, :])
        on_foot = np.where(
            metres <= walk_metres, metres * street_factor / walk_metres_a_minute, np.inf
        )
        np.minimum(best, on_foot.astype(np.float32), out=best)
        out[rows] = (best <= minutes) @ value
    return out
