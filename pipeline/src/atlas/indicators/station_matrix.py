"""The minutes from every rail station to every other, for the travel estimate to a user's places.

The Journey Planner cannot answer every pair (D10), so the matrix comes from the timetables: a
shortest-path search over a graph with a node for each station and one for each line at each
station. Riding from one stop of a line to the next costs the timetable's minutes; boarding a line
costs the walk from the street to the platform and half its headway (the mean wait); getting off
costs the walk from the platform to the street; and a change to another stop
within `change_metres` in a straight line (the Tube's and National Rail's platforms of one station
have different ids) costs the walk. The result is in whole minutes, with `UNREACHABLE` where no
way exists.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import KDTree

from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network

UNREACHABLE = 65535  # the matrix is kept as unsigned 16-bit minutes
STREET_FACTOR = 1.33  # a street walk is a median 1.33 times its straight line (spike S6)
WALK_METRES_A_MINUTE = 80.0
CHANGE_METRES = 300.0
# The walks between the street and the platform, in minutes (fitted to the Journey Planner's times
# from stations to the default places in the London build of 2026-11-22: see the spec).
BOARD_MINUTES = 5.0
ALIGHT_MINUTES = 2.0


@dataclass(frozen=True)
class Ride:
    """A train's run from one stop to the next stop it calls at, on one line, in minutes."""

    line: str
    start: str
    end: str
    minutes: float


def station_matrix(
    stations: pd.DataFrame,
    rides: Iterable[Ride],
    headways: Mapping[str, float],
    *,
    change_metres: float = CHANGE_METRES,
    board_minutes: float = 0.0,
    alight_minutes: float = 0.0,
) -> np.ndarray:
    """The minutes from each station of `stations` (`stop`, `Easting`, `Northing`, in metres) to
    each other, in their order, as a square array of unsigned 16-bit whole minutes. `headways`
    gives each line's minutes between trains, and `board_minutes` and `alight_minutes` the walks
    between the street and the platform (a change of line pays both). A ride to or from a stop that
    `stations` lacks is left out."""
    stops = list(stations["stop"])
    index = {stop: i for i, stop in enumerate(stops)}
    count = len(stops)
    line_nodes: dict[tuple[str, str], int] = {}

    def node(stop: str, line: str) -> int:
        key = (stop, line)
        if key not in line_nodes:
            line_nodes[key] = count + len(line_nodes)
        return line_nodes[key]

    # The cheapest cost of each edge: two routes can give the same ride, and a sparse graph would
    # add up repeated entries rather than keep the cheaper one.
    edges: dict[tuple[int, int], float] = {}

    def edge(a: int, b: int, cost: float) -> None:
        edges[(a, b)] = min(cost, edges.get((a, b), np.inf))

    for ride in rides:
        if ride.start not in index or ride.end not in index:
            continue
        wait = board_minutes + headways[ride.line] / 2
        for stop in (ride.start, ride.end):
            edge(index[stop], node(stop, ride.line), wait)
            edge(node(stop, ride.line), index[stop], alight_minutes)
        edge(node(ride.start, ride.line), node(ride.end, ride.line), ride.minutes)

    xy = np.column_stack([stations["Easting"].to_numpy(), stations["Northing"].to_numpy()])
    for a, b in sorted(KDTree(xy).query_pairs(change_metres)):
        metres = float(np.hypot(*(xy[a] - xy[b])))
        walk = metres * STREET_FACTOR / WALK_METRES_A_MINUTE
        edge(a, b, walk)
        edge(b, a, walk)

    rows = [a for a, _ in edges]
    cols = [b for _, b in edges]
    # A cost of 0 would read as "no edge" in a sparse graph, so it is kept just above 0.
    costs = [max(c, 1e-9) for c in edges.values()]
    size = count + len(line_nodes)
    graph = coo_matrix((costs, (rows, cols)), shape=(size, size)).tocsr()
    minutes = dijkstra(graph, directed=True, indices=list(range(count)))[:, :count]
    out = np.full((count, count), UNREACHABLE, dtype=np.uint16)
    reached = np.isfinite(minutes)
    out[reached] = np.rint(minutes[reached]).astype(np.uint16)
    np.fill_diagonal(out, 0)
    return out


def cell_stations(
    network: Network,
    stations: pd.DataFrame,
    cells: list[str],
    *,
    walk: float = 40.0,
    keep: int = 8,
) -> list[tuple[int, int, float]]:
    """For each cell, the `keep` stations quickest to walk to from its centre along the streets,
    within `walk` minutes: (cell position, station position, minutes to a tenth). These are where
    the estimate to a user's place can start."""
    xy = np.column_stack([stations["Easting"].to_numpy(), stations["Northing"].to_numpy()])
    links: list[tuple[int, int, float]] = []
    for position, (found, minutes) in enumerate(
        network.times_within(xy, cell_centres_bng(cells), walk)
    ):
        order = np.lexsort((found, minutes))[:keep]
        links += [(position, int(found[i]), round(float(minutes[i]), 1)) for i in order]
    return links
