"""The minutes from each cell to each station: a walk along the streets, or a walk to a bus stop
and a bus to the station, whichever is quicker (spike S9).

The travel estimate starts and ends at the stations (D10). A walk to a station is an upper bound
where a bus is quicker, which made the estimate a median 11 minutes too long ([S4]); a bus leg at
both ends cut that to 5.5 minutes ([S9]). The bus leg is found on a graph with a node for each
stop, one for each line at each stop, and one for each station: boarding a line at a stop costs
half its headway (the mean wait) and `BOARD_MINUTES`, a ride to the next stop costs the
timetable's minutes, getting off costs nothing, and a stop links to each station within a walk of
`TO_STATION` minutes in a straight line times the street factor. A search back from each station
gives every stop's minutes to it. A cell then takes, for each station, the quicker of the street
walk and a street walk of at most `STOP_WALK` minutes to a stop plus that stop's minutes.

The times are an estimate: the wait is a mean, and the timetable is the weekday morning's.
"""

from collections.abc import Iterable, Mapping

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import KDTree

from atlas.indicators.station_matrix import STREET_FACTOR, WALK_METRES_A_MINUTE, Ride
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network

# For each cell, the positions of the stations within reach (ascending) and the minutes to each.
Access = list[tuple[np.ndarray, np.ndarray]]

STOP_WALK = 10.0  # the longest walk along the streets from a cell's centre to a bus stop
TO_STATION = 6.0  # the longest walk from a bus stop to a station
BOARD_MINUTES = 0.5  # boarding a bus, beyond the wait
REACH = 40.0  # the longest way to a station, on foot or by bus
_CHUNK = 100  # stations searched at once


def _xy(table: pd.DataFrame) -> np.ndarray:
    return np.column_stack([table["Easting"].to_numpy(), table["Northing"].to_numpy()])


def bus_to_station(
    stops: pd.DataFrame,
    rides: Iterable[Ride],
    headways: Mapping[str, float],
    stations: pd.DataFrame,
    *,
    reach: float = REACH,
) -> np.ndarray:
    """The minutes from each stop of `stops` to each station of `stations` (both with `stop`,
    `Easting` and `Northing`), by bus and on foot, as stations by stops in their order, with
    infinity beyond `reach`. A ride may pass through a stop that `stops` lacks (one with no
    position): it is a node of the graph, with no walk to a station."""
    index = {stop: i for i, stop in enumerate(stops["stop"])}
    rides = list(rides)
    for ride in rides:
        for stop in (ride.start, ride.end):
            index.setdefault(stop, len(index))
    count = len(index)
    line_nodes: dict[tuple[str, str], int] = {}

    def node(stop: str, line: str) -> int:
        return line_nodes.setdefault((stop, line), count + len(line_nodes))

    # The cheapest cost of each edge, since a sparse graph adds up repeated entries.
    edges: dict[tuple[int, int], float] = {}

    def edge(a: int, b: int, cost: float) -> None:
        edges[(a, b)] = min(cost, edges.get((a, b), np.inf))

    for ride in rides:
        wait = headways[ride.line] / 2 + BOARD_MINUTES
        for stop in (ride.start, ride.end):
            edge(index[stop], node(stop, ride.line), wait)
            edge(node(stop, ride.line), index[stop], 0.0)
        edge(node(ride.start, ride.line), node(ride.end, ride.line), ride.minutes)

    first_station = count + len(line_nodes)
    station_xy, stop_xy = _xy(stations), _xy(stops)
    if len(stop_xy) and len(station_xy):
        metres_limit = TO_STATION * WALK_METRES_A_MINUTE / STREET_FACTOR
        near = KDTree(station_xy).query_ball_point(stop_xy, metres_limit)
        for s, found in enumerate(near):
            for q in sorted(found):
                metres = float(np.hypot(*(station_xy[q] - stop_xy[s])))
                edge(s, first_station + q, metres * STREET_FACTOR / WALK_METRES_A_MINUTE)

    size = first_station + len(station_xy)
    rows = [a for a, _ in edges]
    cols = [b for _, b in edges]
    # A cost of 0 would read as "no edge" in a sparse graph, so it is kept just above 0.
    costs = [max(c, 1e-9) for c in edges.values()]
    back = coo_matrix((costs, (cols, rows)), shape=(size, size)).tocsr()
    out = np.full((len(station_xy), len(stop_xy)), np.inf, dtype=np.float32)
    for start in range(0, len(station_xy), _CHUNK):
        chunk = range(first_station + start, first_station + min(start + _CHUNK, len(station_xy)))
        found = dijkstra(back, directed=True, indices=list(chunk), limit=reach)
        out[start : start + len(chunk)] = found[:, : len(stop_xy)]
    return out


def cell_access(
    network: Network,
    stations: pd.DataFrame,
    cells: list[str],
    *,
    walk: float = REACH,
    buses: tuple[pd.DataFrame, np.ndarray] | None = None,
) -> Access:
    """For each cell, the stations within `walk` minutes of its centre and the minutes to each:
    the street walk, or with `buses` (the stops, and `bus_to_station`'s minutes from them), the
    quicker of the walk and a walk to a stop within `STOP_WALK` plus the stop's minutes."""
    centres = cell_centres_bng(cells)
    walks = network.times_within(_xy(stations), centres, walk)
    stop_walks = (
        network.times_within(_xy(buses[0]), centres, STOP_WALK) if buses is not None else None
    )
    access: Access = []
    for c, (found, minutes) in enumerate(walks):
        best = np.full(len(stations), np.inf)
        best[found] = minutes
        if buses is not None and stop_walks is not None:
            stops, to_walk = stop_walks[c]
            if len(stops):
                by_bus = (buses[1][:, stops] + to_walk[None, :]).min(axis=1)
                best = np.minimum(best, by_bus)
        kept = np.flatnonzero(best <= walk)
        access.append((kept, best[kept]))
    return access
