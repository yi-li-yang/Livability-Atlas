"""The transport indicators that are walks: the minutes on foot to the nearest station, and the
number of lines or routes that stop within a walk."""

import re

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.sparse import csr_matrix
from scipy.spatial import KDTree

from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network

_TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)


def station_minutes(network: Network, stations: pd.DataFrame, cells: list[str]) -> pd.Series:
    """The walking minutes from each cell's centre to the nearest station entrance, along streets
    and paths. A cell from which no station can be reached has no value."""
    x, y = _TO_BNG.transform(stations["Longitude"].to_numpy(), stations["Latitude"].to_numpy())
    minutes = network.minutes_to_nearest(
        places=np.column_stack([x, y]), origins=cell_centres_bng(cells)
    )
    return pd.Series(minutes, index=cells)


def place_stops(stops: pd.DataFrame) -> pd.DataFrame:
    """The same rows with the `Easting` and `Northing` of each stop's `Latitude` and
    `Longitude`."""
    x, y = _TO_BNG.transform(stops["Longitude"].to_numpy(), stops["Latitude"].to_numpy())
    return stops.assign(Easting=x, Northing=y)


def lines_within_a_walk(
    network: Network, stops: pd.DataFrame, cells: list[str], minutes: float
) -> pd.Series:
    """The number of distinct lines (or routes) that serve a stop within a walk of each cell's
    centre, along streets and paths.

    `stops` has a row for each line at each stop: `stop`, `line`, `Easting` and `Northing`. A
    line counts once however many of its stops are in reach, and a cell with none in reach has 0.
    """
    places = stops.drop_duplicates("stop").reset_index(drop=True)
    codes = pd.Categorical(stops["line"]).codes
    at = pd.Series(places.index, index=places["stop"]).reindex(stops["stop"]).to_numpy()
    belongs = csr_matrix(
        (np.ones(len(stops), dtype=np.int8), (at, codes)), shape=(len(places), codes.max() + 1)
    )
    reach = network.places_within(
        places[["Easting", "Northing"]].to_numpy(dtype=float), cell_centres_bng(cells), minutes
    )
    counts = [np.unique(belongs[found].indices).size if len(found) else 0 for found in reach]
    return pd.Series(counts, index=cells, dtype=int)


def fare_zones(stations: pd.DataFrame, cells: list[str]) -> pd.Series:
    """The fare zone of the station nearest to each cell's centre, in a straight line, among the
    stations inside TfL's fare zones. `stations` has `Easting`, `Northing` and `zone`, as TfL
    writes it: `2`, `2+3` or `2/3` for a station in two zones, which counts as the lower one, and
    `NA` or nothing for a station outside the zones, which is not a choice. The zone is text, so
    that the curve's lookup reads it. A cell with no station in the zones has no value."""
    found = [re.findall(r"\d+", str(zone)) for zone in stations["zone"]]
    lowest = np.array([min(int(z) for z in zones) if zones else 0 for zones in found])
    zoned = lowest > 0
    if not zoned.any():
        return pd.Series([None] * len(cells), index=cells, dtype=object)
    places = np.column_stack(
        [stations["Easting"].to_numpy()[zoned], stations["Northing"].to_numpy()[zoned]]
    )
    _, nearest = KDTree(places).query(cell_centres_bng(cells))
    return pd.Series([str(z) for z in lowest[zoned][nearest]], index=cells, dtype=object)


def travel_minutes(
    network: Network,
    stations: pd.DataFrame,
    times: pd.DataFrame,
    cells: list[str],
    walk: float = 40.0,
) -> pd.Series:
    """The mean over the default places of the quickest door-to-door time from each cell's centre,
    by foot to a station within `walk` minutes and then that station's journey.

    `stations` has `stop`, `Easting` and `Northing`, and `times` has the journey `minutes` from
    each `stop` to each `place`. For each place a cell takes the station that gives the shortest
    walk plus journey, and the places' times are averaged. A cell with no station in reach, or from
    which a place cannot be reached, has no value.
    """
    names = sorted(set(times["place"]))
    table = np.full((len(stations), len(names)), np.nan)
    row = {stop: i for i, stop in enumerate(stations["stop"])}
    column = {name: j for j, name in enumerate(names)}
    for stop, place, minutes in zip(times["stop"], times["place"], times["minutes"], strict=True):
        if stop in row:
            table[row[stop], column[place]] = minutes
    places = np.column_stack([stations["Easting"].to_numpy(), stations["Northing"].to_numpy()])
    reach = network.times_within(places, cell_centres_bng(cells), walk)
    result = np.full(len(cells), np.nan)
    for position, (found, walking) in enumerate(reach):
        if len(found) == 0:
            continue
        total = walking[:, None] + table[found]
        if np.isnan(total).all(axis=0).any():
            continue
        result[position] = float(np.nanmin(total, axis=0).mean())
    return pd.Series(result, index=cells)
