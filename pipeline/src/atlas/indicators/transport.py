"""The transport indicators that are walks: the minutes on foot to the nearest station."""

import h3
import numpy as np
import pandas as pd
from pyproj import Transformer

from atlas.spatial.walking import Network

_TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)


def cell_centres(cells: list[str]) -> np.ndarray:
    """The centre of each cell, in metres of British National Grid."""
    points = [h3.cell_to_latlng(c) for c in cells]
    x, y = _TO_BNG.transform([p[1] for p in points], [p[0] for p in points])
    return np.column_stack([x, y])


def station_minutes(network: Network, stations: pd.DataFrame, cells: list[str]) -> pd.Series:
    """The walking minutes from each cell's centre to the nearest station entrance, along streets
    and paths. A cell from which no station can be reached has no value."""
    x, y = _TO_BNG.transform(stations["Longitude"].to_numpy(), stations["Latitude"].to_numpy())
    minutes = network.minutes_to_nearest(
        places=np.column_stack([x, y]), origins=cell_centres(cells)
    )
    return pd.Series(minutes, index=cells)
