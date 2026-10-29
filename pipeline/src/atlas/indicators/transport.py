"""The transport indicators that are walks: the minutes on foot to the nearest station, and the
number of lines or routes that stop within a walk."""

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.sparse import csr_matrix

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
