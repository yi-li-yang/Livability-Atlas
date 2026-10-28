"""The environment indicators that are walks: the minutes on foot to a way into a green space."""

import numpy as np
import pandas as pd

from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network


def green_space_minutes(network: Network, entrances: np.ndarray, cells: list[str]) -> pd.Series:
    """The walking minutes from each cell's centre to the nearest way into a green space, along
    streets and paths. `entrances` holds an easting and a northing for each."""
    minutes = network.minutes_to_nearest(places=entrances, origins=cell_centres_bng(cells))
    return pd.Series(minutes, index=cells)
